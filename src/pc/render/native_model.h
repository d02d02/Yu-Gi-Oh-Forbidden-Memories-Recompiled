#ifndef MEMORIES_PC_NATIVE_MODEL_H
#define MEMORIES_PC_NATIVE_MODEL_H
/* Native model pass: a monster whose model has an HDM4 replacement (native_models in a mod's manifest,
 * notes/native-models.md) is drawn by the OpenGL picture from that model instead of from the game's PS1 packets. The
 * game's logic, animation, packet buffer and save states are untouched:
 *
 *   func_800540B4 (the slot draw) calls BeginSlot / Part / SlotInfo / EndSlot while it sorts the slot. Part reads the
 *   part's GTE matrices (the lights come from them), SlotInfo the slot's animation row, clock and body root, EndSlot
 *   closes the draw and NativeModel_Link puts a one-word marker packet (GP0 command 0, a no-op for every GPU) into the
 *   ordering table, so the model is drawn where the slot sorts, in the order of the frame.
 *   DrawOTag takes the frame's draws (NativeModel_Take), the replay gets them with the frame (SoftGpu recorder
 *   `native`), and gl_picture.c draws the model when its marker comes by: its own clip (native_anim.c), skinned on the
 *   GPU, with a depth buffer of its own, laid over the picture.
 *
 * The file is HDM4 (native_format.h), which tools/hd-models/rigged_to_hdm4.py writes from a rigged glTF. */
#include <stddef.h>
#include <stdint.h>

#define NATIVE_MAX_DRAWS 8
#define NATIVE_MAX_PARTS 64
#define NATIVE_MARKER 0x00A5C000u /* | draw id & 0xFF: GP0 command 0, ignored by every GPU */
#define NATIVE_RING 16

typedef struct NativePart {
    int16_t rot[9]; /* the GTE rotation matrix, row by row, 1.3.12 fixed point */
    int16_t used;
    int32_t tr[3];  /* the GTE translation */
    int16_t llm[9]; /* the GTE light matrix (lights in the part's local space), 1.3.12 */
    int16_t lcm[9]; /* the GTE light colour matrix (rows: colour channels, columns: lights), 1.3.12 */
} NativePart;

/* What the game says about the slot, read at the end of its draw (the director's inputs: the disc's animation
 * state, the body centre, the root pose). Plain numbers: the GL pass replays them without game memory. */
typedef struct NativeSlotInfo {
    int32_t slot;                    /* 0 = attacker's, 1 = defender's, 2 = other */
    int32_t anim_index, anim_frame, anim_length, anim_speed; /* disc anim row, clock (12.4), row length, speed */
    int32_t row_prev, state;         /* field_E0F, field_E0E */
    int32_t scale[4];                /* field_DB0 */
    int16_t centre[4];               /* field_DD0 */
    uint16_t extents[4];             /* field_DC8 */
    uint8_t tint[8];                 /* field_DC0 */
    int16_t root_rot[9];             /* field_D1C->workm: the body root, local-to-world */
    int32_t root_tr[3];
    int16_t ws_rot[9];               /* GsWSMATRIX: world-to-screen */
    int32_t ws_tr[3];
    int32_t flat_lights[12];         /* field_D70: 3 entries of (3 x s32 direction, colour) */
    int32_t ambient[3];              /* field_DA0 */
    int32_t attack_row;              /* field_DFE + 3: the row this card attacks with (4 with its second guardian star) */
} NativeSlotInfo;

typedef struct NativeDraw {
    int32_t id;     /* running number; its low 8 bits are in the marker (the replay keeps the last 16) */
    int32_t model;  /* the slot's model id */
    int32_t ofx, ofy; /* GTE screen offset (16.16) */
    int32_t h;      /* GTE projection distance */
    int32_t bk[3];  /* GTE background (ambient) colour, 1.0 = 0x1000 */
    uint32_t tint;  /* the polygons' base colour the slot is drawn with (0x80 = neutral), r in the low byte */
    NativePart parts[NATIVE_MAX_PARTS];
    NativeSlotInfo info;
} NativeDraw;

