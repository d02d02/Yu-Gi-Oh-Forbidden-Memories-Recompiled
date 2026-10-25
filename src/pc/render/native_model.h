#ifndef MEMORIES_PC_NATIVE_MODEL_H
#define MEMORIES_PC_NATIVE_MODEL_H
/* Native model pass: a monster whose card (or disc model) has a native model (native_models in a mod's manifest,
 * native_registry.h, notes/native-models.md) is drawn by the OpenGL picture from that model instead of from the
 * game's PS1 packets. The game's logic, animation, packet buffer and save states are untouched:
 *
 *   func_800540B4 (the slot draw) calls BeginSlot / Part / SlotInfo / EndSlot while it sorts the slot. Part reads the
 *   part's GTE matrices (the lights come from them), SlotInfo the slot's animation row, clock and body root, EndSlot
 *   closes the draw and NativeModel_Link puts a one-word marker packet (GP0 command 0, a no-op for every GPU) into the
 *   ordering table, so the model is drawn where the slot sorts, in the order of the frame.
 *   DrawOTag takes the frame's draws (NativeModel_Take), the replay gets them with the frame (SoftGpu recorder
 *   `native`), and gl_picture.c draws the model when its marker comes by: its own clip (native_anim.c), skinned on the
 *   GPU, with a depth buffer of its own, laid over the picture.
 *
 * The model is an HDM4 file (native_format.h), alone or in a package with its textures and choices (model.json);
 * tools/hd-models/native_convert.py makes both from a rigged glTF. */
#include <stddef.h>
#include <stdint.h>

#define NATIVE_MAX_DRAWS 16 /* a frame's native draws: ten monsters on the field and two on the attack's big cards fit */
#define NATIVE_MAX_PARTS 64
#define NATIVE_MARKER 0x00A5C000u /* | draw id & 0xFF: GP0 command 0, ignored by every GPU */
#define NATIVE_RING 32      /* the draws the replay keeps: two frames' worth */

/* Where a slot is drawn (NativeInstance.context). */
enum {
    NATIVE_CONTEXT_ARENA = 0, /* the game's own: the arena battle (and the Library's model view) */
    NATIVE_CONTEXT_FIELD,     /* a code mod's monster on the duel field (3D Monsters) */
    NATIVE_CONTEXT_BIG_CARD,  /* a code mod's monster on the battle presentation's big cards */
    NATIVE_CONTEXT_MEASURE,   /* a code mod measuring the disc model's packets: nothing is captured or left out */
    NATIVE_CONTEXT_COUNT
};

/* What a code mod says about the camera shots (NativeModel_FieldShot, native_cinematic.h): the two fighters' cards and what they
 * are playing, and, filled by the call, the camera move: degrees of yaw and pitch, the distance as a factor, units of height. */
typedef struct NativeFieldShot {
    int32_t size;
    int32_t card[2];       /* the attacker's and the defender's card (0: none) */
    int32_t row[2];        /* the disc animation row each plays (0: none) */
    int32_t attack_row[2]; /* the row each card attacks with */
    int32_t frame[2];      /* the frame of that row each is at (-1: not begun) */
    float yaw, pitch, distance, height; /* out; 0, 0, 1, 0 when no shot applies */
} NativeFieldShot;

/* What a code mod says about the slot it is about to draw with func_800540B4 (NativeModel_SetInstance). It applies
 * to that one draw. `size` is sizeof(NativeInstance) in the caller's build: a field past it is taken as 0, so a mod
 * built against this layout keeps working when fields are added at the end. */
