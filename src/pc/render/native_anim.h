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

/* The clip an act plays: the package's choice (NativeMesh.act_clip), else the default name, else the first clip; NULL
 * when the mesh has none. */
const NativeClip *NativeAnim_ActClip(const NativeMesh *mesh, NativeAct act);
/* The clip draw `d` plays (`*clip_out`, NULL when the mesh has none) and the time in it, in seconds. `forced`: a clip
 * name played on a free clock whatever the game does (MEMORIES_NATIVE_CLIP), or NULL / "". */
float NativeAnim_Choose(const NativeDraw *d, const NativeMesh *mesh, const char *forced, const NativeClip **clip_out);
/* The rows (4 x NATIVE_SKIN_ROWS x 4 floats) for draw `d` at time `t` of `clip`. */
void NativeAnim_Rows(const NativeDraw *d, const NativeMesh *mesh, const NativeClip *clip, float t, const NativeAnimFrame *frame,
                     float *rows);
#endif