/* HDM4: a clip = local translation + rotation (disc space) of every bone, baked at `fps`. */
#define NATIVE_MAX_CLIPS 16
#define NATIVE_MAX_BONES 128
typedef struct NativeClip {
    char name[32];
    uint32_t frames;
    float fps;
    const float *data; /* frames x bones x 7: t[3], q[4] (xyzw) */
} NativeClip;

typedef struct NativeMesh {
    uint32_t vertices, tex_w, tex_h;
    uint32_t stride;       /* words per vertex: 13 */
    const uint32_t *words; /* per vertex: f32 pos[3], normal[3], uv[2], u32 joints (4 x u8), f32 weights[4] */
    const uint8_t *rgba;   /* tex_w x tex_h */
    /* the model's OWN skeleton and clips */
    uint32_t bones, index_count, clip_count;
    uint32_t normal_w, normal_h, mr_w, mr_h; /* HDM4 PBR-lite maps (0 = none): normal map, metal (B) / roughness (G) */
    const uint8_t *normal_rgba, *mr_rgba;
    const uint32_t *bone_table; /* per bone 16 words: i32 parent, f32 ibm[12] (3x4 row major) */
    const uint32_t *indices;
    NativeClip clips[NATIVE_MAX_CLIPS];
} NativeMesh;

/* The look of big native models: environment (MEMORIES_ARENA_CAMERA_*, MEMORIES_NATIVE_*) over the mod's settings over these defaults
 * (filled when the first slot is drawn, on the game thread; the GL pass only reads). */
typedef struct NativeTune {
    float camera_near, camera_keep, camera_scale; /* arena camera: close shots under `near` are pushed out, `keep` of the way in stays; overall scale */
    float ambient, light_gain;                    /* added to the game's ambient light; the game's lights multiplied */
    float normal_strength, highlight, flip_green; /* PBR-lite: normal map strength, specular highlight strength, flip the normal map's green (0/1) */
} NativeTune;
extern NativeTune NativeModel_Tune;
extern unsigned NativeModel_Stats[8];
/* 1 while the slot being sorted has a replacement mesh the GL pass will draw: the drivers then leave the model's
 * PS1 packets unlinked (they still run, so the packet cursor and the colour cache stay as they were). */
extern volatile int NativeModel_Suppress;
/* Set by the GL pass: it can draw native models now (a picture of 2x or more, programs made). */
extern volatile int NativeModel_GlReady;
/* The slot draw (game side). model < 0: not a duel model. */
void NativeModel_BeginSlot(int model);
void NativeModel_Part(int part);
/* Closes the draw; returns its id + 1 (0: nothing to draw). */
int NativeModel_EndSlot(void);
/* Before EndSlot: the slot's own state (NULL-safe: nothing is being captured). */
void NativeModel_SlotInfo(const NativeSlotInfo *info);
/* Links the marker of the draw EndSlot returned into the slot's ordering table `ot` (a GsOT), at the nearest entry. */
void NativeModel_Link(uint32_t *ot, int draw);

/* DrawOTag: the frame's draws move to the taken set; the flush reads them. */
void NativeModel_Take(void);
const NativeDraw *NativeModel_Taken(size_t *count);

/* The mesh for a model id (the replay), or NULL. */
const NativeMesh *NativeModel_Mesh(int model);
/* 1 when a slot drawing `model` now is drawn by the native pass (a mesh, the pass ready, a picture of 2x or more). */
int NativeModel_WillDraw(int model);
/* The arena camera's eye-to-look-at factor for a frame whose battle slots draw model0 and model1 (-1: none): 1 (the
 * game's camera) unless one of them is drawn natively. */
float NativeModel_ArenaCameraFactor(int model0, int model1, float dx, float dy, float dz);
#endif