typedef struct NativeInstance {
    int32_t size;
    int32_t context;       /* NATIVE_CONTEXT_* */
    int32_t key;           /* the caller's own name for the monster (a zone, a side, 0 to 65535): its animation state goes with it */
    int32_t card;          /* the card shown (0: unknown) */
    int32_t fade;          /* 0 opaque .. 255 gone, as SOFT_GPU_FADE */
    int32_t contact_frame; /* the disc frame of the attack row where its blow lands, -1 unknown */
} NativeInstance;

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
    /* Filled by the capture (NativeModel_SlotInfo), not by the slot draw: */
    int32_t context;                 /* NATIVE_CONTEXT_* */
    int32_t key;                     /* the animation state's owner: the slot in the arena, context << 16 | the mod's key else */
    int32_t card;                    /* the card shown (0: unknown) */
    int32_t fade;                    /* 0 opaque .. 255 gone */
    int32_t contact_frame;           /* see NativeInstance, -1 unknown */
} NativeSlotInfo;

typedef struct NativeDraw {
    int32_t id;     /* running number; its low 8 bits are in the marker (the replay keeps the last NATIVE_RING) */
    int32_t model;  /* the slot's model id */
    int32_t mesh_id; /* the native model chosen for it (NativeModel_MeshById) */
    int32_t ofx, ofy; /* GTE screen offset (16.16) */
    int32_t h;      /* GTE projection distance */
    int32_t bk[3];  /* GTE background (ambient) colour, 1.0 = 0x1000 */
    uint32_t tint;  /* the polygons' base colour the slot is drawn with (0x80 = neutral), r in the low byte */
    NativePart parts[NATIVE_MAX_PARTS];
    NativeSlotInfo info;
} NativeDraw;

/* A camera shot (native_cinematic.h): while `act` plays (row frames `from` to `to`; of the other monster of the battle when
 * `other`), the camera is turned `yaw` degrees about its look-at point, raised `pitch` degrees and `height` units, and its
 * distance made `distance` percent, easing in and out over `ease` frames. */
#define NATIVE_MAX_SHOTS 8
typedef struct NativeShot {
    uint8_t act, other;
    int16_t from, to, yaw, pitch, distance, height, ease;
} NativeShot;

/* A time map (Studio S6): points of {clip frame, row frame}, both rising; while `act` plays, the clip's frame is the piecewise
 * linear map of the disc row's frame (NativeAnim_TimeMapClip), in place of the automatic strike/BLS warps. */
#define NATIVE_MAX_TIMEMAPS 8
#define NATIVE_MAX_TIMEMAP_POINTS 16
typedef struct NativeTimeMap {
    uint8_t act, count;
    float points[NATIVE_MAX_TIMEMAP_POINTS][2];
} NativeTimeMap;

/* HDM4: a clip = local translation + rotation (disc space) of every bone, baked at `fps`. */
#define NATIVE_MAX_CLIPS 16
#define NATIVE_MAX_BONES 128
typedef struct NativeClip {
    char name[32];
    uint32_t frames;
    float fps;
    const float *data; /* frames x bones x 7: t[3], q[4] (xyzw) */
} NativeClip;

/* What a slot is doing, from its disc row: the rows the arena plays (func_8004EB00, model_control.c) and 3D Monsters
 * plays on the field. 0 and 1 idle (1: back from a hit), 2 enter, the attack row field_DFE + 3 (3, or 4 with the second
 * guardian star), 5 hit and standing, 6 destroyed, 7 the winner's pose, 8 guard (NativeAnim_Act). */
typedef enum NativeAct {
    NATIVE_ACT_IDLE,
    NATIVE_ACT_ENTER,
    NATIVE_ACT_ATTACK,
    NATIVE_ACT_HIT,
    NATIVE_ACT_DESTROYED,
    NATIVE_ACT_WIN,
    NATIVE_ACT_GUARD,
    NATIVE_ACT_COUNT
} NativeAct;

/* How a native model is lit and framed: defaults, under its mod's settings, under its package's "look", under the
 * environment (MEMORIES_ARENA_CAMERA_*, MEMORIES_NATIVE_*: one run). Made when the model is read (native_registry.c). */
