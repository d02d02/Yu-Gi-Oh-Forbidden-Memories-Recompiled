/* The HDM4 native model file's checks (src/pc/render/native_format.h): a good file is read as written; a file cut
 * short anywhere, with a word too many, or with any count, parent, joint or index that does not fit is refused
 * with a reason, and the mesh it was to fill is left as it was. */
#include "pc/render/native_format.h"
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

typedef struct {
    uint32_t bones, vertices, indices, tex_w, tex_h, clips, flags, frames;
} Shape;

static const Shape small = {2, 3, 3, 1, 1, 1, 0, 2};

#define CAPACITY 4096
static uint32_t file[CAPACITY];

static uint32_t float_bits(float value)
{
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

/* A model of the shape: bone b's parent is b - 1, every vertex on joint 0, triangles round the vertices, one
 * 1x1 map per flag bit, clips named Clip0.. at 30 fps with identity rotations. Returns its words. */
static size_t make(Shape s)
{
    size_t at = 0, i, k;
    memset(file, 0, sizeof(file));
    memcpy(&file[at++], "HDM4", 4);
    file[at++] = s.vertices;
    file[at++] = s.indices;
    file[at++] = s.bones;
    file[at++] = s.tex_w;
    file[at++] = s.tex_h;
    file[at++] = s.clips;
    file[at++] = s.flags;
    for (i = 0; i < s.bones; i++) {
        file[at] = (uint32_t)((int32_t)i - 1);
        file[at + 1] = file[at + 6] = file[at + 11] = float_bits(1.0f); /* identity inverse bind */
        at += 16;
    }
    for (i = 0; i < s.vertices; i++) {
        file[at + 9] = float_bits(1.0f); /* weight 1 on joint 0 */
        at += 13;
    }
    for (i = 0; i < s.indices; i++) file[at++] = (uint32_t)(i % s.vertices);
    at += (size_t)s.tex_w * s.tex_h;
    for (k = 1; k <= 2; k++) {
        if (!(s.flags & k)) continue;
        file[at++] = 1;
        file[at++] = 1;
        at += 1;
    }
    for (k = 0; k < s.clips; k++) {
        char name[32];
        memset(name, 0, sizeof(name));
        snprintf(name, sizeof(name), "Clip%u", (unsigned)k);
        memcpy(&file[at], name, sizeof(name));
        file[at + 8] = s.frames;
        file[at + 9] = float_bits(30.0f);
        at += 12;
        for (i = 0; i < (size_t)s.frames * s.bones; i++) {
            file[at + 6] = float_bits(1.0f);
            at += 7;
        }
    }
    return at;
}

/* Parses the first `words` words of `file`; on refusal checks that a reason was given and `out` is untouched. */
static int parse(size_t words, NativeMesh *out)
{
    NativeMesh before;
    char why[200] = "";
    int ok;
    memset(out, 0x5a, sizeof(*out));
    memcpy(&before, out, sizeof(before));
    ok = NativeFormat_ParseHdm4(file, words * 4, out, why, sizeof(why));
    if (!ok) {
        CHECK(why[0] != 0);
        CHECK(memcmp(&before, out, sizeof(before)) == 0);
    }
    return ok;
}

/* The same, from a heap copy exactly `words` long, so that a read past the end is caught by a sanitizer. */
static int parse_exact(size_t words)
{
    NativeMesh mesh;
    uint32_t *copy = (uint32_t *)malloc(words ? words * 4 : 1);
    char why[200] = "";
    int ok;
    if (!copy) return 0;
    memcpy(copy, file, words * 4);
    ok = NativeFormat_ParseHdm4(copy, words * 4, &mesh, why, sizeof(why));
    if (!ok) CHECK(why[0] != 0);
    free(copy);
    return ok;
}

static int refused(Shape s, size_t word, uint32_t value)
{
    NativeMesh mesh;
    size_t words = make(s);
    file[word] = value;
    return !parse(words, &mesh) && !parse_exact(words);
}

int main(void)
{
    NativeMesh mesh;
    size_t words, cut;
    Shape s;

    /* Good files. */
    words = make(small);
    CHECK(parse(words, &mesh));
    CHECK(mesh.vertices == 3 && mesh.bones == 2 && mesh.index_count == 3 && mesh.clip_count == 1);
    CHECK(mesh.tex_w == 1 && mesh.tex_h == 1 && mesh.stride == 13);
    CHECK(strcmp(mesh.clips[0].name, "Clip0") == 0 && mesh.clips[0].frames == 2 && mesh.clips[0].fps == 30.0f);
    CHECK(mesh.normal_rgba == NULL && mesh.mr_rgba == NULL);
    CHECK(mesh.bone_table == file + 8 && mesh.words == file + 8 + 2 * 16);
    s = small;
    s.flags = 3;
    s.clips = 3;
    words = make(s);
    CHECK(parse(words, &mesh));
    CHECK(mesh.normal_w == 1 && mesh.mr_h == 1 && mesh.normal_rgba && mesh.mr_rgba && mesh.clip_count == 3);
    CHECK(strcmp(mesh.clips[2].name, "Clip2") == 0);

    /* Cut short anywhere, one word too many, not whole words, no NULL. */
    words = make(s);
    CHECK(parse_exact(words));
    for (cut = 1; cut <= words; cut++) CHECK(!parse(words - cut, &mesh) && !parse_exact(words - cut));
    CHECK(!parse(words + 1, &mesh));
    CHECK(!NativeFormat_ParseHdm4(file, words * 4 - 1, &mesh, NULL, 0));
    CHECK(!NativeFormat_ParseHdm4(NULL, 64, &mesh, NULL, 0));

    /* Header counts. */
    CHECK(refused(small, 0, 0x334d4448u));           /* "HDM3" */
    CHECK(refused(small, 3, 0));                     /* no bones */
    CHECK(refused(small, 3, NATIVE_MAX_BONES + 1));  /* too many */
    CHECK(refused(small, 1, 0));                     /* no vertices */
    CHECK(refused(small, 2, 4));                     /* not triangles */
    CHECK(refused(small, 6, NATIVE_MAX_CLIPS + 1));  /* too many clips */
    CHECK(refused(small, 7, 4));                     /* unknown flag */
    CHECK(refused(small, 4, 0xffffffffu));           /* a texture side that would wrap the size round */
    CHECK(refused(small, 4, NATIVE_FORMAT_MAX_SIDE + 1));
    CHECK(refused(small, 1, 0x40000000u));           /* vertices that would wrap */

    /* The skeleton: parents in range, not itself, no cycle. */
    CHECK(refused(small, 8 + 16, 2));                /* bone 1's parent: no bone 2 */
    CHECK(refused(small, 8 + 16, (uint32_t)-2));
    CHECK(refused(small, 8 + 16, 1));                /* its own parent */
    words = make(small);
    file[8] = 1;                                     /* bone 0 under bone 1, bone 1 under bone 0 */
    CHECK(!parse(words, &mesh));

    /* Vertices and triangles. */
    CHECK(refused(small, 8 + 32 + 8, 2));            /* vertex 0 on joint 2 of 2 */
    CHECK(refused(small, 8 + 32 + 8, 2u << 24));     /* its fourth joint */
    CHECK(refused(small, 8 + 32 + 39, 3));           /* a corner on vertex 3 of 3 */

    /* Clips: frames and frame rate. */
    s = small;
    s.frames = 0;
    words = make(s);
    CHECK(!parse(words, &mesh));
    words = make(small);
    file[8 + 32 + 39 + 3 + 1 + 9] = float_bits(0.0f);
    CHECK(!parse(words, &mesh));
    file[8 + 32 + 39 + 3 + 1 + 9] = 0x7fc00000u;     /* NaN */
    CHECK(!parse(words, &mesh));

    /* A map with a bad side. */
    s = small;
    s.flags = 1;
    CHECK(refused(s, 8 + 32 + 39 + 3 + 1, 0));

    if (failures) {
        fprintf(stderr, "native_format_test: %d failed\n", failures);
        return 1;
    }
    printf("native_format_test: ok\n");
    return 0;
}
