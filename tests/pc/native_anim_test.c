/* The native model's animation without OpenGL (src/pc/render/native_anim.h): the disc row picks the clip (the attack is
 * row field_DFE + 3), the attack row of Black Luster Soldier is time-warped onto the game's contact frames, the clip is
 * posed by forward kinematics into the skinning rows, and a row change cross-fades over NATIVE_FADE draws; a package's
 * clip choices and scale (native_registry.h) are honoured. */
#include "pc/render/native_anim.h"
#include <math.h>
#include <stdio.h>
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

    if (failures) {
        fprintf(stderr, "native_anim_test: %d failed\n", failures);
        return 1;
    }
    printf("native_anim_test: ok\n");
    return 0;
}
