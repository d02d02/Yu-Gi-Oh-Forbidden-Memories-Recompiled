/* The HDM4 native model file, checked (native_format.h). */
#include "pc/render/native_format.h"
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#define HEADER_WORDS 8u
#define BONE_WORDS 16u
#define VERTEX_WORDS 13u
#define CLIP_HEADER_WORDS 12u
#define CLIP_KEY_FLOATS 7u /* per bone and frame: translation[3], rotation quaternion[4] */
#define KNOWN_FLAGS 3u     /* bit 0 normal map, bit 1 metal/roughness map */

static int fail(char *why, size_t why_size, const char *format, ...)
{
    if (why && why_size) {
        va_list list;
        va_start(list, format);
        vsnprintf(why, why_size, format, list);
        va_end(list);
    }
    return 0;
}

/* Moves the cursor past `count` words, or says there are not that many left (the cursor never passes `words`). */
static int take(uint64_t *at, uint64_t count, uint64_t words)
{
    if (*at > words || count > words - *at) return 0;
    *at += count;
    return 1;
}

static int side_ok(uint32_t side)
{
    return side >= 1 && side <= NATIVE_FORMAT_MAX_SIDE;
}

int NativeFormat_ParseHdm4(const uint32_t *w, size_t bytes, NativeMesh *out, char *why, size_t why_size)
{
    NativeMesh m;
    uint64_t words, at = HEADER_WORDS, k;
    uint32_t b, flags, map;
    if (!w || bytes < HEADER_WORDS * 4u || bytes % 4u) return fail(why, why_size, "too short, or not whole 4-byte words");
    if (memcmp(w, "HDM4", 4) != 0) return fail(why, why_size, "not an HDM4 file");
    words = (uint64_t)bytes / 4u;
    memset(&m, 0, sizeof(m));
    m.vertices = w[1];
    m.index_count = w[2];
    m.bones = w[3];
    m.tex_w = w[4];
    m.tex_h = w[5];
    m.clip_count = w[6];
    flags = w[7];
    m.stride = VERTEX_WORDS;
    if (m.bones < 1 || m.bones > NATIVE_MAX_BONES)
        return fail(why, why_size, "%u bones (it takes 1 to %d)", m.bones, NATIVE_MAX_BONES);
    if (m.vertices < 1) return fail(why, why_size, "no vertices");
    if (m.index_count < 3 || m.index_count % 3)
        return fail(why, why_size, "%u indices (triangles: a multiple of 3)", m.index_count);
    if (m.clip_count > NATIVE_MAX_CLIPS)
        return fail(why, why_size, "%u animation clips (at most %d)", m.clip_count, NATIVE_MAX_CLIPS);
    if (flags & ~KNOWN_FLAGS) return fail(why, why_size, "unknown flags 0x%x", flags);
    if (!side_ok(m.tex_w) || !side_ok(m.tex_h))
        return fail(why, why_size, "texture %ux%u (each side 1 to %u)", m.tex_w, m.tex_h, NATIVE_FORMAT_MAX_SIDE);

    m.bone_table = w + at;
    if (!take(&at, (uint64_t)m.bones * BONE_WORDS, words)) return fail(why, why_size, "cut short in the bones");
    m.words = w + at;
    if (!take(&at, (uint64_t)m.vertices * VERTEX_WORDS, words)) return fail(why, why_size, "cut short in the vertices");
    m.indices = w + at;
    if (!take(&at, m.index_count, words)) return fail(why, why_size, "cut short in the triangles");
    m.rgba = (const uint8_t *)(w + at);
    if (!take(&at, (uint64_t)m.tex_w * m.tex_h, words)) return fail(why, why_size, "cut short in the texture");
    for (map = 1; map <= 2; map <<= 1) {
        uint32_t mw, mh;
        const char *name = map == 1 ? "normal map" : "metal/roughness map";
        if (!(flags & map)) continue;
        if (!take(&at, 2, words)) return fail(why, why_size, "cut short before the %s", name);
        mw = w[at - 2];
        mh = w[at - 1];
        if (!side_ok(mw) || !side_ok(mh))
            return fail(why, why_size, "%s %ux%u (each side 1 to %u)", name, mw, mh, NATIVE_FORMAT_MAX_SIDE);
        if (map == 1) {
            m.normal_w = mw;
            m.normal_h = mh;
            m.normal_rgba = (const uint8_t *)(w + at);
        } else {
            m.mr_w = mw;
            m.mr_h = mh;
            m.mr_rgba = (const uint8_t *)(w + at);
        }
        if (!take(&at, (uint64_t)mw * mh, words)) return fail(why, why_size, "cut short in the %s", name);
    }
    for (k = 0; k < m.clip_count; k++) {
        const uint32_t *c = w + at;
        NativeClip *clip = &m.clips[k];
        if (!take(&at, CLIP_HEADER_WORDS, words)) return fail(why, why_size, "cut short in clip %u", (unsigned)k);
        memcpy(clip->name, c, sizeof(clip->name));
        clip->name[sizeof(clip->name) - 1] = 0;
        clip->frames = c[8];
        memcpy(&clip->fps, c + 9, sizeof(clip->fps));
        if (clip->frames < 1) return fail(why, why_size, "clip %s has no frames", clip->name);
        if (!(clip->fps > 0.0f && clip->fps <= 240.0f)) /* NaN fails too */
            return fail(why, why_size, "clip %s: frame rate out of range", clip->name);
        clip->data = (const float *)(w + at);
        if (!take(&at, (uint64_t)clip->frames * m.bones * CLIP_KEY_FLOATS, words))
            return fail(why, why_size, "cut short in clip %s", clip->name);
    }
    if (at != words)
        return fail(why, why_size, "%u words left over after the last clip", (unsigned)(words - at));

    /* The skeleton: every parent a bone of the file, and walking up from any bone ends at a root. */
    for (b = 0; b < m.bones; b++) {
        int32_t parent = (int32_t)m.bone_table[(size_t)b * BONE_WORDS];
        if (parent < -1 || parent >= (int32_t)m.bones || parent == (int32_t)b)
            return fail(why, why_size, "bone %u has parent %d", b, parent);
    }
    for (b = 0; b < m.bones; b++) {
        int32_t up = (int32_t)b;
        uint32_t steps = 0;
        while (up >= 0) {
            if (++steps > m.bones) return fail(why, why_size, "bone %u is its own ancestor", b);
            up = (int32_t)m.bone_table[(size_t)up * BONE_WORDS];
        }
    }
    for (k = 0; k < m.vertices; k++) {
        uint32_t joints = m.words[k * VERTEX_WORDS + 8], j;
        for (j = 0; j < 4; j++)
            if (((joints >> (8 * j)) & 0xffu) >= m.bones)
                return fail(why, why_size, "vertex %u names joint %u of %u", (unsigned)k, (joints >> (8 * j)) & 0xffu, m.bones);
    }
    for (k = 0; k < m.index_count; k++)
        if (m.indices[k] >= m.vertices)
            return fail(why, why_size, "triangle corner %u is vertex %u of %u", (unsigned)k, m.indices[k], m.vertices);
    *out = m;
    return 1;
}
