/* The native models the applied mods supply (native_registry.h). */
#include "pc/render/native_registry.h"
#include "pc/render/native_anim.h"
#include "pc/render/native_format.h"
#include "pc/compat/fs.h"
#include "pc/mods/json.h"
#include "pc/mods/mods.h"
#include "pc/platform/paths.h"
#include <png.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PATH_SIZE 1024

enum { UNREAD, READY, REFUSED };

typedef struct Entry {
    char mod[64];        /* the mod's id; "" for the test switch */
    char name[112];      /* what logs call it: "<mod>: native_models[2]", or the test switch's file */
    char where[40];      /* what the mod's notes call it: "native_models[2]" */
    char path[PATH_SIZE]; /* the package's model.json, or the model file itself */
    int package;         /* `path` is a model.json */
    int test;            /* the test switch (MEMORIES_NATIVE_MODEL) */
    int model;           /* the disc model it stands for; -1: by its cards; -2: every model (the test switch) */
    int cards[NATIVE_REGISTRY_CARDS];
    int card_count;
    int state;
    NativeMesh mesh;
    uint32_t *data;    /* the model file, which the mesh points into */
    uint8_t *maps[3];  /* the package's textures, decoded (NULL: the file's own): base, normal, metal/roughness */
    size_t bytes;      /* what the entry holds */
} Entry;

static Entry entries[NATIVE_REGISTRY_MAX];
static int entry_count;
static int read_done;
static size_t used_bytes;

static const char *const act_names[NATIVE_ACT_COUNT] = {"idle", "enter", "attack", "hit", "destroyed", "win", "guard"};

/* Why an entry is not (quite) what it asked for: beside its mod, or on stderr for the test switch. */
static void note(const Entry *e, const char *format, ...)
{
    char text[512];
    va_list list;
    va_start(list, format);
    vsnprintf(text, sizeof(text), format, list);
    va_end(list);
    if (e->mod[0]) Mods_Note(e->mod, "%s: %s", e->where, text);
    else fprintf(stderr, "memories-pc: native model: %s: %s\n", e->name, text);
}

static size_t budget(void)
{
    const char *text = getenv("MEMORIES_NATIVE_BUDGET_MB");
    long mb = text && *text ? atol(text) : 512;
    if (mb < 16) mb = 16;
    if (mb > 1536) mb = 1536;
    return (size_t)mb * 1024u * 1024u;
}

static uint32_t texture_cap(void)
{
    const char *text = getenv("MEMORIES_NATIVE_TEXTURE_MAX");
    long side = text && *text ? atol(text) : 2048;
    if (side < 64) side = 64;
    if (side > (long)NATIVE_FORMAT_MAX_SIDE) side = (long)NATIVE_FORMAT_MAX_SIDE;
    return (uint32_t)side;
}

/* --- the manifests ----------------------------------------------------------------------------------------------- */
static Entry *new_entry(const char *mod, const char *where)
{
    Entry *e;
    if (entry_count >= NATIVE_REGISTRY_MAX) {
        if (mod) Mods_Note(mod, "%s and after: at most %d native models in all the mods", where, NATIVE_REGISTRY_MAX);
        return NULL;
    }
    e = &entries[entry_count];
    memset(e, 0, sizeof(*e));
    e->model = -1;
    snprintf(e->where, sizeof(e->where), "%s", where);
    if (mod) {
        snprintf(e->mod, sizeof(e->mod), "%s", mod);
        snprintf(e->name, sizeof(e->name), "%.63s: %s", mod, where);
    } else {
        snprintf(e->name, sizeof(e->name), "%s", where);
    }
    return e;
}

static void add_card(Entry *e, const JsonValue *value, const char *what)
{
    long card = Json_TypeOf(value) == JSON_NUMBER ? Json_Number(value, -1) : -1;
    if (card < 1 || card > 65535) {
        note(e, "%s: a card is a card id (1 to 65535)", what);
        return;
    }
    if (e->card_count >= NATIVE_REGISTRY_CARDS) {
        note(e, "%s: at most %d cards per entry (another entry can name more)", what, NATIVE_REGISTRY_CARDS);
        return;
    }
    e->cards[e->card_count++] = (int)card;
}

