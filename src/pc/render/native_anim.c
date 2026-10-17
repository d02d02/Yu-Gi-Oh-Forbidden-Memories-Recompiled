/* The native model's animation without OpenGL (native_anim.h). */
#include "pc/render/native_anim.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

NativeAct NativeAnim_Act(int row, int attack_row)
{
    int attack = attack_row == 4 ? 4 : 3;
    if (row == attack) return NATIVE_ACT_ATTACK;
    switch (row) {
    case 2:
        return NATIVE_ACT_ENTER;
    case 5:
        return NATIVE_ACT_HIT;
    case 6:
        return NATIVE_ACT_DESTROYED;
    case 7:
        return NATIVE_ACT_WIN;
    case 8:
        return NATIVE_ACT_GUARD;
    default: /* 0 and 1 (idle, back from a hit), the other guardian star's attack row, anything else */
        return NATIVE_ACT_IDLE;
    }
}

/* The cross-fade's memory of each monster (NativeSlotInfo.key): the pose last drawn, and the pose a row change fades
 * from. A key not seen for a while gives its place to a new one; a key whose mesh changed starts afresh (no fade from
 * another skeleton). */
#define MEMORIES 16
typedef struct Memory {
    int used, key, row, valid, fade, id;
    unsigned stamp;
    const NativeMesh *mesh;
    float last[NATIVE_MAX_BONES][7], from[NATIVE_MAX_BONES][7];
} Memory;
static Memory memory[MEMORIES];
static unsigned memory_clock;

static Memory *memory_for(int key, const NativeMesh *mesh)
{
    Memory *m = NULL, *spare = NULL;
    int i;
    for (i = 0; i < MEMORIES && !m; i++) {
        Memory *e = &memory[i];
        if (e->used && e->key == key) {
            m = e;
        } else if (!spare || (!e->used && spare->used) || (e->used == spare->used && e->stamp < spare->stamp)) {
            spare = e; /* an unused entry first, else the one drawn longest ago */
        }
    }
    if (!m) {
        m = spare;
        memset(m, 0, sizeof(*m));
        m->used = 1;
        m->key = key;
        m->mesh = mesh;
    } else if (m->mesh != mesh) {
        m->mesh = mesh;
        m->valid = m->fade = m->id = 0;
    }
    m->stamp = ++memory_clock;
    return m;
}

/* Which clip and where in it: the director. MEMORIES_NATIVE_CLIP=<name> plays that clip on a free-running clock (the game is
 * ignored); otherwise the disc row decides (idle/enter/attack/hit/destroyed/win) and the clip runs over the row's own length.
 * The attack is row field_DFE + 3 (info.attack_row): 3, or 4 when the card fights with its second guardian star. */
float NativeAnim_Choose(const NativeDraw *d, const NativeMesh *mesh, const char *forced, const NativeClip **clip_out)
{
    static const char *const by_act[NATIVE_ACT_COUNT] = {"Sword_Idle", "Idle_Loop", "Sword_Attack", "Hit_Chest", "Death01",
                                                         "Sword_Idle", "Sword_Idle"};
    int row = d->info.anim_index, attack = d->info.attack_row == 4 ? 4 : 3;
    const char *want = forced && *forced ? forced : by_act[NativeAnim_Act(row, d->info.attack_row)];
    const NativeClip *c = NULL;
    unsigned i;
    float phase, t;
    for (i = 0; i < mesh->clip_count; i++)
        if (strcmp(mesh->clips[i].name, want) == 0) c = &mesh->clips[i];
    if (!c && mesh->clip_count) c = &mesh->clips[0];
    *clip_out = c;
    if (!c || c->frames < 1) return 0.0f;
    if (forced && *forced) {
        float length = (float)c->frames / c->fps;
        t = (float)d->id / 30.0f;
        return t - (float)(int)(t / length) * length;
    }
    phase = d->info.anim_length > 0 ? (float)d->info.anim_frame / (16.0f * (float)d->info.anim_length) : 0.0f;
    phase = phase < 0.0f ? 0.0f : phase > 1.0f ? 1.0f : phase;
    if (row == 3 && attack == 3 && strcmp(c->name, "Sword_Attack") == 0 && c->frames == 47) {
        /* Piecewise time warp keyed to the game's events (disc frames of row 3: contact window opens at 29, closes at 61, second
         * contact at 95, row ends at 150) and the clip's own (hand-speed peak at frame 11, hold until 22, second swing at 30).
         * Measured on Black Luster Soldier's row 3 only: row 4 has no measurement yet, so its clip runs evenly over the row. */
        static const float disc[6] = {0.0f, 25.0f, 30.0f, 61.0f, 95.0f, 150.0f};
        static const float clip[6] = {0.0f, 8.0f, 11.0f, 22.0f, 30.0f, 46.0f};
        float frame = (float)d->info.anim_frame / 16.0f;
        int k;
        if (frame >= disc[5]) return clip[5] / c->fps;
        for (k = 0; k < 5 && frame >= disc[k + 1]; k++) continue;
        return (clip[k] + (clip[k + 1] - clip[k]) * (frame - disc[k]) / (disc[k + 1] - disc[k])) / c->fps;
    }
    return phase * (float)(c->frames - 1) / c->fps;
}