typedef struct NativeTune {
    float camera_near, camera_keep, camera_scale; /* arena camera: close shots under `near` are pushed out, `keep` of the way in stays; overall scale */
    float ambient, light_gain;                    /* added to the game's ambient light; the game's lights multiplied */
    float normal_strength, highlight, flip_green; /* PBR-lite: normal map strength, specular highlight strength, flip the normal map's green (0/1) */
} NativeTune;
#define NATIVE_MAX_STRIKES 4

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
    /* From the package (model.json, native_registry.c); all 0 = the defaults, so a mesh made by hand needs none: */
    uint8_t act_clip[NATIVE_ACT_COUNT]; /* the clip an act plays, + 1 (0: the default names, NativeAnim_Choose) */
    uint8_t strike_count;               /* the attack clip's frames where its blows land (NATIVE_MAX_STRIKES at most) */
    uint16_t strike[NATIVE_MAX_STRIKES];
    float scale;                        /* drawn this many times as large, standing where it stood (0: 1) */
    float ground;                       /* the soles' height in the model's space (y down: its largest y), for `scale` */
    NativeShot shots[NATIVE_MAX_SHOTS]; /* from the package ("shots") */
    uint8_t shot_count;
    NativeTimeMap timemaps[NATIVE_MAX_TIMEMAPS]; /* from the package ("timemaps"): row frame -> clip frame, per act */
    uint8_t timemap_count;
    float offset[3];                    /* moved this far in the model's own space (x right, y down, z forward), before `scale` */
    NativeTune tune;
} NativeMesh;

extern unsigned NativeModel_Stats[8];
/* 1 while the slot being sorted has a replacement mesh the GL pass will draw: the drivers then leave the model's
 * PS1 packets unlinked (they still run, so the packet cursor and the colour cache stay as they were). */
extern volatile int NativeModel_Suppress;
/* Set by the GL pass: it can draw native models now (a picture of 2x or more, programs made). */
extern volatile int NativeModel_GlReady;
/* While NativeModel_Suppress: the nearest ordering-table entry the slot's packets would have gone into (the drivers
 * keep the least index; ~0u: none yet). NativeModel_Link puts the marker there, so the model sorts at its own depth. */
extern unsigned NativeModel_Nearest;
/* A code mod, before func_800540B4: what the next slot draw is (NULL: the game's own, the default). Used once. */
void NativeModel_SetInstance(const NativeInstance *instance);
/* The battle code, as the arena starts: the cards of its slots 0 and 1 (0, 0 when it ends). */
void NativeModel_SetBattleCards(int card0, int card1);
/* The slot draw (game side): the model it draws (< 0: not a duel model) and the slot (0 and 1: the battle's). */
void NativeModel_BeginSlot(int model, int slot);
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

/* The mesh a captured draw chose (NativeDraw.mesh_id; the replay), or NULL. */
const NativeMesh *NativeModel_MeshById(int id);
/* 1 when a slot drawing `model` for `card` (0: unknown) now is drawn by the native pass (a model for it, the pass
 * ready, a picture of 2x or more). */
int NativeModel_WillDraw(int model, int card);
/* Studio compare (control command "native show disc|native"): while on, WillDraw says no, so the disc's own monster is drawn. */
void NativeModel_ShowDisc(int on);
int NativeModel_ShowingDisc(void);
/* The arena camera's eye-to-look-at factor for a frame whose battle slots draw model0 and model1 (-1: none): 1 (the
 * game's camera) unless one of them is drawn natively. */
float NativeModel_ArenaCameraFactor(int model0, int model1, float dx, float dy, float dz);
/* The arena camera of a shot of a drawn native model's package (native_cinematic.h): `eye` moved about `look` while the
 * acts of the battle's two monsters match one; 0 (and `eye` as it was) when none does. */
int NativeModel_ArenaShot(int model0, int model1, const float look[3], float eye[3]);
/* The same for a code mod's camera (the field fight): the strongest shot of the two fighters' packages that matches what they
 * play. Returns 1 when one applies (the camera move is in the structure), else 0. */
int NativeModel_FieldShot(NativeFieldShot *shot);
#endif