static void add_from_manifest(const char *id, const char *directory, const JsonValue *item, const char *where)
{
    const char *package = Json_String(Json_Member(item, "package"), "");
    const char *file = Json_String(Json_Member(item, "file"), "");
    const char *named = *package ? package : file;
    const JsonValue *cards = Json_Member(item, "cards"), *card = Json_Member(item, "card"), *value;
    const JsonValue *model = Json_Member(item, "model");
    Entry *e = new_entry(id, where);
    if (!e) return;
    if (Json_TypeOf(item) != JSON_OBJECT || !*named || (*package && *file)) {
        note(e, "needs a \"package\" (a model.json) or a \"file\" (an .hdm model), one of the two");
        return;
    }
    if (!Paths_Contained(named) || snprintf(e->path, sizeof(e->path), "%s/%s", directory, named) >= (int)sizeof(e->path)) {
        note(e, "%s is not a file inside the mod", named);
        return;
    }
    e->package = *package != 0;
    if (card) add_card(e, card, "card");
    if (cards && Json_TypeOf(cards) != JSON_ARRAY) note(e, "\"cards\" is a list of card ids: [364]");
    else
        for (value = Json_At(cards, 0); value; value = Json_Next(value)) add_card(e, value, "cards");
    if (model) {
        long m = Json_TypeOf(model) == JSON_NUMBER ? Json_Number(model, -1) : -1;
        if (m < 0 || m > 65535) note(e, "\"model\" is a disc model id (the card id - 1)");
        else e->model = (int)m;
    }
    if (!e->card_count && e->model < 0) {
        note(e, "names no card (\"cards\": [364]) and no disc model (\"model\": 363)");
        return;
    }
    entry_count++;
}

static void visit(const char *id, const char *directory, const JsonValue *manifest, void *context)
{
    const JsonValue *list = Json_Member(manifest, "native_models"), *item;
    int i = 0;
    (void)context;
    if (!list) return;
    if (Json_TypeOf(list) != JSON_ARRAY) {
        Mods_Note(id, "native_models is a list: [{\"cards\": [364], \"package\": \"angel/model.json\"}]");
        return;
    }
    for (item = Json_At(list, 0); item; item = Json_Next(item), i++) {
        char where[40];
        snprintf(where, sizeof(where), "native_models[%d]", i);
        if (Json_TypeOf(item) == JSON_OBJECT && !Mods_EntryUsed(id, item, where)) continue;
        add_from_manifest(id, directory, item, where);
    }
}

static int ends_with(const char *text, const char *end)
{
    size_t a = strlen(text), b = strlen(end);
    return a >= b && !strcmp(text + a - b, end);
}

void NativeRegistry_Read(void)
{
    const char *path = getenv("MEMORIES_NATIVE_MODEL"), *id = getenv("MEMORIES_NATIVE_MODEL_ID");
    if (read_done) return;
    read_done = 1;
    Mods_VisitManifests(visit, NULL);
    if (path && *path) {
        Entry *e = new_entry(NULL, path);
        if (!e) return;
        snprintf(e->path, sizeof(e->path), "%s", path);
        e->package = ends_with(path, ".json");
        e->test = 1;
        e->model = id && *id ? atoi(id) : NATIVE_TEST_MODEL;
        entry_count++;
    }
}

/* --- reading a model --------------------------------------------------------------------------------------------- */
/* The whole file (4-byte aligned), or NULL; `*size` its length. */
static uint32_t *read_whole(const char *path, long *size)
{
    FILE *file = fopen(path, "rb");
    uint32_t *data = NULL;
    if (!file) return NULL;
    if (!fseek(file, 0, SEEK_END)) *size = ftell(file);
    if (*size > 0 && !fseek(file, 0, SEEK_SET)) data = (uint32_t *)malloc((size_t)*size);
    if (data && fread(data, 1, (size_t)*size, file) != (size_t)*size) {
        free(data);
        data = NULL;
    }
    fclose(file);
    return data;
}

/* `name` (from model.json) inside the package's folder -> `out`; 0 when it would leave the mod. */
static int in_package(const Entry *e, const char *name, char *out, size_t size)
{
    const char *slash = strrchr(e->path, '/');
    int folder;
#ifdef _WIN32
    /* a path typed or resolved on Windows (MEMORIES_NATIVE_MODEL, a command line) has backslashes */
    {
        const char *back = strrchr(e->path, '\\');
        if (back && (!slash || back > slash)) slash = back;
    }
#endif
    folder = slash ? (int)(slash - e->path) : 0;
    if (!Paths_Contained(name)) return 0;
    if (!slash) return snprintf(out, size, "%s", name) < (int)size;
    return snprintf(out, size, "%.*s/%s", folder, e->path, name) < (int)size;
}