/* 3x4 (row major, implied last row 0 0 0 1) product: out = a * b. */
static void mul34(const float *a, const float *b, float *out)
{
    int r, c;
    for (r = 0; r < 3; r++) {
        for (c = 0; c < 3; c++) out[r * 4 + c] = a[r * 4] * b[c] + a[r * 4 + 1] * b[4 + c] + a[r * 4 + 2] * b[8 + c];
        out[r * 4 + 3] = a[r * 4] * b[3] + a[r * 4 + 1] * b[7] + a[r * 4 + 2] * b[11] + a[r * 4 + 3];
    }
}

/* The clip at time t (seconds): per bone the local matrix, forward kinematics, then rows = root view x world x inverse bind. */
void NativeAnim_Rows(const NativeDraw *d, const NativeMesh *mesh, const NativeClip *clip, float t, const NativeAnimFrame *frame,
                     float *rows)
{
    const int lit = frame->lit;
    float world[NATIVE_MAX_BONES][12];
    float lq[NATIVE_MAX_BONES][7]; /* local pose per bone: t[3], q[4] */
    unsigned char done[NATIVE_MAX_BONES];
    float rv[12];
    unsigned b, pass;
    int r, c;
    const NativeSlotInfo *in = &d->info;
    { /* the root's view matrix: ws * root, translation ws * root_t + ws_t (GTE: v' = R v / 4096 + TR) */
        float ws[9], rr[9];
        for (r = 0; r < 9; r++) {
            ws[r] = (float)in->ws_rot[r] / 4096.0f;
            rr[r] = (float)in->root_rot[r] / 4096.0f;
        }
        for (r = 0; r < 3; r++) {
            for (c = 0; c < 3; c++) rv[r * 4 + c] = ws[r * 3] * rr[c] + ws[r * 3 + 1] * rr[3 + c] + ws[r * 3 + 2] * rr[6 + c];
            rv[r * 4 + 3] = (ws[r * 3] * (float)in->root_tr[0] + ws[r * 3 + 1] * (float)in->root_tr[1] +
                             ws[r * 3 + 2] * (float)in->root_tr[2]) + (float)in->ws_tr[r];
        }
    }
    if (frame->log) {
        static unsigned n;
        if (n++ % 20 == 0) {
            const NativePart *p1 = &d->parts[1];
            fprintf(stderr, "skin: row=%d root_rot=%d,%d,%d/%d,%d,%d/%d,%d,%d root_tr=%d,%d,%d scale=%d ws_tr=%d,%d,%d | rv_t=%.0f,%.0f,%.0f | part1 used=%d tr=%d,%d,%d rot=%d,%d,%d/%d,%d,%d/%d,%d,%d ofx=%d h=%d\n",
                    in->anim_index, in->root_rot[0], in->root_rot[1], in->root_rot[2], in->root_rot[3], in->root_rot[4], in->root_rot[5],
                    in->root_rot[6], in->root_rot[7], in->root_rot[8], in->root_tr[0], in->root_tr[1], in->root_tr[2], in->scale[0],
                    in->ws_tr[0], in->ws_tr[1], in->ws_tr[2], rv[3], rv[7], rv[11], p1->used, p1->tr[0], p1->tr[1], p1->tr[2],
                    p1->rot[0], p1->rot[1], p1->rot[2], p1->rot[3], p1->rot[4], p1->rot[5], p1->rot[6], p1->rot[7], p1->rot[8],
                    d->ofx >> 16, d->h);
        }
    }
    /* The clip's local pose (linear between the baked frames, rotation nlerp), then a short cross-fade when the game's
     * animation row changes (the new row's clip starts elsewhere than the old one ended): the last pose drawn for this slot
     * is blended into the new one over NATIVE_FADE draws (game frames). */
    for (b = 0; b < mesh->bones; b++) {
        float *o = lq[b];
        o[0] = o[1] = o[2] = o[3] = o[4] = o[5] = 0.0f;
        o[6] = 1.0f;
        if (clip && clip->frames) {
            float f = t * clip->fps, k, len;
            unsigned i0, i1;
            const float *a, *bb;
            if (f < 0.0f) f = 0.0f;
            i0 = (unsigned)f;
            if (i0 >= clip->frames - 1) { i0 = clip->frames - 1; i1 = i0; k = 0.0f; }
            else { i1 = i0 + 1; k = f - (float)i0; }
            a = clip->data + ((size_t)i0 * mesh->bones + b) * 7;
            bb = clip->data + ((size_t)i1 * mesh->bones + b) * 7;
            for (r = 0; r < 3; r++) o[r] = a[r] + (bb[r] - a[r]) * k;
            for (r = 0; r < 4; r++) o[3 + r] = a[3 + r] + (bb[3 + r] - a[3 + r]) * k;
            len = sqrtf(o[3] * o[3] + o[4] * o[4] + o[5] * o[5] + o[6] * o[6]);
            if (len < 1e-8f) { o[3] = o[4] = o[5] = 0.0f; o[6] = 1.0f; }
            else for (r = 3; r < 7; r++) o[r] /= len;
        }
    }
    {
        Memory *m = memory_for(in->key, mesh);
        if (m->id != d->id + 1) { /* once per draw (the same draw can be replayed) */
            if (m->valid && m->row != in->anim_index) {
                memcpy(m->from, m->last, sizeof(m->from));
                m->fade = NATIVE_FADE;
            }
            m->row = in->anim_index;
            m->valid = 1;
            m->id = d->id + 1;
            if (m->fade > 0) {
                float w = (float)(NATIVE_FADE - m->fade + 1) / (float)(NATIVE_FADE + 1);
                for (b = 0; b < mesh->bones; b++) {
                    const float *fr = m->from[b];
                    float *o = lq[b], dot = fr[3] * o[3] + fr[4] * o[4] + fr[5] * o[5] + fr[6] * o[6], len;
                    for (r = 0; r < 3; r++) o[r] = fr[r] + (o[r] - fr[r]) * w;
                    for (r = 3; r < 7; r++) o[r] = fr[r] * (dot < 0.0f ? -1.0f : 1.0f) * (1.0f - w) + o[r] * w;
                    len = sqrtf(o[3] * o[3] + o[4] * o[4] + o[5] * o[5] + o[6] * o[6]);
                    for (r = 3; r < 7; r++) o[r] /= len;
                }
                m->fade--;
            }
            memcpy(m->last, lq, (size_t)mesh->bones * sizeof(lq[0]));
        } else {
            /* a replay of the same draw: the blended pose was stored in `last` */
            memcpy(lq, m->last, (size_t)mesh->bones * sizeof(lq[0]));
        }
    }
    memset(done, 0, sizeof(done));
    for (pass = 0; pass < NATIVE_MAX_BONES; pass++) {
        unsigned left = 0;
        for (b = 0; b < mesh->bones; b++) {
            const uint32_t *bt = mesh->bone_table + (size_t)b * 16;
            int parent = (int)bt[0];
            float loc[12];
            if (done[b]) continue;
            if (parent >= 0 && !done[parent]) { left++; continue; }
            memset(loc, 0, sizeof(loc));
            loc[0] = loc[5] = loc[10] = 1.0f;
            {   /* the (cross-faded) local pose of bone b: rotation as a unit quaternion, translation */
                const float *lp = lq[b];
                float x = lp[3], y = lp[4], z = lp[5], w = lp[6];
                loc[0] = 1 - 2 * (y * y + z * z); loc[1] = 2 * (x * y - z * w); loc[2] = 2 * (x * z + y * w);
                loc[4] = 2 * (x * y + z * w); loc[5] = 1 - 2 * (x * x + z * z); loc[6] = 2 * (y * z - x * w);
                loc[8] = 2 * (x * z - y * w); loc[9] = 2 * (y * z + x * w); loc[10] = 1 - 2 * (x * x + y * y);
                loc[3] = lp[0];
                loc[7] = lp[1];
                loc[11] = lp[2];
            }
            if (parent >= 0) mul34(world[parent], loc, world[b]);
            else memcpy(world[b], loc, sizeof(loc));
            done[b] = 1;
        }
        if (!left) break;
    }
    memset(rows, 0, (size_t)4 * NATIVE_SKIN_ROWS * 4 * sizeof(float));
    for (b = 0; b < mesh->bones; b++) {
        float m[12], v[12];
        const float *ibm = (const float *)(mesh->bone_table + (size_t)b * 16) + 1;
        mul34(world[b], ibm, m);
        mul34(rv, m, v);
        for (r = 0; r < 3; r++)
            for (c = 0; c < 4; c++) rows[((size_t)b * 4 + (size_t)r) * 4 + (size_t)c] = v[r * 4 + c];
    }
    { /* the draw: row 128 (texels 0-2), the light directions: row 129, the light colour matrix: row 130 */
        float *k = rows + (size_t)NATIVE_MAX_BONES * 4 * 4;
        const NativePart *lp = NULL;
        unsigned p;
        k[0] = (float)d->ofx / 65536.0f + frame->offset_x;
        k[1] = (float)d->ofy / 65536.0f + frame->offset_y;
        k[2] = (float)d->h;
        k[3] = (float)frame->scale;
        k[4] = (float)(d->tint & 0xff) / 128.0f;
        k[5] = (float)((d->tint >> 8) & 0xff) / 128.0f;
        k[6] = (float)((d->tint >> 16) & 0xff) / 128.0f;
        k[7] = (float)lit;
        k[8] = (float)d->bk[0] / 4096.0f;
        k[9] = (float)d->bk[1] / 4096.0f;
        k[10] = (float)d->bk[2] / 4096.0f;
        /* HDM4 light tuning (the game's lights are dim for a detailed model): ambient lift (texel 3 .x) and light gain (.y) */
        k[12] = frame->ambient;
        k[13] = frame->light_gain;
        for (p = 0; p < NATIVE_MAX_PARTS && !lp; p++)
            if (d->parts[p].used) lp = &d->parts[p];
        if (lp && lit) { /* d_i = unit(R_ls) x (light matrix row i), view space */
            float ru[9], sc[3];
            float *dirs = rows + (size_t)(NATIVE_MAX_BONES + 1) * 4 * 4, *cols = rows + (size_t)(NATIVE_MAX_BONES + 2) * 4 * 4;
            for (c = 0; c < 3; c++)
                sc[c] = sqrtf((float)lp->rot[c] * lp->rot[c] + (float)lp->rot[3 + c] * lp->rot[3 + c] + (float)lp->rot[6 + c] * lp->rot[6 + c]);
            for (r = 0; r < 3; r++)
                for (c = 0; c < 3; c++) ru[r * 3 + c] = sc[c] > 0.0f ? (float)lp->rot[r * 3 + c] / sc[c] : 0.0f;
            for (r = 0; r < 3; r++) { /* light r: texel r of row 129; colour row r of row 130 */
                for (c = 0; c < 3; c++) {
                    dirs[r * 4 + c] = (ru[c * 3] * (float)lp->llm[r * 3] + ru[c * 3 + 1] * (float)lp->llm[r * 3 + 1] +
                                       ru[c * 3 + 2] * (float)lp->llm[r * 3 + 2]) / 4096.0f;
                    cols[r * 4 + c] = (float)lp->lcm[r * 3 + c] / 4096.0f;
                }
            }
        }
    }
}

