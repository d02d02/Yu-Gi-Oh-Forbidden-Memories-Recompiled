#ifndef MEMORIES_PC_NATIVE_FORMAT_H
#define MEMORIES_PC_NATIVE_FORMAT_H
/* The HDM4 native model file (native_model.h describes the fields it fills), checked whole before anything
 * reads it: a file from a mod is untrusted, and a bad one is a note beside the mod, never a crash.
 *
 *   "HDM4", nverts, nindices, nbones, tex_w, tex_h, nclips, flags (bit 0 normal map, bit 1 metal/roughness map)
 *   bones    nbones x 16 words: i32 parent (-1 = none), f32 inverse bind [12] (3x4 row major), 3 pad
 *   vertices nverts x 13 words: f32 pos[3], normal[3], uv[2], u32 joints (4 x u8), f32 weights[4]
 *   indices  nindices x u32 (triangles)
 *   texture  tex_w x tex_h RGBA8; then per flag bit: u32 w, u32 h, w x h RGBA8
 *   clips    per clip 12 words (char name[32], u32 frames, f32 fps, 2 pad), then frames x nbones x 7 f32
 *
 * Nothing in the file is trusted: every count is checked against what is left before it is used (in 64-bit
 * arithmetic, so a 32-bit game cannot wrap round), every parent is a bone of the file and no bone is its own
 * ancestor, every vertex's joints are bones of the file, every index is a vertex. */
#include "pc/render/native_model.h"
#include <stddef.h>
#include <stdint.h>

#define NATIVE_FORMAT_MAX_SIDE 16384u /* the largest texture side accepted */

/* `data` (4-byte aligned, `bytes` long) -> `out`, whose pointers then point into `data` (keep it). 1 = usable;
 * 0 = malformed, `why` (when not NULL) says what, and `out` is left as it was. */
int NativeFormat_ParseHdm4(const uint32_t *data, size_t bytes, NativeMesh *out, char *why, size_t why_size);
#endif