/* Halves an RGBA image until both sides are at most `cap` (alpha-weighted, so clear texels do not darken edges). */
static uint8_t *shrink(uint8_t *rgba, uint32_t *w, uint32_t *h, uint32_t cap)
{
    while (*w > cap || *h > cap) {
        uint32_t nw = *w > 1 ? *w / 2 : 1, nh = *h > 1 ? *h / 2 : 1, x, y;
        uint8_t *to = (uint8_t *)malloc((size_t)nw * nh * 4);
        if (!to) return rgba;
        for (y = 0; y < nh; y++)
            for (x = 0; x < nw; x++) {
                unsigned sum[3] = {0, 0, 0}, alpha = 0, k;
                uint8_t *o = to + ((size_t)y * nw + x) * 4;
                for (k = 0; k < 4; k++) {
                    uint32_t sx = x * 2 + (k & 1), sy = y * 2 + (k >> 1);
                    const uint8_t *p;
                    if (sx >= *w) sx = *w - 1;
                    if (sy >= *h) sy = *h - 1;
                    p = rgba + ((size_t)sy * *w + sx) * 4;
                    sum[0] += (unsigned)p[0] * p[3];
                    sum[1] += (unsigned)p[1] * p[3];
                    sum[2] += (unsigned)p[2] * p[3];
                    alpha += p[3];
                }
                for (k = 0; k < 3; k++) o[k] = alpha ? (uint8_t)((sum[k] + alpha / 2) / alpha) : 0;
                o[3] = (uint8_t)((alpha + 2) / 4);
            }
        free(rgba);
        rgba = to;
        *w = nw;
        *h = nh;
    }
    return rgba;
}

/* A PNG as RGBA8, at most `cap` a side; NULL with `why` set. */
static uint8_t *read_png(const char *path, uint32_t *w, uint32_t *h, size_t room, char *why, size_t why_size)
{
    png_image image;
    FILE *file;
    uint8_t *rgba;
    uint64_t bytes;
    memset(&image, 0, sizeof(image));
    image.version = PNG_IMAGE_VERSION;
    file = fopen(path, "rb");
    if (!file) {
        snprintf(why, why_size, "it cannot be read");
        return NULL;
    }
    if (!png_image_begin_read_from_stdio(&image, file)) {
        snprintf(why, why_size, "not a PNG (%s)", image.message);
        fclose(file);
        return NULL;
    }
    bytes = (uint64_t)image.width * image.height * 4u;
    if (image.width < 1 || image.height < 1 || image.width > NATIVE_FORMAT_MAX_SIDE || image.height > NATIVE_FORMAT_MAX_SIDE ||
        bytes > room) {
        snprintf(why, why_size, "%ux%u is too large (each side at most %u, and within the memory budget)", (unsigned)image.width,
                 (unsigned)image.height, NATIVE_FORMAT_MAX_SIDE);
        png_image_free(&image);
        fclose(file);
        return NULL;
    }
    image.format = PNG_FORMAT_RGBA;
    rgba = (uint8_t *)malloc((size_t)bytes);
    if (!rgba || !png_image_finish_read(&image, NULL, rgba, 0, NULL)) {
        if (rgba) snprintf(why, why_size, "it cannot be decoded (%s)", image.message);
        else snprintf(why, why_size, "no memory for it");
        free(rgba);
        png_image_free(&image);
        fclose(file);
        return NULL;
    }
    fclose(file);
    *w = image.width;
    *h = image.height;
    png_image_free(&image);
    return shrink(rgba, w, h, texture_cap());
}

