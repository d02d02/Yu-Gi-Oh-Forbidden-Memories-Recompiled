/* The native models the mods supply (src/pc/render/native_registry.h), with the mod system stood in for: entries by
 * card and by disc model, a later mod over an earlier one, a model that cannot be read falling back to the one before,
 * a package (model.json) with its PNG textures, clips, strike frames, scale and look, the texture cap and the memory
 * budget, entries left out by a setting or naming files outside the mod, and the test switch over all of them. */
#define _POSIX_C_SOURCE 200809L /* setenv, mkdtemp (scratch.h) */
#include "pc/render/native_registry.h"
#include "pc/mods/json.h"
#include "pc/mods/mods.h"
#include "scratch.h"
#include <assert.h>
#include <png.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#ifdef _WIN32
#include <direct.h>
#endif

static int failures;

#define CHECK(condition)                                                              \
    do {                                                                              \
        if (!(condition)) {                                                           \
            fprintf(stderr, "%s:%d: CHECK(%s) failed\n", __FILE__, __LINE__, #condition); \
            failures++;                                                               \
        }                                                                             \
    } while (0)

static char root[SCRATCH_MAX];

/* --- the mod system ---------------------------------------------------------------------------------------------- */
static struct {
    const char *id;
    const char *manifest;
} mods[2];
static char notes[8192];

void Mods_VisitManifests(void (*visit)(const char *, const char *, const struct JsonValue *, void *), void *context)
{
    size_t i;
    for (i = 0; i < sizeof(mods) / sizeof(mods[0]); i++) {
        char error[200], directory[SCRATCH_MAX + 16];
        JsonDocument *document;
        if (!mods[i].id) continue;
        document = Json_Parse(mods[i].manifest, error, sizeof(error));
        assert(document);
        snprintf(directory, sizeof(directory), "%s/%s", root, mods[i].id);
        visit(mods[i].id, directory, Json_Root(document), context);
        Json_Free(document); /* the registry keeps nothing of the manifest */
    }
}

int Mods_Setting(const char *id, const char *key, int fallback)
{
    if (!strcmp(id, "b") && !strcmp(key, "light_gain")) return 250; /* mod b's player set its light gain to 2.5 */
    return fallback;
}

void Mods_Note(const char *id, const char *format, ...)
{
    size_t at = strlen(notes);
    va_list list;
    snprintf(notes + at, sizeof(notes) - at, "%s: ", id);
    at = strlen(notes);
    va_start(list, format);
    vsnprintf(notes + at, sizeof(notes) - at, format, list);
    va_end(list);
    at = strlen(notes);
    snprintf(notes + at, sizeof(notes) - at, "\n");
}

/* An entry with a "setting" stands for one whose setting is off. */
int Mods_EntryUsed(const char *id, const struct JsonValue *entry, const char *where)
{
    (void)id;
    (void)where;
    return Json_Member(entry, "setting") == NULL;
}

/* --- files ------------------------------------------------------------------------------------------------------- */
static void path_of(char *out, size_t size, const char *relative)
{
    snprintf(out, size, "%s/%s", root, relative);
}

static void make_dir(const char *relative)
{
    char path[SCRATCH_MAX + 64];
    path_of(path, sizeof(path), relative);
#ifdef _WIN32
    assert(!_mkdir(path));
#else
    assert(!mkdir(path, 0777));
#endif
}

static void write_file(const char *relative, const void *data, size_t size)
{
    char path[SCRATCH_MAX + 64];
    FILE *file;
    path_of(path, sizeof(path), relative);
    file = fopen(path, "wb");
    assert(file);
    assert(size == 0 || fwrite(data, size, 1, file) == 1);
    fclose(file);
}

static void write_text(const char *relative, const char *text)
{
    write_file(relative, text, strlen(text));
}

static void put_float(uint32_t *word, float value)
{
    memcpy(word, &value, sizeof(value));
}

/* A one-bone HDM4: three vertices at heights `y` (a 1x1 texture), and the clips named, 2 + 8 i frames each. */
static void write_model(const char *relative, float tag, const char *const *clips, unsigned clip_count)
{
    static uint32_t w[4096];
    static const float y[3] = {-10.0f, 0.0f, 25.0f};
    size_t at = 8, i;
    unsigned c;
    memset(w, 0, sizeof(w));
    memcpy(w, "HDM4", 4);
    w[1] = 3;
    w[2] = 3;
    w[3] = 1;
    w[4] = 1;
    w[5] = 1;
    w[6] = clip_count;
    w[at] = (uint32_t)-1; /* the root */
    put_float(&w[at + 1], 1.0f);
    put_float(&w[at + 6], 1.0f);
    put_float(&w[at + 11], 1.0f);
    at += 16;
    for (i = 0; i < 3; i++, at += 13) {
        put_float(&w[at], tag); /* x tells the models apart */
        put_float(&w[at + 1], y[i]);
        put_float(&w[at + 9], 1.0f);
    }
    for (i = 0; i < 3; i++) w[at++] = (uint32_t)i;
    w[at++] = 0xff808080u; /* the texture */
    for (c = 0; c < clip_count; c++) {
        unsigned frames = 2 + 8 * c, k;
        snprintf((char *)&w[at], 32, "%s", clips[c]);
        w[at + 8] = frames;
        put_float(&w[at + 9], 30.0f);
        at += 12;
        for (k = 0; k < frames; k++, at += 7) put_float(&w[at + 6], 1.0f); /* identity keys */
    }
    assert(at <= sizeof(w) / sizeof(w[0]));
    write_file(relative, w, at * 4);
}

static void write_png(const char *relative, unsigned width, unsigned height, uint8_t value)
{
    char path[SCRATCH_MAX + 64];
    png_image image;
    uint8_t *pixels = (uint8_t *)malloc((size_t)width * height * 4);
    assert(pixels);
    memset(pixels, value, (size_t)width * height * 4);
    memset(&image, 0, sizeof(image));
    image.version = PNG_IMAGE_VERSION;
    image.width = width;
    image.height = height;
    image.format = PNG_FORMAT_RGBA;
    path_of(path, sizeof(path), relative);
    assert(png_image_write_to_file(&image, path, 0, pixels, 0, NULL));
    free(pixels);
}

static void set_env(const char *name, const char *value)
{
#ifdef _WIN32
    assert(!_putenv_s(name, value ? value : ""));
#else
    if (value) assert(!setenv(name, value, 1));
    else assert(!unsetenv(name));
#endif
}

static float tag_of(int id)
{
    const NativeMesh *mesh = NativeRegistry_Mesh(id);
    float x = -1.0f;
    if (mesh) memcpy(&x, mesh->words, sizeof(x));
    return x;
}

/* Floats as the build keeps them (a 32-bit x87 build compares a literal at more precision than a stored float). */
static int near(float a, float b)
{
    float d = a - b;
    return d < 1e-4f && d > -1e-4f;
}

static int noted(const char *text)
{
    return strstr(notes, text) != NULL;
}

/* `--load PATH`: the game's loader on one model (tools/hd-models/tests: a converted package read back), one line. */
static int load_one(const char *path)
{
    const NativeMesh *mesh;
    set_env("MEMORIES_NATIVE_MODEL", path);
    set_env("MEMORIES_NATIVE_MODEL_ID", "363");
    mesh = NativeRegistry_Mesh(NativeRegistry_Find(363, 0));
    if (!mesh) {
        fprintf(stderr, "native_registry_test: %s was not loaded\n", path);
        return 1;
    }
    printf("loaded vertices=%u bones=%u clips=%u texture=%ux%u normal=%ux%u attack=%u idle=%u strikes=%u", mesh->vertices,
           mesh->bones, mesh->clip_count, mesh->tex_w, mesh->tex_h, mesh->normal_w, mesh->normal_h,
           (unsigned)mesh->act_clip[NATIVE_ACT_ATTACK], (unsigned)mesh->act_clip[NATIVE_ACT_IDLE], (unsigned)mesh->strike_count);
    if (mesh->strike_count) printf(" strike0=%u", (unsigned)mesh->strike[0]);
    printf(" ground=%.1f\n", (double)mesh->ground);
    return 0;
}

int main(int argc, char **argv)
{
    static const char *const clips[] = {"Idle", "Swing", "Fall"};
    const NativeMesh *mesh;
    int id;

    if (argc == 3 && !strcmp(argv[1], "--load")) return load_one(argv[2]);

    assert(scratch_dir(root, sizeof(root), "memories-native"));
    set_env("MEMORIES_NATIVE_MODEL", NULL);
    set_env("MEMORIES_NATIVE_SPEC", NULL);
    make_dir("a");
    make_dir("a/pkg");
    make_dir("a/bad");
    make_dir("b");
    write_model("a/a.hdm", 1.0f, clips, 1);
    write_model("a/pkg/m.hdm", 2.0f, clips, 3);
    write_png("a/pkg/base.png", 4, 2, 200);
    write_png("a/pkg/n.png", 8, 8, 128);
    write_png("a/pkg/big.png", 256, 128, 90);
    write_text("a/pkg/model.json",
               "{\"format\": 1, \"model\": \"m.hdm\", \"textures\": {\"base\": \"base.png\", \"normal\": \"n.png\"},"
               " \"clips\": {\"attack\": \"Swing\", \"idle\": \"Idle\", \"dance\": \"Idle\", \"hit\": \"Nope\"},"
               " \"strike\": {\"attack\": [3, 7]}, \"scale\": 150, \"offset\": [10, 0, -5], \"shots\": [{\"act\": \"attack\", \"from\": 5, \"to\": 60, \"yaw\": 40, \"distance\": 80, \"ease\": 8}, {\"act\": \"dance\", \"from\": 0, \"to\": 1}, {\"act\": \"hit\", \"other\": true, \"from\": 0, \"to\": 20, \"yaw\": 999}], \"look\": {\"ambient\": 40}, \"author\": \"t\", \"extra\": 1}");
    write_text("a/pkg/big.json", "{\"model\": \"m.hdm\", \"textures\": {\"base\": \"big.png\"}}");
    write_text("a/pkg/strike.json", "{\"model\": \"m.hdm\", \"clips\": {\"attack\": \"Idle\"}, \"strike\": {\"attack\": [1, 5]}}");
    write_text("a/bad/model.json", "{\"format\": 2, \"model\": \"m.hdm\"}");
    write_model("b/b.hdm", 3.0f, clips, 2);
    write_text("b/broken.hdm", "HDM4 is not enough");
    mods[0].id = "a";
    mods[0].manifest =
        "{\"native_models\": [{\"model\": 363, \"file\": \"a.hdm\"}, {\"cards\": [1, 2], \"package\": \"pkg/model.json\"},"
        " {\"card\": 5, \"package\": \"../b/b.hdm\"}, {\"card\": 6, \"file\": \"missing.hdm\"},"
        " {\"card\": 7, \"package\": \"bad/model.json\"}, {\"card\": 8, \"package\": \"pkg/big.json\"},"
        " {\"card\": 10, \"package\": \"pkg/strike.json\"}, {\"file\": \"a.hdm\"}, {\"cards\": [0], \"file\": \"a.hdm\"}]}";
    mods[1].id = "b";
    mods[1].manifest = "{\"native_models\": [{\"cards\": [2], \"file\": \"b.hdm\"}, {\"card\": 1, \"file\": \"broken.hdm\"},"
                       " {\"card\": 9, \"file\": \"b.hdm\", \"setting\": \"off\"}]}";
    set_env("MEMORIES_NATIVE_TEXTURE_MAX", "64");
    NativeRegistry_Read();
    /* The manifests: what cannot be used is said beside its mod, and nothing is read yet. */
    CHECK(noted("a: native_models[2]: ../b/b.hdm is not a file inside the mod"));
    CHECK(noted("a: native_models[7]: names no card"));
    CHECK(noted("a: native_models[8]: cards: a card is a card id"));
    CHECK(NativeRegistry_Bytes() == 0);

    /* By disc model (card unknown or the entry has no cards): the plain file, with the defaults. */
    id = NativeRegistry_Find(363, 0);
    mesh = NativeRegistry_Mesh(id);
    CHECK(id >= 0 && mesh && near(tag_of(id), 1.0f) && mesh->tex_w == 1 && near(mesh->ground, 25.0f) && near(mesh->scale, 0.0f));
    CHECK(mesh && near(mesh->tune.ambient, 0.2f) && near(mesh->tune.camera_near, 1000.0f) && near(mesh->tune.normal_strength, 1.8f));
    CHECK(mesh && !mesh->normal_rgba && !mesh->mr_rgba && !mesh->act_clip[NATIVE_ACT_ATTACK]);
    CHECK(NativeRegistry_Find(363, 364) == id); /* an entry without cards stands for its disc model whatever the card */
    CHECK(NativeRegistry_Find(-1, 1) < 0 && NativeRegistry_Find(100, 0) < 0);
    CHECK(strcmp(NativeRegistry_Name(id), "a: native_models[0]") == 0);

    /* Card 1: mod b's is later but cannot be read, so mod a's package is drawn. */
    id = NativeRegistry_Find(0, 1);
    mesh = NativeRegistry_Mesh(id);
    CHECK(noted("b: native_models[1]:") && noted("broken.hdm is not a usable HDM4 model"));
    CHECK(mesh && near(tag_of(id), 2.0f));
    if (mesh) {
        CHECK(mesh->tex_w == 4 && mesh->tex_h == 2 && mesh->rgba[0] == 200); /* the PNG over the file's texture */
        CHECK(mesh->normal_w == 8 && mesh->normal_rgba && mesh->normal_rgba[0] == 128);
        CHECK(mesh->mr_w == 1 && mesh->mr_rgba); /* a flat one beside the normal map, so the lit program runs */
        CHECK(mesh->act_clip[NATIVE_ACT_ATTACK] == 2 && mesh->act_clip[NATIVE_ACT_IDLE] == 1 && !mesh->act_clip[NATIVE_ACT_HIT]);
        CHECK(mesh->strike_count == 2 && mesh->strike[0] == 3 && mesh->strike[1] == 7);
        CHECK(near(mesh->scale, 1.5f) && near(mesh->tune.ambient, 0.4f) && near(mesh->tune.light_gain, 1.0f));
        CHECK(mesh->shot_count == 1 && mesh->shots[0].act == NATIVE_ACT_ATTACK && mesh->shots[0].yaw == 40 &&
              mesh->shots[0].distance == 80 && mesh->shots[0].ease == 8 && !mesh->shots[0].other);
        CHECK(near(mesh->offset[0], 10.0f) && near(mesh->offset[1], 0.0f) && near(mesh->offset[2], -5.0f));
    }
    CHECK(noted("clips: \"dance\" is not an act") && noted("clips.hit: the model has no clip \"Nope\""));
    CHECK(noted("shots[1]: \"act\" is one of") && noted("shots[2]: 0 <= from"));
    CHECK(noted("model.json: \"extra\" is not read") && !noted("\"author\" is not read"));
    CHECK(NativeRegistry_Find(0, 1) == id); /* read once */
    CHECK(NativeRegistry_Find(0, 0) == id); /* the card unknown: disc model 0 is card 1's */

    /* Card 2: both mods have one; the later mod's is drawn, with its player's setting. */
    id = NativeRegistry_Find(1, 2);
    mesh = NativeRegistry_Mesh(id);
    CHECK(mesh && near(tag_of(id), 3.0f) && near(mesh->tune.light_gain, 2.5f));
    CHECK(NativeRegistry_Find(1, 0) == id);

    /* Not drawn: a missing file (noted once, not tried again), a newer format, an entry whose setting is off. */
    notes[0] = 0;
    CHECK(NativeRegistry_Find(5, 6) < 0 && noted("missing.hdm is not a usable HDM4 model"));
    notes[0] = 0;
    CHECK(NativeRegistry_Find(5, 6) < 0 && !noted("missing"));
    CHECK(NativeRegistry_Find(6, 7) < 0 && noted("model.json is format 2"));
    CHECK(NativeRegistry_Find(8, 9) < 0);
    CHECK(NativeRegistry_Find(4, 5) < 0);

    /* The texture cap: 256x128 halved to 64x32. Strike frames outside the attack clip are dropped. */
    id = NativeRegistry_Find(7, 8);
    mesh = NativeRegistry_Mesh(id);
    CHECK(mesh && mesh->tex_w == 64 && mesh->tex_h == 32 && mesh->rgba[0] == 90 && mesh->rgba[3] == 90);
    notes[0] = 0;
    id = NativeRegistry_Find(9, 10);
    mesh = NativeRegistry_Mesh(id);
    CHECK(mesh && mesh->act_clip[NATIVE_ACT_ATTACK] == 1 && mesh->strike_count == 0);
    CHECK(noted("strike.attack: 5 is not a frame of the attack clip (Idle, 2 frames)"));
    CHECK(NativeRegistry_Bytes() > 0);

    /* The memory budget: a texture that would pass it is left out (the model's own is used). */
    NativeRegistry_Reset();
    set_env("MEMORIES_NATIVE_TEXTURE_MAX", NULL);
    set_env("MEMORIES_NATIVE_BUDGET_MB", "16");
    write_png("a/pkg/big.png", 2100, 2100, 90);
    notes[0] = 0;
    id = NativeRegistry_Find(7, 8);
    mesh = NativeRegistry_Mesh(id);
    CHECK(mesh && mesh->tex_w == 1 && noted("textures.base: big.png:") && noted("within the memory budget"));
    CHECK(NativeRegistry_Bytes() < 64 * 1024);
    set_env("MEMORIES_NATIVE_BUDGET_MB", NULL);

    /* The test switch: over every mod's, a package read from it as from a mod, -2 for every model; the environment
     * over the look. */
    NativeRegistry_Reset();
    {
        char path[SCRATCH_MAX + 64];
        path_of(path, sizeof(path), "a/pkg/model.json");
        set_env("MEMORIES_NATIVE_MODEL", path);
        set_env("MEMORIES_NATIVE_MODEL_ID", "-2");
        set_env("MEMORIES_NATIVE_SPEC", "0.5");
    }
    id = NativeRegistry_Find(1, 2);
    mesh = NativeRegistry_Mesh(id);
    CHECK(mesh && near(tag_of(id), 2.0f) && mesh->tex_w == 4 && near(mesh->tune.highlight, 0.5f) && near(mesh->tune.ambient, 0.4f));
    CHECK(NativeRegistry_Find(100, 0) == id && NativeRegistry_Find(-1, 0) < 0);
    set_env("MEMORIES_NATIVE_MODEL_ID", "100");
    NativeRegistry_Reset();
    CHECK(NativeRegistry_Find(100, 0) >= 0 && near(tag_of(NativeRegistry_Find(100, 0)), 2.0f));
    CHECK(near(tag_of(NativeRegistry_Find(1, 2)), 3.0f)); /* other models: the mods' */
    NativeRegistry_Reset();
    CHECK(NativeRegistry_Mesh(0) == NULL && NativeRegistry_Bytes() == 0);

    if (failures) {
        fprintf(stderr, "native_registry_test: %d failed\nnotes:\n%s", failures, notes);
        return 1;
    }
    printf("native_registry_test: ok\n");
    return 0;
}
