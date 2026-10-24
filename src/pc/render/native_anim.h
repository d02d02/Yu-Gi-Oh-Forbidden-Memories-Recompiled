#ifndef MEMORIES_PC_NATIVE_ANIM_H
#define MEMORIES_PC_NATIVE_ANIM_H
/* The native model's animation, without OpenGL (native_model.h): which clip a draw plays and where in it (the director),
 * then the clip sampled, cross-faded on a row change and posed by forward kinematics into the rows the skinning shader
 * reads. gl_picture.c uploads the rows and draws; everything here is plain C, so it is tested without a picture.
 *
 * The rows (4 RGBA32F texels each, NATIVE_SKIN_ROWS of them): rows 0-127 = bone j's 3x4 matrix, view <- model space
 * = (root view) x (bone world) x (inverse bind), texels 0-2 = matrix rows with the translation in .w; row 128 = (screen
 * offset x, y incl. the picture offset, H, scale), (tint rgb / 128, lit), (ambient rgb), (ambient lift, light gain);
 * row 129 = the three light directions in view space; row 130 = the light colour matrix rows. */
#include "pc/render/native_model.h"

#define NATIVE_SKIN_ROWS (NATIVE_MAX_BONES + 3)
#define NATIVE_FADE 6 /* game frames of cross-fade when the disc animation row changes (0.2 s at 30 fps) */

/* The act of a disc row (NativeAct, native_model.h). */
NativeAct NativeAnim_Act(int row, int attack_row);

/* What the picture adds to a draw's own state. */
typedef struct NativeAnimFrame {
    float offset_x, offset_y; /* the drawing offset the GPU adds to every vertex */
    int scale;                /* the picture's scale */
    int lit;                  /* the slot's lights are set (else the tint alone colours it) */
    float ambient, light_gain; /* the mesh's NativeTune */
    int log;                  /* MEMORIES_NATIVE_SKIN_LOG: a pose line every 20 draws */
} NativeAnimFrame;

/* The clip an act plays: the package's choice (NativeMesh.act_clip), else the default name; an act with neither plays
 * the hit's (guard, destroyed) or the idle's (the others), else the first clip; NULL when the mesh has none. */
const NativeClip *NativeAnim_ActClip(const NativeMesh *mesh, NativeAct act);
/* The clip draw `d` plays (`*clip_out`, NULL when the mesh has none) and the time in it, in seconds: over the row's
 * length, the attack time-warped so the package's first strike frame lands on the draw's contact frame when both are
 * known (else Black Luster Soldier's measured warp for its row 3). `forced`: a clip name played on a free clock whatever
 * the game does (MEMORIES_NATIVE_CLIP), or NULL / "". */
float NativeAnim_Choose(const NativeDraw *d, const NativeMesh *mesh, const char *forced, const NativeClip **clip_out);
/* The rows (4 x NATIVE_SKIN_ROWS x 4 floats) for draw `d` at time `t` of `clip`. */
void NativeAnim_Rows(const NativeDraw *d, const NativeMesh *mesh, const NativeClip *clip, float t, const NativeAnimFrame *frame,
                     float *rows);

/* Transport state for live control of the native model preview (E3).
 * Inactive = byte-for-byte identical to the old behaviour. */
typedef struct NativeAnimTransport {
    int active;                 /* 0 = inactive (default), 1 = active */
    const char *forced_clip;    /* clip name to force, or NULL for auto (game-decided) */
    int paused;                 /* 1 = freeze at current anim_frame / free clock */
    float speed;                /* free-clock speed multiplier (0.05..8), default 1 */
    float phase_override;       /* phase (0..1) to scrub to, -1 = none */
    int frame_override;         /* clip frame to jump to, -1 = none */
    int last_anim_frame;        /* held anim_frame when paused (row-driven) */
    int last_anim_length;       /* row length of the last chosen clip, for reporting */
    float last_phase;           /* phase the last chosen clip used, for reporting */
    unsigned last_id;           /* held draw id when paused (free clock) */
} NativeAnimTransport;

/* Global transport state (process-wide, single preview). */
extern NativeAnimTransport native_anim_transport;

/* Initialise transport to inactive defaults. */
void NativeAnim_TransportInit(void);

/* Setters (clamp/validate). */
void NativeAnim_TransportSetActive(int active);
void NativeAnim_TransportSetForcedClip(const char *name);  /* NULL or "" = auto */
void NativeAnim_TransportSetPaused(int paused);
void NativeAnim_TransportSetSpeed(float speed);            /* 0.05..8 */
void NativeAnim_TransportSetPhase(float phase);            /* 0..1, -1 = clear */
void NativeAnim_TransportSetFrame(int frame);              /* >=0, -1 = clear */

/* Get a human-readable status line into `reply` (max `n` bytes). */
void NativeAnim_TransportGet(char *reply, size_t n);

/* Parse one "anim ..." command line: "anim clip NAME|auto", "anim pause", "anim resume",
 * "anim speed X", "anim phase P", "anim frame N", "anim get".
 * Returns 0 on success (reply is "ok ..."), -1 on error (reply is "err ..."). */
int NativeAnim_Command(const char *line, char *reply, size_t n);

#endif