/* One of the package's textures over the model file's. */
static void package_texture(Entry *e, const JsonValue *textures, int slot, const char *key, size_t room)
{
    const JsonValue *value = Json_Member(textures, key);
    const char *name = Json_String(value, "");
    char path[PATH_SIZE], why[200];
    uint32_t w = 0, h = 0;
    uint8_t *rgba;
    if (!value) return;
    if (!*name || !in_package(e, name, path, sizeof(path))) {
        note(e, "textures.%s: \"%s\" is not a file inside the mod", key, name);
        return;
    }
    rgba = read_png(path, &w, &h, room, why, sizeof(why));
    if (!rgba) {
        note(e, "textures.%s: %s: %s (the model's own is used)", key, name, why);
        return;
    }
    e->maps[slot] = rgba;
    e->bytes += (size_t)w * h * 4u;
    if (slot == 0) {
        e->mesh.rgba = rgba;
        e->mesh.tex_w = w;
        e->mesh.tex_h = h;
    } else if (slot == 1) {
        e->mesh.normal_rgba = rgba;
        e->mesh.normal_w = w;
        e->mesh.normal_h = h;
    } else {
        e->mesh.mr_rgba = rgba;
        e->mesh.mr_w = w;
        e->mesh.mr_h = h;
    }
}

static int clip_index(const NativeMesh *mesh, const char *name)
{
    unsigned i;
    for (i = 0; i < mesh->clip_count; i++)
        if (!strcmp(mesh->clips[i].name, name)) return (int)i;
    return -1;
}

static void package_clips(Entry *e, const JsonValue *clips)
{
    const JsonValue *member;
    if (!clips) return;
    if (Json_TypeOf(clips) != JSON_OBJECT) {
        note(e, "\"clips\" maps acts to the model's clips: {\"attack\": \"Sword_Attack\"}");
        return;
    }
    for (member = Json_At(clips, 0); member; member = Json_Next(member)) {
        const char *act = Json_Name(member), *clip = Json_String(member, "");
        int a, index;
        for (a = 0; a < NATIVE_ACT_COUNT && strcmp(act, act_names[a]); a++) continue;
        if (a == NATIVE_ACT_COUNT) {
            note(e, "clips: \"%s\" is not an act (idle, enter, attack, hit, destroyed, win, guard)", act);
            continue;
        }
        index = clip_index(&e->mesh, clip);
        if (index < 0) {
            note(e, "clips.%s: the model has no clip \"%s\"", act, clip);
            continue;
        }
        e->mesh.act_clip[a] = (uint8_t)(index + 1);
    }
}

static void package_strike(Entry *e, const JsonValue *strike)
{
    const JsonValue *frames = Json_Member(strike, "attack"), *value;
    const NativeClip *clip = NativeAnim_ActClip(&e->mesh, NATIVE_ACT_ATTACK);
    long last = -1;
    if (!strike) return;
    if (Json_TypeOf(frames) != JSON_ARRAY) {
        note(e, "\"strike\" lists the attack clip's frames where its blows land: {\"attack\": [11, 30]}");
        return;
    }
    for (value = Json_At(frames, 0); value; value = Json_Next(value)) {
        long frame = Json_TypeOf(value) == JSON_NUMBER ? Json_Number(value, -1) : -1;
        if (e->mesh.strike_count >= NATIVE_MAX_STRIKES) {
            note(e, "strike.attack: at most %d blows", NATIVE_MAX_STRIKES);
            break;
        }
        if (frame <= last || !clip || frame >= (long)clip->frames) {
            note(e, "strike.attack: %ld is not a frame of the attack clip (%s, %u frames) after the one before", frame,
                 clip ? clip->name : "none", clip ? clip->frames : 0u);
            e->mesh.strike_count = 0;
            return;
        }
        e->mesh.strike[e->mesh.strike_count++] = (uint16_t)frame;
        last = frame;
    }
}

/* One look value: the environment (a float) over the mod's setting (an int, `unit` per 1.0) over the package's look
 * over the default. */
static float tune_value(const Entry *e, const JsonValue *look, const char *env, const char *key, float unit, float fallback)
{
    const char *text = env ? getenv(env) : NULL;
    long given = Json_Number(Json_Member(look, key), -1);
    float value = given >= 0 ? (float)given / unit : fallback;
    if (text && *text) return (float)atof(text);
    if (e->mod[0]) return (float)Mods_Setting(e->mod, key, (int)(value * unit + 0.5f)) / unit;
    return value;
}

