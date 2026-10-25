/* The native model's animation without OpenGL (src/pc/render/native_anim.h): the disc row picks the clip (the attack is
 * row field_DFE + 3), the attack row of Black Luster Soldier is time-warped onto the game's contact frames, the clip is
 * posed by forward kinematics into the skinning rows, and a row change cross-fades over NATIVE_FADE draws; a package's
 * clip choices (with the fallbacks of an act it has no clip for), strike frames and scale (native_registry.h) are
 * honoured. */
#include "pc/render/native_anim.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures;

#define CHECK(condition)                                                              \
    do {                                                                              \
        if (!(condition)) {                                                           \
            fprintf(stderr, "%s:%d: CHECK(%s) failed\n", __FILE__, __LINE__, #condition); \
            failures++;                                                               \
        }                                                                             \
    } while (0)

static int near(float a, float b)
{
    return fabsf(a - b) < 1e-3f;
}

/* Two bones: the root, and a child standing 10 up from it (its inverse bind takes it back). */
#define BONES 2
static uint32_t bone_table[BONES * 16];
enum { IDLE, LOOP, ATTACK, HIT, DEATH, CLIPS };
static const char *const clip_names[CLIPS] = {"Sword_Idle", "Idle_Loop", "Sword_Attack", "Hit_Chest", "Death01"};
static const unsigned clip_frames[CLIPS] = {1, 1, 47, 2, 1};
static float clip_data[CLIPS][47 * BONES * 7];
static NativeMesh mesh;

static void put_float(uint32_t *word, float value)
{
    memcpy(word, &value, sizeof(value));
}

/* A local pose key: translation, then rotation as a quaternion (x, y, z, w). */
static void key(float *at, float tx, float ty, float tz, float qx, float qy, float qz, float qw)
{
    at[0] = tx;
    at[1] = ty;
    at[2] = tz;
    at[3] = qx;
    at[4] = qy;
    at[5] = qz;
    at[6] = qw;
}

static void build(void)
{
    const float s = sqrtf(0.5f); /* a quarter turn about z: (0, 0, s, s) */
    unsigned c, f;
    memset(bone_table, 0, sizeof(bone_table));
    bone_table[0] = (uint32_t)-1;
    bone_table[16] = 0;
    for (c = 0; c < BONES; c++) {
        put_float(&bone_table[c * 16 + 1], 1.0f);
        put_float(&bone_table[c * 16 + 6], 1.0f);
        put_float(&bone_table[c * 16 + 11], 1.0f);
    }
    put_float(&bone_table[16 + 8], -10.0f); /* bone 1's inverse bind: translation (0, -10, 0) */
    memset(&mesh, 0, sizeof(mesh));
    mesh.bones = BONES;
    mesh.bone_table = bone_table;
    mesh.clip_count = CLIPS;
    for (c = 0; c < CLIPS; c++) {
        snprintf(mesh.clips[c].name, sizeof(mesh.clips[c].name), "%s", clip_names[c]);
        mesh.clips[c].frames = clip_frames[c];
        mesh.clips[c].fps = 30.0f;
        mesh.clips[c].data = clip_data[c];
        for (f = 0; f < clip_frames[c]; f++) {
            float *at = clip_data[c] + (size_t)f * BONES * 7;
            int turned = c == HIT; /* Hit_Chest: the root a quarter turn about z */
            key(at, 0, 0, 0, 0, 0, turned ? s : 0.0f, turned ? s : 1.0f);
            key(at + 7, 0, 10, 0, 0, 0, 0, 1);
        }
    }
}

static NativeDraw draw;

static void set_draw(int id, int slot, int row, int attack_row, int frame, int length)
{
    int k;
    memset(&draw, 0, sizeof(draw));
    draw.id = id;
    draw.ofx = 160 << 16;
    draw.ofy = 120 << 16;
    draw.h = 1000;
    draw.tint = 0x808080u;
    draw.info.slot = slot;
    draw.info.key = slot;
    draw.info.anim_index = row;
    draw.info.attack_row = attack_row;
    draw.info.anim_frame = frame;
    draw.info.anim_length = length;
    for (k = 0; k < 3; k++) {
        draw.info.root_rot[k * 4] = 4096;
        draw.info.ws_rot[k * 4] = 4096;
    }
    draw.info.ws_tr[2] = 1000;
}

static const char *chosen(int row, int attack_row)
{
    const NativeClip *clip = NULL;
    set_draw(1, 0, row, attack_row, 0, 10);
    NativeAnim_Choose(&draw, &mesh, NULL, &clip);
    return clip ? clip->name : "";
}

static float time_at(int row, int attack_row, int frame, int length, const NativeClip **clip)
{
    set_draw(1, 0, row, attack_row, frame, length);
    return NativeAnim_Choose(&draw, &mesh, NULL, clip);
}

static float rows[4 * NATIVE_SKIN_ROWS * 4];

static const float *bone_row(unsigned bone, unsigned row)
{
    return rows + ((size_t)bone * 4 + row) * 4;
}

static void pose_mesh(int id, int key, int row, const NativeMesh *with)
{
    NativeAnimFrame frame;
    const NativeClip *clip = NULL;
    float t;
    memset(&frame, 0, sizeof(frame));
    frame.scale = 2;
    set_draw(id, 0, row, 3, 0, 10);
    draw.info.key = key;
    t = NativeAnim_Choose(&draw, with, NULL, &clip);
    NativeAnim_Rows(&draw, with, clip, t, &frame, rows);
}

static void pose(int id, int slot, int row)
{
    NativeAnimFrame frame;
    const NativeClip *clip = NULL;
    float t;
    memset(&frame, 0, sizeof(frame));
    frame.offset_x = 8.0f;
    frame.offset_y = 16.0f;
    frame.scale = 2;
    frame.lit = 0;
    frame.ambient = 0.2f;
    frame.light_gain = 1.5f;
    set_draw(id, slot, row, 3, 0, 10);
    t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
    NativeAnim_Rows(&draw, &mesh, clip, t, &frame, rows);
}

int main(void)
{
    const NativeClip *clip = NULL;
    float t;
    build();

    /* The director's rows. */
    CHECK(strcmp(chosen(0, 3), "Sword_Idle") == 0);
    CHECK(strcmp(chosen(1, 3), "Sword_Idle") == 0);
    CHECK(strcmp(chosen(2, 3), "Idle_Loop") == 0);
    CHECK(strcmp(chosen(3, 3), "Sword_Attack") == 0);
    CHECK(strcmp(chosen(4, 3), "Sword_Idle") == 0);   /* the other guardian star's attack row */
    CHECK(strcmp(chosen(4, 4), "Sword_Attack") == 0); /* the second guardian star: row 4 is the attack */
    CHECK(strcmp(chosen(3, 4), "Sword_Idle") == 0);
    CHECK(strcmp(chosen(5, 3), "Hit_Chest") == 0);
    CHECK(strcmp(chosen(6, 3), "Death01") == 0);
    CHECK(strcmp(chosen(7, 3), "Sword_Idle") == 0);
    CHECK(strcmp(chosen(8, 3), "Sword_Idle") == 0);   /* past the table: the first entry */
    CHECK(strcmp(chosen(0, 0), "Sword_Idle") == 0);   /* no attack row captured: row 3 is the attack */

    /* Row 3's time warp (Black Luster Soldier's contact frames) and row 4's even run. */
    t = time_at(3, 3, 30 * 16, 150, &clip);
    CHECK(clip && strcmp(clip->name, "Sword_Attack") == 0 && near(t, 11.0f / 30.0f));
    CHECK(near(time_at(3, 3, 0, 150, &clip), 0.0f));
    CHECK(near(time_at(3, 3, 61 * 16, 150, &clip), 22.0f / 30.0f));
    CHECK(near(time_at(3, 3, 200 * 16, 150, &clip), 46.0f / 30.0f));
    CHECK(near(time_at(4, 4, 75 * 16, 150, &clip), 0.5f * 46.0f / 30.0f));
    CHECK(near(time_at(5, 3, 5 * 16, 10, &clip), 0.5f * 1.0f / 30.0f));
    CHECK(near(time_at(5, 3, 99 * 16, 10, &clip), 1.0f / 30.0f)); /* past the row's end: its last frame */

    /* A forced clip runs on the draw count, round its own length (47 frames at 30 fps). */
    set_draw(60, 0, 0, 3, 0, 10);
    t = NativeAnim_Choose(&draw, &mesh, "Sword_Attack", &clip);
    CHECK(clip && strcmp(clip->name, "Sword_Attack") == 0 && near(t, 2.0f - 47.0f / 30.0f));

    /* Forward kinematics: identity root and view, so every bone's row is the view's (translation 0, 0, 1000); the
     * child's 10 up is undone by its inverse bind. Row 128 carries the draw. */
    pose(1, 2, 0);
    CHECK(near(bone_row(0, 0)[0], 1.0f) && near(bone_row(0, 1)[1], 1.0f) && near(bone_row(0, 2)[2], 1.0f));
    CHECK(near(bone_row(0, 2)[3], 1000.0f) && near(bone_row(1, 2)[3], 1000.0f) && near(bone_row(1, 1)[3], 0.0f));
    {
        const float *k = rows + (size_t)NATIVE_MAX_BONES * 4 * 4;
        CHECK(near(k[0], 168.0f) && near(k[1], 136.0f) && near(k[2], 1000.0f) && near(k[3], 2.0f));
        CHECK(near(k[4], 1.0f) && near(k[5], 1.0f) && near(k[6], 1.0f) && near(k[7], 0.0f));
        CHECK(near(k[12], 0.2f) && near(k[13], 1.5f));
    }

    /* A row change cross-fades: slot 1 idles, then is hit (the root a quarter turn about z). The first hit draw is
     * 1/7 of the way there, the same draw replayed is the same, and after NATIVE_FADE draws it is the hit pose. */
    pose(10, 1, 0);
    CHECK(near(bone_row(0, 0)[0], 1.0f) && near(bone_row(0, 1)[0], 0.0f));
    pose(11, 1, 5);
    {
        float c0 = bone_row(0, 0)[0], s0 = bone_row(0, 1)[0];
        CHECK(c0 < 0.999f && c0 > 0.5f && s0 > 0.01f); /* turned a little, not all the way */
        pose(11, 1, 5);
        CHECK(near(bone_row(0, 0)[0], c0) && near(bone_row(0, 1)[0], s0));
    }
    {
        int id;
        for (id = 12; id < 12 + NATIVE_FADE; id++) pose(id, 1, 5);
    }
    CHECK(near(bone_row(0, 0)[0], 0.0f) && near(bone_row(0, 1)[0], 1.0f)); /* x goes to y: a quarter turn */
    CHECK(near(bone_row(1, 2)[3], 1000.0f) && near(bone_row(1, 0)[3], 0.0f)); /* the child turns with it, in place */

    /* The acts of the rows. */
    CHECK(NativeAnim_Act(0, 3) == NATIVE_ACT_IDLE && NativeAnim_Act(1, 3) == NATIVE_ACT_IDLE);
    CHECK(NativeAnim_Act(2, 3) == NATIVE_ACT_ENTER && NativeAnim_Act(3, 3) == NATIVE_ACT_ATTACK);
    CHECK(NativeAnim_Act(4, 3) == NATIVE_ACT_IDLE && NativeAnim_Act(4, 4) == NATIVE_ACT_ATTACK && NativeAnim_Act(3, 4) == NATIVE_ACT_IDLE);
    CHECK(NativeAnim_Act(5, 3) == NATIVE_ACT_HIT && NativeAnim_Act(6, 3) == NATIVE_ACT_DESTROYED);
    CHECK(NativeAnim_Act(7, 3) == NATIVE_ACT_WIN && NativeAnim_Act(8, 3) == NATIVE_ACT_GUARD && NativeAnim_Act(9, 3) == NATIVE_ACT_IDLE);
    CHECK(NativeAnim_Act(3, 0) == NATIVE_ACT_ATTACK); /* no attack row captured: row 3 */

    /* Two monsters drawn by turns in different rows (one idle, one hit: two field monsters through slot 0) keep their
     * own poses: neither fades into the other's. */
    {
        int id = 100, k;
        for (k = 0; k < 2 * (NATIVE_FADE + 2); k++, id++) pose_mesh(id, k & 1 ? 0x10002 : 0x10001, k & 1 ? 5 : 0, &mesh);
        CHECK(near(bone_row(0, 0)[0], 0.0f) && near(bone_row(0, 1)[0], 1.0f)); /* the hit one, fully turned */
        pose_mesh(id++, 0x10001, 0, &mesh);
        CHECK(near(bone_row(0, 0)[0], 1.0f) && near(bone_row(0, 1)[0], 0.0f)); /* the idle one, not turned at all */
    }
    /* A key whose mesh changed starts afresh: no fade from the other skeleton's pose. */
    {
        static NativeMesh other;
        other = mesh;
        pose_mesh(200, 0x20001, 5, &mesh);
        pose_mesh(201, 0x20001, 5, &mesh); /* settled on the hit pose ... */
        pose_mesh(202, 0x20001, 0, &other); /* ... then idle with another mesh: idle at once */
        CHECK(near(bone_row(0, 0)[0], 1.0f) && near(bone_row(0, 1)[0], 0.0f));
    }
    /* More monsters than the memory holds: the oldest gives its place, and every draw still poses. */
    {
        int k;
        for (k = 0; k < 40; k++) pose_mesh(300 + k, 0x30000 + k, 0, &mesh);
        CHECK(near(bone_row(0, 0)[0], 1.0f));
    }

    /* A package's choices (model.json, native_registry.c): an act's clip by index + 1, the others by the default names;
     * a mesh without clips plays none. */
    {
        static NativeMesh mapped, bare;
        const NativeMesh *keep = &mesh;
        mapped = mesh;
        mapped.act_clip[NATIVE_ACT_ATTACK] = HIT + 1;
        mapped.act_clip[NATIVE_ACT_IDLE] = DEATH + 1;
        set_draw(1, 0, 3, 3, 0, 10);
        NativeAnim_Choose(&draw, &mapped, NULL, &clip);
        CHECK(clip && strcmp(clip->name, "Hit_Chest") == 0);
        set_draw(1, 0, 0, 3, 0, 10);
        NativeAnim_Choose(&draw, &mapped, NULL, &clip);
        CHECK(clip && strcmp(clip->name, "Death01") == 0);
        CHECK(NativeAnim_ActClip(&mapped, NATIVE_ACT_HIT) == &mapped.clips[HIT]); /* not mapped: its default name */
        CHECK(NativeAnim_ActClip(keep, NATIVE_ACT_WIN) == &keep->clips[IDLE]);
        memset(&bare, 0, sizeof(bare));
        CHECK(NativeAnim_ActClip(&bare, NATIVE_ACT_IDLE) == NULL && NativeAnim_ActClip(&mesh, NATIVE_ACT_COUNT) == NULL);
    }
    /* An act without a clip plays the nearest act that has one: guard and destroyed the hit, the others the idle. */
    {
        static NativeMesh partial;
        partial = mesh;
        snprintf(partial.clips[IDLE].name, sizeof(partial.clips[IDLE].name), "Stand");
        snprintf(partial.clips[HIT].name, sizeof(partial.clips[HIT].name), "Ouch");
        snprintf(partial.clips[LOOP].name, sizeof(partial.clips[LOOP].name), "Spin");
        snprintf(partial.clips[DEATH].name, sizeof(partial.clips[DEATH].name), "Fall");
        CHECK(NativeAnim_ActClip(&partial, NATIVE_ACT_GUARD) == &partial.clips[0]); /* nothing mapped, no default names */
        partial.act_clip[NATIVE_ACT_IDLE] = IDLE + 1;
        partial.act_clip[NATIVE_ACT_HIT] = HIT + 1;
        CHECK(NativeAnim_ActClip(&partial, NATIVE_ACT_GUARD) == &partial.clips[HIT]);
        CHECK(NativeAnim_ActClip(&partial, NATIVE_ACT_DESTROYED) == &partial.clips[HIT]);
        CHECK(NativeAnim_ActClip(&partial, NATIVE_ACT_WIN) == &partial.clips[IDLE]);
        CHECK(NativeAnim_ActClip(&partial, NATIVE_ACT_ENTER) == &partial.clips[IDLE]);
        CHECK(NativeAnim_ActClip(&partial, NATIVE_ACT_ATTACK) == &partial.clips[ATTACK]); /* Sword_Attack: its default name */
        partial.act_clip[NATIVE_ACT_HIT] = 0;
        CHECK(NativeAnim_ActClip(&partial, NATIVE_ACT_GUARD) == &partial.clips[IDLE]); /* no hit either: the idle */
    }
    /* The blow's frame known (a code mod's draw): the package's first strike frame lands on it, both ends fixed; the
     * second guardian star's row too. Unknown (the arena) or no strike frames: as before. */
    {
        static NativeMesh struck;
        struck = mesh;
        struck.strike_count = 2;
        struck.strike[0] = 11;
        struck.strike[1] = 30;
        set_draw(1, 0, 3, 3, 75 * 16, 150);
        draw.info.contact_frame = 75;
        CHECK(near(NativeAnim_Choose(&draw, &struck, NULL, &clip), 11.0f / 30.0f) && clip == &struck.clips[ATTACK]);
        draw.info.anim_frame = 0;
        CHECK(near(NativeAnim_Choose(&draw, &struck, NULL, &clip), 0.0f));
        draw.info.anim_frame = 150 * 16;
        CHECK(near(NativeAnim_Choose(&draw, &struck, NULL, &clip), 46.0f / 30.0f));
        draw.info.anim_frame = 375 * 16 / 10; /* 37.5: half way to the blow */
        CHECK(near(NativeAnim_Choose(&draw, &struck, NULL, &clip), 5.5f / 30.0f));
        draw.info.anim_frame = 1125 * 16 / 10; /* 112.5: half way from the blow to the end */
        CHECK(near(NativeAnim_Choose(&draw, &struck, NULL, &clip), 28.5f / 30.0f));
        set_draw(1, 0, 4, 4, 40 * 16, 80);
        draw.info.contact_frame = 40;
        CHECK(near(NativeAnim_Choose(&draw, &struck, NULL, &clip), 11.0f / 30.0f));
        set_draw(1, 0, 3, 3, 30 * 16, 150);
        draw.info.contact_frame = -1; /* the arena: Black Luster Soldier's measured warp */
        CHECK(near(NativeAnim_Choose(&draw, &struck, NULL, &clip), 11.0f / 30.0f));
        draw.info.contact_frame = 75;
        struck.strike_count = 0; /* no strike frames: the measured warp too */
        CHECK(near(NativeAnim_Choose(&draw, &struck, NULL, &clip), 11.0f / 30.0f));
        struck.strike_count = 1;
        set_draw(1, 0, 5, 3, 5 * 16, 10);
        draw.info.contact_frame = 5; /* not the attack: no warp */
        CHECK(near(NativeAnim_Choose(&draw, &struck, NULL, &clip), 0.5f * 1.0f / 30.0f));
    }
    /* A package's scale is about the soles: twice the size, the ground (y = 10, y down) where it was. */
    {
        static NativeMesh big;
        big = mesh;
        big.scale = 2.0f;
        big.ground = 10.0f;
        pose_mesh(400, 0x40000, 0, &big);
        CHECK(near(bone_row(0, 0)[0], 2.0f) && near(bone_row(0, 1)[1], 2.0f) && near(bone_row(0, 2)[2], 2.0f));
        CHECK(near(bone_row(0, 1)[3], -10.0f) && near(bone_row(0, 2)[3], 1000.0f)); /* y' = 2 y - 10: 10 stays 10 */
        CHECK(near(bone_row(0, 1)[1] * 10.0f + bone_row(0, 1)[3], 10.0f));
    }

    /* A package's offset moves it along its own axes, whatever the scale. */
    {
        static NativeMesh moved;
        moved = mesh;
        moved.offset[0] = 30.0f;
        moved.offset[2] = -20.0f;
        pose_mesh(400, 0x40000, 0, &moved);
        CHECK(near(bone_row(0, 0)[3], 30.0f) && near(bone_row(0, 2)[3], 980.0f));
        moved.scale = 2.0f;
        pose_mesh(400, 0x40000, 0, &moved);
        CHECK(near(bone_row(0, 0)[3], 30.0f) && near(bone_row(0, 2)[3], 980.0f));
    }

    /* Transport (E3): inactive = unchanged behaviour. */
    {
        NativeAnim_TransportInit();
        NativeAnim_TransportSetActive(0);
        set_draw(1, 0, 3, 3, 30 * 16, 150);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(clip && strcmp(clip->name, "Sword_Attack") == 0 && near(t, 11.0f / 30.0f));
        /* Forced clip via env still works when transport inactive. */
        set_draw(60, 0, 0, 3, 0, 10);
        t = NativeAnim_Choose(&draw, &mesh, "Sword_Attack", &clip);
        CHECK(clip && strcmp(clip->name, "Sword_Attack") == 0 && near(t, 2.0f - 47.0f / 30.0f));
    }

    /* Transport active: forced clip overrides env forced. */
    {
        NativeAnim_TransportInit();
        NativeAnim_TransportSetActive(1);
        NativeAnim_TransportSetForcedClip("Hit_Chest");
        set_draw(1, 0, 3, 3, 0, 10); /* would be attack row */
        t = NativeAnim_Choose(&draw, &mesh, "Sword_Attack", &clip); /* env forced ignored */
        CHECK(clip && strcmp(clip->name, "Hit_Chest") == 0);
        /* Free clock runs on draw id, not game frame. */
        set_draw(30, 0, 0, 3, 0, 10);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        float expected = (30.0f / 30.0f) - (float)(int)(30.0f / 30.0f / (2.0f / 30.0f)) * (2.0f / 30.0f);
        CHECK(near(t, expected));
        /* Clear forced clip -> back to game-decided. */
        NativeAnim_TransportSetForcedClip(NULL);
        set_draw(1, 0, 3, 3, 30 * 16, 150);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(clip && strcmp(clip->name, "Sword_Attack") == 0 && near(t, 11.0f / 30.0f));
    }

    /* Transport pause/resume on free-running clip. */
    {
        NativeAnim_TransportInit();
        NativeAnim_TransportSetActive(1);
        NativeAnim_TransportSetForcedClip("Sword_Attack");
        set_draw(10, 0, 0, 3, 0, 10);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        float t10 = t;
        set_draw(20, 0, 0, 3, 0, 10);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        float t20 = t;
        CHECK(!near(t, t10)); /* advanced */
        NativeAnim_TransportSetPaused(1);
        set_draw(30, 0, 0, 3, 0, 10);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(near(t, t20)); /* frozen at id=20 */
        NativeAnim_TransportSetPaused(0);
        set_draw(40, 0, 0, 3, 0, 10);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(!near(t, t20)); /* resumes from id=40 */
    }

    /* Transport speed on free-running clip. */
    {
        NativeAnim_TransportInit();
        NativeAnim_TransportSetActive(1);
        NativeAnim_TransportSetForcedClip("Sword_Attack");
        NativeAnim_TransportSetSpeed(2.0f);
        set_draw(30, 0, 0, 3, 0, 10); /* id=30, speed=2 -> effective id=60 */
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        float expected = (60.0f / 30.0f) - (float)(int)(60.0f / 30.0f / (47.0f / 30.0f)) * (47.0f / 30.0f);
        CHECK(near(t, expected));
        NativeAnim_TransportSetSpeed(0.5f);
        set_draw(30, 0, 0, 3, 0, 10); /* id=30, speed=0.5 -> effective id=15 */
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        expected = (15.0f / 30.0f) - (float)(int)(15.0f / 30.0f / (47.0f / 30.0f)) * (47.0f / 30.0f);
        CHECK(near(t, expected));
        /* Speed clamped to 0.05..8. */
        NativeAnim_TransportSetSpeed(10.0f);
        CHECK(near(native_anim_transport.speed, 8.0f));
        NativeAnim_TransportSetSpeed(0.01f);
        CHECK(near(native_anim_transport.speed, 0.05f));
    }

    /* Transport phase override on row-driven clip (attack row: feeds strike_warp). */
    {
        NativeAnim_TransportInit();
        NativeAnim_TransportSetActive(1);
        /* Phase 0.5 on row 3 (attack, length 150) -> anim_frame = 0.5 * 16 * 150 = 1200 -> disc frame 75.
         * strike_warp: contact=75, strike=11 -> t = strike * frame/contact / fps = 11 * 75/75 / 30 = 11/30. */
        set_draw(1, 0, 3, 3, 0, 150);
        draw.info.contact_frame = 75;
        mesh.strike_count = 1;
        mesh.strike[0] = 11;
        NativeAnim_TransportSetPhase(0.5f);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(clip && strcmp(clip->name, "Sword_Attack") == 0 && near(t, 11.0f / 30.0f));
        /* Phase 0 -> anim_frame=0 -> t=0. */
        NativeAnim_TransportSetPhase(0.0f);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(near(t, 0.0f));
        /* Phase 1 -> anim_frame=2400 -> disc frame 150 -> t = (strike + (last-strike)*(150-75)/(150-75))/fps = 46/30. */
        NativeAnim_TransportSetPhase(1.0f);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(near(t, 46.0f / 30.0f));
        /* Phase out of range -> cleared. */
        NativeAnim_TransportSetPhase(1.5f);
        CHECK(native_anim_transport.phase_override < 0);
        NativeAnim_TransportSetPhase(-0.1f);
        CHECK(native_anim_transport.phase_override < 0);
        mesh.strike_count = 0;
    }

    /* Transport phase override on BLS measured warp (row 3, Sword_Attack, 47 frames). */
    {
        NativeAnim_TransportInit();
        NativeAnim_TransportSetActive(1);
        set_draw(1, 0, 3, 3, 0, 150);
        draw.info.contact_frame = -1; /* triggers BLS warp */
        /* Phase 0.2 -> anim_frame = 0.2 * 16 * 150 = 480 -> disc frame 30.
         * BLS warp: disc[2]=30 -> clip[2]=11 -> t=11/30. */
        NativeAnim_TransportSetPhase(0.2f);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(clip && strcmp(clip->name, "Sword_Attack") == 0 && near(t, 11.0f / 30.0f));
        /* Phase 0.4 -> anim_frame = 0.4 * 16 * 150 = 960 -> disc frame 60.
         * Between disc[2]=30 (clip=11) and disc[3]=61 (clip=22): (60-30)/(61-30) * (22-11) + 11 = 21.66. */
        NativeAnim_TransportSetPhase(0.4f);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        float expected_bls = (11.0f + (22.0f - 11.0f) * (60.0f - 30.0f) / (61.0f - 30.0f)) / 30.0f;
        CHECK(near(t, expected_bls));
    }

    /* Transport frame override on row-driven clip. */
    {
        NativeAnim_TransportInit();
        NativeAnim_TransportSetActive(1);
        set_draw(1, 0, 5, 3, 0, 10); /* hit row, clip Hit_Chest (2 frames) */
        /* Frame 1 (second frame of 2) -> phase = 1/(2-1) = 1 -> anim_frame = 1 * 16 * 10 = 160. */
        NativeAnim_TransportSetFrame(1);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(clip && strcmp(clip->name, "Hit_Chest") == 0 && near(t, 1.0f / 30.0f));
        /* Frame 0 -> phase = 0 -> t=0. */
        NativeAnim_TransportSetFrame(0);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(near(t, 0.0f));
        /* Frame out of range -> clamped to last frame. */
        NativeAnim_TransportSetFrame(100);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(near(t, 1.0f / 30.0f));
        /* Clear frame override. */
        NativeAnim_TransportSetFrame(-1);
        CHECK(native_anim_transport.frame_override < 0);
    }

    /* Transport pause on row-driven clip holds last anim_frame. */
    {
        NativeAnim_TransportInit();
        NativeAnim_TransportSetActive(1);
        set_draw(1, 0, 3, 3, 30 * 16, 150); /* anim_frame=480, phase=0.2 */
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        float t_at_480 = t;
        NativeAnim_TransportSetPaused(1);
        set_draw(2, 0, 3, 3, 150 * 16, 150); /* game advances to end of row */
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(near(t, t_at_480)); /* frozen at anim_frame=480 */
        NativeAnim_TransportSetPaused(0);
        t = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
        CHECK(near(t, 46.0f / 30.0f)); /* now at game's anim_frame=2400 */
    }

    /* NativeAnim_Command parsing. */
    {
        char reply[256];
        NativeAnim_TransportInit();
        CHECK(native_anim_transport.active == 0);
        CHECK(NativeAnim_Command("anim pause", reply, sizeof(reply)) == 0);
        CHECK(native_anim_transport.active == 1);   /* a transport command turns it on */
        NativeAnim_TransportInit();
        NativeAnim_TransportSetActive(1);
        CHECK(NativeAnim_Command("anim clip Sword_Attack", reply, sizeof(reply)) == 0);
        CHECK(strstr(reply, "ok clip=Sword_Attack") != NULL);
        CHECK(NativeAnim_Command("anim clip auto", reply, sizeof(reply)) == 0);
        CHECK(strstr(reply, "ok clip=auto") != NULL);
        CHECK(NativeAnim_Command("anim pause", reply, sizeof(reply)) == 0);
        CHECK(strstr(reply, "ok paused") != NULL);
        CHECK(NativeAnim_Command("anim resume", reply, sizeof(reply)) == 0);
        CHECK(strstr(reply, "ok resumed") != NULL);
        CHECK(NativeAnim_Command("anim speed 2.5", reply, sizeof(reply)) == 0);
        CHECK(strstr(reply, "ok speed=2.500") != NULL);
        CHECK(NativeAnim_Command("anim phase 0.5", reply, sizeof(reply)) == 0);
        CHECK(strstr(reply, "ok phase=0.500") != NULL);
        CHECK(NativeAnim_Command("anim frame 10", reply, sizeof(reply)) == 0);
        CHECK(strstr(reply, "ok frame=10") != NULL);
        CHECK(NativeAnim_Command("anim get", reply, sizeof(reply)) == 0);
        CHECK(strstr(reply, "ok active=1") != NULL);
        /* Errors. */
        CHECK(NativeAnim_Command("anim clip", reply, sizeof(reply)) == -1);
        CHECK(strstr(reply, "err clip needs a name") != NULL);
        CHECK(NativeAnim_Command("anim speed", reply, sizeof(reply)) == -1);
        CHECK(strstr(reply, "err speed needs a number") != NULL);
        CHECK(NativeAnim_Command("anim phase", reply, sizeof(reply)) == -1);
        CHECK(strstr(reply, "err phase needs a number") != NULL);
        CHECK(NativeAnim_Command("anim frame", reply, sizeof(reply)) == -1);
        CHECK(strstr(reply, "err frame needs an integer") != NULL);
        CHECK(NativeAnim_Command("anim unknown", reply, sizeof(reply)) == -1);
        CHECK(strstr(reply, "err unknown anim subcommand") != NULL);
        CHECK(NativeAnim_Command("notanim clip", reply, sizeof(reply)) == -1);
        CHECK(strstr(reply, "err not an anim command") != NULL);
    }

    /* Parser torture: the command parser must never crash, must NUL-terminate within n, must never
     * write past the buffer (a canary byte after the n-byte region is never written), and an `err`
     * reply must leave the transport state byte-for-byte unchanged. */
    {
        char reply[256];
        char before[256], after[256];

        /* Malformed top-level lines all error and do not crash. */
        CHECK(NativeAnim_Command("", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim ", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("   \t ", reply, sizeof(reply)) == -1);

        /* A 4000-char line is rejected and the reply stays NUL-terminated. */
        {
            char big[4001];
            memset(big, 'x', sizeof(big) - 1);
            big[0] = 'a'; big[1] = 'n'; big[2] = 'i'; big[3] = 'm'; big[4] = ' ';
            big[sizeof(big) - 1] = '\0';
            memset(reply, 0xAB, sizeof(reply));
            CHECK(NativeAnim_Command(big, reply, sizeof(reply)) == -1);
            CHECK(memchr(reply, '\0', sizeof(reply)) != NULL);
        }

        /* The reply buffer is never overrun and is NUL-terminated whenever n > 0. */
        {
            static const char *const cmds[] = {
                "anim get",
                "anim clip Sword_Attack",
                "anim speed nan",
                "anim pause",
                "anim unknown junk"
            };
            static const size_t sizes[] = {0, 1, 2, 8, 64};
            size_t ci, si;
            for (ci = 0; ci < sizeof(cmds) / sizeof(cmds[0]); ci++) {
                for (si = 0; si < sizeof(sizes) / sizeof(sizes[0]); si++) {
                    size_t ns = sizes[si];
                    unsigned char buf[80];
                    memset(buf, 0xAB, sizeof(buf));
                    NativeAnim_Command(cmds[ci], (char *)buf, ns);
                    CHECK(buf[ns] == 0xAB); /* the canary byte after the buffer is never written */
                    if (ns > 0) CHECK(memchr(buf, '\0', ns) != NULL); /* always NUL-terminated within n */
                }
            }
        }

        /* TimeMapClip unit tests: */
        {
            const float points1[][2] = {{0.0f,0.0f},{10.0f,20.0f},{30.0f,40.0f}};
            CHECK(NativeAnim_TimeMapClip(points1, 3, 0.0f) == 0.0f);
            CHECK(NativeAnim_TimeMapClip(points1, 3, 10.0f) == 5.0f);
            CHECK(NativeAnim_TimeMapClip(points1, 3, 20.0f) == 10.0f);
            CHECK(NativeAnim_TimeMapClip(points1, 3, 30.0f) == 20.0f);
            CHECK(NativeAnim_TimeMapClip(points1, 3, 40.0f) == 30.0f);
            CHECK(NativeAnim_TimeMapClip(points1, 3, 50.0f) == 30.0f);
            const float points2[][2] = {{0.0f,0.0f},{10.0f,10.0f}}; /* linear default */
            CHECK(NativeAnim_TimeMapClip(points2, 2, 5.0f) == 5.0f);
            /* Midpoint of two-segment map */
            const float points3[][2] = {{0.0f,0.0f},{10.0f,10.0f},{30.0f,20.0f}};
            CHECK(NativeAnim_TimeMapClip(points3, 3, 15.0f) == 20.0f);
        }

        NativeAnim_TransportInit();
        CHECK(NativeAnim_Command("anim speed 2.5", reply, sizeof(reply)) == 0);
        CHECK(NativeAnim_Command("anim speed nan", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim speed inf", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim speed 1e99", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim speed 1,5", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim speed -1", reply, sizeof(reply)) == 0);
        CHECK(native_anim_transport.speed >= 0.05f);
        CHECK(NativeAnim_Command("anim speed 0", reply, sizeof(reply)) == 0);
        CHECK(native_anim_transport.speed >= 0.05f);
        CHECK(NativeAnim_Command("anim speed 9", reply, sizeof(reply)) == 0);
        CHECK(native_anim_transport.speed <= 8.0f);
        CHECK(NativeAnim_Command("anim speed 0x10", reply, sizeof(reply)) == 0); /* hex 16 clamps to 8 */
        CHECK(native_anim_transport.speed <= 8.0f);
        CHECK(NativeAnim_Command("anim phase 1.0000001", reply, sizeof(reply)) == 0);
        CHECK(native_anim_transport.phase_override < 0); /* out of range clears */
        CHECK(NativeAnim_Command("anim phase -0.0001", reply, sizeof(reply)) == 0);
        CHECK(native_anim_transport.phase_override < 0);
        CHECK(NativeAnim_Command("anim phase abc", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim phase nan", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim phase 0.5", reply, sizeof(reply)) == 0);
        CHECK(near(native_anim_transport.phase_override, 0.5f));
        CHECK(NativeAnim_Command("anim frame -5", reply, sizeof(reply)) == 0);
        CHECK(native_anim_transport.frame_override < 0); /* negative clears */
        CHECK(NativeAnim_Command("anim frame 99999999999", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim frame 1.5", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim frame 12", reply, sizeof(reply)) == 0);
        CHECK(native_anim_transport.frame_override == 12);

        /* Tabs are whitespace at every boundary. */
        NativeAnim_TransportInit();
        CHECK(NativeAnim_Command("anim\tpause", reply, sizeof(reply)) == 0);
        CHECK(native_anim_transport.paused == 1);
        CHECK(NativeAnim_Command("anim\tspeed\t2", reply, sizeof(reply)) == 0);
        CHECK(near(native_anim_transport.speed, 2.0f));
        CHECK(NativeAnim_Command("  anim\tclip\tauto ", reply, sizeof(reply)) == 0);
        CHECK(native_anim_transport.forced_clip == NULL);

        /* An err reply leaves the state unchanged (compare "anim get" before and after). */
        NativeAnim_TransportInit();
        CHECK(NativeAnim_Command("anim clip Sword_Attack", reply, sizeof(reply)) == 0);
        CHECK(NativeAnim_Command("anim speed 2.5", reply, sizeof(reply)) == 0);
        CHECK(NativeAnim_Command("anim phase 0.5", reply, sizeof(reply)) == 0);
        CHECK(NativeAnim_Command("anim frame 10", reply, sizeof(reply)) == 0);
        CHECK(NativeAnim_Command("anim pause", reply, sizeof(reply)) == 0);
        CHECK(NativeAnim_Command("anim get", before, sizeof(before)) == 0);
        CHECK(NativeAnim_Command("anim speed nan", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim phase abc", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim frame 1.5", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim frame 99999999999", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim bogus", reply, sizeof(reply)) == -1);
        CHECK(NativeAnim_Command("anim get", after, sizeof(after)) == 0);
        CHECK(strcmp(before, after) == 0);
        NativeAnim_TransportInit();
    }

        /* Scrub parity: active phase matches inactive frame (differential test) */
        {
            const float phases[] = {0.0f, 0.1f, 0.25f, 0.5f, 0.75f, 0.9f, 1.0f};
            const int lengths[] = {5, 10, 47};
            int rows_to_test[2] = {0, 3}; /* 0 non-attack, 3 attack */
            for (size_t pi = 0; pi < sizeof(phases)/sizeof(phases[0]); ++pi) {
                for (size_t li = 0; li < sizeof(lengths)/sizeof(lengths[0]); ++li) {
                    int len = lengths[li];
                    float P = phases[pi];
                    for (size_t ri = 0; ri < sizeof(rows_to_test)/sizeof(rows_to_test[0]); ++ri) {
                        int row = rows_to_test[ri];
                        /* active transport */
                        NativeAnim_TransportInit();
                        NativeAnim_TransportSetActive(1);
                        NativeAnim_TransportSetPhase(P);
                        set_draw(1, 0, row, 3, 0, len);
                        float t_active = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
                        /* inactive transport */
                        NativeAnim_TransportInit();
                        int frame = (int)(P * 16.0f * (float)len + 0.5f);
                        set_draw(1, 0, row, 3, frame, len);
                        float t_inactive = NativeAnim_Choose(&draw, &mesh, NULL, &clip);
                        CHECK(near(t_active, t_inactive));
                    }
                }
            }
        }

        if (failures) {
        fprintf(stderr, "native_anim_test: %d failed\n", failures);
        return 1;
    }
    printf("native_anim_test: ok\n");
    return 0;
}
