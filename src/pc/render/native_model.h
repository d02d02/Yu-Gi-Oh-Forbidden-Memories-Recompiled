#ifndef MEMORIES_PC_NATIVE_MODEL_H
#define MEMORIES_PC_NATIVE_MODEL_H
/* Native model pass (experiment, off unless MEMORIES_NATIVE_MODEL names a file).
 *
 * A monster whose model has a replacement mesh is drawn by the OpenGL picture from that mesh instead of
 * from the game's PS1 packets. The game's logic, animation, packet buffer and save states are untouched:
 *
 *   func_800540B4 (the slot draw) calls BeginSlot / Part / EndSlot while it sorts the slot. Part reads the
 *   part's GTE matrices (the game has just set them with GsSetLsMatrix), EndSlot closes the draw and
 *   NativeModel_Link puts a one-word marker packet (GP0 command 0, a no-op for every GPU) into the
 *   ordering table, so the mesh is drawn where the model sorts, in the order of the frame.
 *   DrawOTag takes the frame's draws (NativeModel_Take), the replay gets them with the frame
 *   (SoftGpu recorder `native`), and gl_picture.c draws the mesh when its marker comes by.
 *
 * The mesh file is what tools/hd-models/hmd_export.py writes (model.hdm): vertices in the parts' local
 * space, one triangle per three vertices, so the same GTE matrices pose it. */
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

typedef struct NativeDraw {
    int32_t id;     /* running number; its low 8 bits are in the marker (the replay keeps the last 16) */
    int32_t model;  /* the slot's model id */
    int32_t ofx, ofy; /* GTE screen offset (16.16) */
    int32_t h;      /* GTE projection distance */
    int32_t bk[3];  /* GTE background (ambient) colour, 1.0 = 0x1000 */
    uint32_t tint;  /* the polygons' base colour the slot is drawn with (0x80 = neutral), r in the low byte */
    NativePart parts[NATIVE_MAX_PARTS];
} NativeDraw;

typedef struct NativeMesh {
    uint32_t vertices, parts, tex_w, tex_h;
    uint32_t stride; /* words per vertex: 9 (HDM1) or 17 (HDM2: the same, then part B, weight B, pos B[3], normal B[3]) */
    const uint32_t *words; /* per vertex 9 words: f32 pos[3], f32 normal[3], f32 uv[2], u32 part */
    const uint8_t *rgba;   /* tex_w x tex_h */
    uint32_t joint_parts;  /* HDM3: entries in the joint table (0 = none: the game's own part translations are used) */
    const uint32_t *joints; /* per part 16 words: i32 parent (-1 none), f32 J[3] the model's own joint, f32 tb[3] the disc's, f32 Rbi[9] the inverse of the disc's bind rotation */
} NativeMesh;

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
/* Links the marker of the draw EndSlot returned into the slot's ordering table `ot` (a GsOT), at the nearest entry. */
void NativeModel_Link(uint32_t *ot, int draw);

/* DrawOTag: the frame's draws move to the taken set; the flush reads them. */
void NativeModel_Take(void);
const NativeDraw *NativeModel_Taken(size_t *count);

/* The mesh for a model id (the replay), or NULL. */
const NativeMesh *NativeModel_Mesh(int model);
#endif