static void package_tune(Entry *e, const JsonValue *look)
{
    NativeTune *t = &e->mesh.tune;
    if (look && Json_TypeOf(look) != JSON_OBJECT) {
        note(e, "\"look\" is an object: {\"ambient\": 20, \"light_gain\": 100}");
        look = NULL;
    }
    t->camera_near = tune_value(e, look, "MEMORIES_ARENA_CAMERA_NEAR", "camera_near", 1.0f, 1000.0f);
    t->camera_keep = tune_value(e, look, "MEMORIES_ARENA_CAMERA_KEEP", "camera_keep", 100.0f, 0.5f);
    t->camera_scale = tune_value(e, look, "MEMORIES_ARENA_CAMERA_SCALE", "camera_scale", 100.0f, 1.0f);
    t->ambient = tune_value(e, look, "MEMORIES_NATIVE_AMBIENT", "ambient", 100.0f, 0.2f);
    t->light_gain = tune_value(e, look, "MEMORIES_NATIVE_LIGHT_GAIN", "light_gain", 100.0f, 1.0f);
    t->normal_strength = tune_value(e, look, "MEMORIES_NATIVE_NORMAL_STRENGTH", "normal_strength", 100.0f, 1.8f);
    t->highlight = tune_value(e, look, "MEMORIES_NATIVE_SPEC", "highlight", 100.0f, 1.0f);
    t->flip_green = tune_value(e, look, "MEMORIES_NATIVE_NORMAL_FLIPY", "flip_green", 1.0f, 1.0f);
    if (t->camera_near < 100.0f) t->camera_near = 1000.0f;
    if (t->camera_keep < 0.2f || t->camera_keep > 1.0f) t->camera_keep = 0.5f;
    if (t->camera_scale < 0.2f || t->camera_scale > 6.0f) t->camera_scale = 1.0f;
}

/* A map the package has only one of: the other one flat, so the lit program still runs. */
static void complete_maps(Entry *e)
{
    static const uint8_t flat_normal[4] = {128, 128, 255, 255}, plain_surface[4] = {0, 160, 0, 255}; /* roughness 0.63, no metal */
    NativeMesh *m = &e->mesh;
    if (m->normal_rgba && !m->mr_rgba) {
        m->mr_rgba = plain_surface;
        m->mr_w = m->mr_h = 1;
    } else if (m->mr_rgba && !m->normal_rgba) {
        m->normal_rgba = flat_normal;
        m->normal_w = m->normal_h = 1;
    }
}

static void forget(Entry *e)
{
    int k;
    free(e->data);
    for (k = 0; k < 3; k++) free(e->maps[k]);
    e->data = NULL;
    memset(e->maps, 0, sizeof(e->maps));
    memset(&e->mesh, 0, sizeof(e->mesh));
    used_bytes -= e->bytes < used_bytes ? e->bytes : used_bytes;
    e->bytes = 0;
}

static const char *const package_keys[] = {"format", "name", "model", "textures", "clips", "strike", "scale", "look",
                                           "author", "license", "source", "converter"};

static int load(Entry *e)
{
    char file[PATH_SIZE], why[200] = "it cannot be read";
    JsonDocument *document = NULL;
    const JsonValue *root = NULL, *member;
    size_t room = budget();
    long size = 0;
    uint32_t i;
    e->state = REFUSED;
    room = room > used_bytes ? room - used_bytes : 0;
    if (e->package) {
        const char *name;
        long format;
        document = Json_ParseFile(e->path, why, sizeof(why));
        if (!document) {
            note(e, "model.json: %s", why);
            return 0;
        }
        root = Json_Root(document);
        format = Json_Number(Json_Member(root, "format"), 1);
        name = Json_String(Json_Member(root, "model"), "");
        if (Json_TypeOf(root) != JSON_OBJECT || format != 1) {
            if (Json_TypeOf(root) != JSON_OBJECT) note(e, "model.json is not an object");
            else note(e, "model.json is format %ld; this build reads format 1", format);
            Json_Free(document);
            return 0;
        }
        for (member = Json_At(root, 0); member; member = Json_Next(member)) {
            size_t k;
            for (k = 0; k < sizeof(package_keys) / sizeof(package_keys[0]) && strcmp(Json_Name(member), package_keys[k]); k++)
                continue;
            if (k == sizeof(package_keys) / sizeof(package_keys[0])) note(e, "model.json: \"%s\" is not read", Json_Name(member));
        }
        if (!*name || !in_package(e, name, file, sizeof(file))) {
            note(e, "model.json: \"model\" names the .hdm file beside it (\"%s\" is not a file inside the mod)", name);
            Json_Free(document);
            return 0;
        }
    } else {
        snprintf(file, sizeof(file), "%s", e->path);
    }
    e->data = read_whole(file, &size);
    if (e->data && (size_t)size > room) {
        snprintf(why, sizeof(why), "%ld MB would go past the native models' memory budget (MEMORIES_NATIVE_BUDGET_MB)",
                 size / (1024 * 1024) + 1);
        free(e->data);
        e->data = NULL;
    }
    if (!e->data || !NativeFormat_ParseHdm4(e->data, (size_t)size, &e->mesh, why, sizeof(why))) {
        note(e, "%s is not a usable HDM4 model: %s", file, why);
        forget(e);
        Json_Free(document);
        return 0;
    }
    e->bytes = (size_t)size;
    e->mesh.ground = -1e30f;
    for (i = 0; i < e->mesh.vertices; i++) {
        float y;
        memcpy(&y, e->mesh.words + (size_t)i * e->mesh.stride + 1, sizeof(y));
        if (y > e->mesh.ground) e->mesh.ground = y;
    }
    if (root) {
        const JsonValue *textures = Json_Member(root, "textures"), *scale = Json_Member(root, "scale");
        if (textures && Json_TypeOf(textures) != JSON_OBJECT) note(e, "\"textures\" is an object: {\"base\": \"base.png\"}");
        package_texture(e, textures, 0, "base", room > e->bytes ? room - e->bytes : 0);
        package_texture(e, textures, 1, "normal", room > e->bytes ? room - e->bytes : 0);
        package_texture(e, textures, 2, "metal_roughness", room > e->bytes ? room - e->bytes : 0);
        package_clips(e, Json_Member(root, "clips"));
        package_strike(e, Json_Member(root, "strike"));
        if (scale) {
            long percent = Json_TypeOf(scale) == JSON_NUMBER ? Json_Number(scale, -1) : -1;
            if (percent < 10 || percent > 1000) note(e, "\"scale\" is a percentage, 10 to 1000");
            else e->mesh.scale = (float)percent / 100.0f;
        }
    }
    complete_maps(e);
    package_tune(e, root ? Json_Member(root, "look") : NULL);
    Json_Free(document);
    used_bytes += e->bytes;
    e->state = READY;
    fprintf(stderr, "memories-pc: native model: %s: %s (%u vertices, %u bones, %u clips, texture %ux%u, %u KB)\n", e->name,
            file, e->mesh.vertices, e->mesh.bones, e->mesh.clip_count, e->mesh.tex_w, e->mesh.tex_h, (unsigned)(e->bytes / 1024));
    return 1;
}

/* --- finding one ------------------------------------------------------------------------------------------------- */
/* How well an entry fits a slot: 3 the test switch, 2 the card, 1 the disc model, 0 not at all. */
static int fit(const Entry *e, int model, int card)
{
    int k;
    if (e->test) return e->model == -2 || e->model == model ? 3 : 0;
    if (card > 0 && e->card_count) {
        for (k = 0; k < e->card_count; k++)
            if (e->cards[k] == card) return 2;
        return 0;
    }
    if (e->model >= 0) return e->model == model;
    for (k = 0; k < e->card_count; k++) /* the card unknown: the disc pairs model id and card id - 1 */
        if (e->cards[k] == model + 1) return 1;
    return 0;
}

int NativeRegistry_Find(int model, int card)
{
    if (model < 0) return -1;
    NativeRegistry_Read();
    for (;;) {
        int best = -1, best_fit = 0, i;
        for (i = entry_count - 1; i >= 0; i--) {
            int f = entries[i].state == REFUSED ? 0 : fit(&entries[i], model, card);
            if (f > best_fit) {
                best = i;
                best_fit = f;
            }
        }
        if (best < 0) return -1;
        if (entries[best].state == READY || load(&entries[best])) return best;
    }
}

const NativeMesh *NativeRegistry_Mesh(int id)
{
    return id >= 0 && id < entry_count && entries[id].state == READY ? &entries[id].mesh : NULL;
}

const char *NativeRegistry_Name(int id)
{
    return id >= 0 && id < entry_count ? entries[id].name : "";
}

size_t NativeRegistry_Bytes(void)
{
    return used_bytes;
}

void NativeRegistry_Reset(void)
{
    int i;
    for (i = 0; i < entry_count; i++) forget(&entries[i]);
    entry_count = 0;
    read_done = 0;
    used_bytes = 0;
}
