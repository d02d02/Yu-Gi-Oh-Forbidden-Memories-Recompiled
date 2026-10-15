/* Native model pass: the capture side (see native_model.h). */
#include "pc/render/native_model.h"
#include "pc/compat/gte.h"
#include "pc/mods/json.h"
#include "pc/mods/mods.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern uint32_t D_800FE240; /* LIBGS packet cursor */
extern uint32_t D_8009AFB4; /* the slot's Gouraud triangle template (colour in the low 3 bytes) */

static NativeDraw frame[NATIVE_MAX_DRAWS];
static size_t frame_count;
static NativeDraw taken[NATIVE_MAX_DRAWS];
static size_t taken_count;
static NativeDraw *current;
static int32_t next_id;

static int loaded; /* 1 once the environment was read */
/* MEMORIES_NATIVE_MODEL_ID=-2 is a TEST switch: the mesh is drawn in every duel slot (two native models for depth tests).
 * Only the model the mesh was made for is posed right; the others get garbage joints. */
static int mesh_model = -1;
static NativeMesh mesh;
static int logged;
volatile int NativeModel_Suppress;
volatile int NativeModel_GlReady;
unsigned NativeModel_Stats[8]; /* parts captured, draws closed, markers linked, takes with draws, replayed ops, markers hit, triangles */

/* One HDM4 file in memory (`data`, kept by the mesh) -> `out`; 0 when it is malformed (nothing is kept then). */
static int parse_hdm4(const char *path, uint32_t *data, long size, NativeMesh *out)
{
    const uint32_t *w = data;
    size_t at = 8 + (size_t)w[3] * 16, k;
    NativeMesh m;
    memset(&m, 0, sizeof(m));
    m.vertices = w[1];
    m.index_count = w[2];
    m.bones = w[3];
    m.tex_w = w[4];
    m.tex_h = w[5];
    m.clip_count = w[6] < NATIVE_MAX_CLIPS ? w[6] : NATIVE_MAX_CLIPS;
    m.stride = 13;
    if (m.bones > NATIVE_MAX_BONES) {
        fprintf(stderr, "memories-pc: native model: %s (HDM4) has too many bones\n", path);
        return 0;
    }
    m.bone_table = w + 8;
    m.words = w + at;
    at += (size_t)m.vertices * 13;
    m.indices = w + at;
    at += m.index_count;
    m.rgba = (const uint8_t *)(w + at);
    at += (size_t)m.tex_w * m.tex_h;
    if (w[7] & 1) { /* a normal map: u32 w, u32 h, RGBA */
        m.normal_w = w[at];
        m.normal_h = w[at + 1];
        m.normal_rgba = (const uint8_t *)(w + at + 2);
        at += 2 + (size_t)m.normal_w * m.normal_h;
    }
    if (w[7] & 2) { /* a metal (B) / roughness (G) map */
        m.mr_w = w[at];
        m.mr_h = w[at + 1];
        m.mr_rgba = (const uint8_t *)(w + at + 2);
        at += 2 + (size_t)m.mr_w * m.mr_h;
    }
    for (k = 0; k < m.clip_count; k++) {
        const uint32_t *c = w + at;
        if (at * 4 + 48 > (size_t)size) break;
        memcpy(m.clips[k].name, c, 32);
        m.clips[k].name[31] = 0;
        m.clips[k].frames = c[8];
        memcpy(&m.clips[k].fps, c + 9, 4);
        m.clips[k].data = (const float *)(c + 12);
        at += 12 + (size_t)c[8] * m.bones * 7;
    }
    if (at * 4 != (size_t)size) {
        fprintf(stderr, "memories-pc: native model: %s (HDM4) has the wrong size\n", path);
        return 0;
    }
    *out = m;
    return 1;
}

/* The whole file, or NULL. */
static uint32_t *read_whole(const char *path, long *size)
{
    FILE *file = fopen(path, "rb");
    uint32_t *data;
    if (!file) return NULL;
    fseek(file, 0, SEEK_END);
    *size = ftell(file);
    fseek(file, 0, SEEK_SET);
    data = *size >= 32 ? (uint32_t *)malloc((size_t)*size) : NULL;
    if (data && fread(data, 1, (size_t)*size, file) != (size_t)*size) {
        free(data);
        data = NULL;
    }
    fclose(file);
    return data;
}

/* The models the applied mods name (manifest "native_models": [{"model": 363, "file": "angel.hdm"}]); the first mod that has any also
 * supplies the tuning settings (camera, light, normal map). */
#define NATIVE_MAX_MODELS 8
static struct { NativeMesh mesh; int model; } mod_models[NATIVE_MAX_MODELS];
static int mod_model_count;
static const char *tune_mod; /* the id of the first mod with native models */
static int any_model;        /* a model is loaded: the arena camera is adjusted for big models */
NativeTune NativeModel_Tune = {1000.0f, 0.5f, 1.0f, 0.2f, 1.0f, 1.8f, 1.0f, 1.0f};

static void visit_native_models(const char *id, const char *directory, const JsonValue *manifest, void *context)
{
    const JsonValue *list = Json_Member(manifest, "native_models");
    int i;
    (void)context;
    for (i = 0; i < Json_Count(list); i++) {
        const JsonValue *entry = Json_At(list, i);
        long model = Json_Number(Json_Member(entry, "model"), -1);
        const char *file = Json_String(Json_Member(entry, "file"), "");
        char path[1024];
        long size = 0;
        uint32_t *data;
        if (model < 0 || !*file) {
            Mods_Note(id, "native_models[%d] needs a \"model\" (the disc model id: card id - 1) and a \"file\"", i);
            continue;
        }
        if (mod_model_count >= NATIVE_MAX_MODELS) {
            Mods_Note(id, "native_models: at most %d models in all", NATIVE_MAX_MODELS);
            return;
        }
        snprintf(path, sizeof(path), "%s/%s", directory, file);
        data = read_whole(path, &size);
        if (!data || memcmp(data, "HDM4", 4) != 0 || !parse_hdm4(path, data, size, &mod_models[mod_model_count].mesh)) {
            Mods_Note(id, "native_models[%d]: %s is not a usable HDM4 model", i, file);
            free(data);
            continue;
        }
        mod_models[mod_model_count].model = (int)model;
        mod_model_count++;
        any_model = 1;
        if (!tune_mod) tune_mod = id;
        fprintf(stderr, "memories-pc: native model: %s for model %ld (mod %s)\n", path, model, id);
    }
}

/* One tuning value: the environment (a float) over the mod's setting (an int, `unit` per 1.0) over the default. */
static float tune_value(const char *env, const char *key, float unit, float fallback)
{
    const char *text = env ? getenv(env) : NULL;
    if (text && *text) return (float)atof(text);
    if (tune_mod && key) return (float)Mods_Setting(tune_mod, key, (int)(fallback * unit + 0.5f)) / unit;
    return fallback;
}

static void load_tuning(void)
{
    NativeTune *t = &NativeModel_Tune;
    t->camera_near = tune_value("MEMORIES_ARENA_CAMERA_NEAR", "camera_near", 1.0f, 1000.0f);
    t->camera_keep = tune_value("MEMORIES_ARENA_CAMERA_KEEP", "camera_keep", 100.0f, 0.5f);
    t->camera_scale = tune_value("MEMORIES_ARENA_CAMERA_SCALE", "camera_scale", 100.0f, 1.0f);
    t->ambient = tune_value("MEMORIES_NATIVE_AMBIENT", "ambient", 100.0f, 0.2f);
    t->light_gain = tune_value("MEMORIES_NATIVE_LIGHT_GAIN", "light_gain", 100.0f, 1.0f);
    t->normal_strength = tune_value("MEMORIES_NATIVE_NORMAL_STRENGTH", "normal_strength", 100.0f, 1.8f);
    t->highlight = tune_value("MEMORIES_NATIVE_SPEC", "highlight", 100.0f, 1.0f);
    t->flip_green = tune_value("MEMORIES_NATIVE_NORMAL_FLIPY", NULL, 1.0f, 1.0f);
    if (t->camera_near < 100.0f) t->camera_near = 1000.0f;
    if (t->camera_keep < 0.2f || t->camera_keep > 1.0f) t->camera_keep = 0.5f;
    if (t->camera_scale < 0.2f || t->camera_scale > 6.0f) t->camera_scale = 1.0f;
}

static void load(void)
{
    const char *path = getenv("MEMORIES_NATIVE_MODEL");
    const char *id = getenv("MEMORIES_NATIVE_MODEL_ID");
    FILE *file;
    long size;
    uint32_t *data;
    loaded = 1;
    logged = getenv("MEMORIES_NATIVE_MODEL_LOG") != NULL;
    Mods_VisitManifests(visit_native_models, NULL);
    load_tuning();
    if (!path || !*path) return;
    file = fopen(path, "rb");
    if (!file) {
        fprintf(stderr, "memories-pc: native model: cannot open %s\n", path);
        return;
    }
    fseek(file, 0, SEEK_END);
    size = ftell(file);
    fseek(file, 0, SEEK_SET);
    data = (uint32_t *)malloc((size_t)size);
    if (data && fread(data, 1, (size_t)size, file) != (size_t)size) {
        free(data);
        data = NULL;
    }
    if (data && size >= 32 && memcmp(data, "HDM4", 4) == 0) {
        fclose(file);
        if (parse_hdm4(path, data, size, &mesh)) {
            mesh_model = id ? atoi(id) : 364;
            any_model = 1;
            fprintf(stderr, "memories-pc: native model: %s (HDM4) for model %d (%u vertices, %u bones, %u clips)\n", path, mesh_model,
                    mesh.vertices, mesh.bones, mesh.clip_count);
        } else {
            free(data);
        }
        return;
    }
    if (!data || size < 20 ||
        (memcmp(data, "HDM1", 4) != 0 && memcmp(data, "HDM2", 4) != 0 && memcmp(data, "HDM3", 4) != 0)) {
        fprintf(stderr, "memories-pc: native model: %s is not a model.hdm\n", path);
        free(data);
        fclose(file);
        return;
    }
    fclose(file);
    mesh.vertices = data[1];
    mesh.parts = data[2];
    mesh.tex_w = data[3];
    mesh.tex_h = data[4];
    mesh.stride = memcmp(data, "HDM1", 4) == 0 ? 9 : 17;
    mesh.joint_parts = 0;
    mesh.joints = NULL;
    if (memcmp(data, "HDM3", 4) == 0) { /* a joint table of `parts` entries (16 words) sits between the header and the vertices */
        mesh.joint_parts = mesh.parts;
        mesh.joints = data + 5;
    }
    if ((size_t)size != 20 + (size_t)mesh.joint_parts * 64 + (size_t)mesh.vertices * mesh.stride * 4 +
                            (size_t)mesh.tex_w * mesh.tex_h * 4) {
        fprintf(stderr, "memories-pc: native model: %s has the wrong size\n", path);
        free(data);
        return;
    }
    mesh.words = data + 5 + (size_t)mesh.joint_parts * 16;
    mesh.rgba = (const uint8_t *)mesh.words + (size_t)mesh.vertices * mesh.stride * 4;
    mesh_model = id ? atoi(id) : 364;
    fprintf(stderr, "memories-pc: native model: %s for model %d (%u vertices, %u parts)\n", path, mesh_model,
            mesh.vertices, mesh.parts);
}

const NativeMesh *NativeModel_Mesh(int model)
{
    int i;
    if ((model == mesh_model || (mesh_model == -2 && model >= 0)) && mesh.words) return &mesh;
    for (i = 0; i < mod_model_count; i++)
        if (mod_models[i].model == model) return &mod_models[i].mesh;
    return NULL;
}

void NativeModel_BeginSlot(int model)
{
    current = NULL;
    if (!loaded) load();
    if (logged && model >= 0) {
        static int last = -2;
        if (model != last) {
            fprintf(stderr, "memories-pc: native model: a slot draws model %d\n", model);
            last = model;
        }
    }
    if (!NativeModel_Mesh(model) || frame_count >= NATIVE_MAX_DRAWS) return;
    current = &frame[frame_count];
    memset(current, 0, sizeof(*current));
    current->model = model;
    current->tint = D_8009AFB4 & 0x00ffffffu; /* the Gouraud triangle template: its colour is what the lighting scales */
    NativeModel_Suppress = NativeModel_GlReady;
}

void NativeModel_Part(int part)
{
    NativePart *p;
    uint32_t c[5];
    unsigned i;
    if (!current || part < 0 || part >= NATIVE_MAX_PARTS) return;
    p = &current->parts[part];
    for (i = 0; i < 5; i++) c[i] = Memories_GteReadControl(i);
    p->rot[0] = (int16_t)c[0];
    p->rot[1] = (int16_t)(c[0] >> 16);
    p->rot[2] = (int16_t)c[1];
    p->rot[3] = (int16_t)(c[1] >> 16);
    p->rot[4] = (int16_t)c[2];
    p->rot[5] = (int16_t)(c[2] >> 16);
    p->rot[6] = (int16_t)c[3];
    p->rot[7] = (int16_t)(c[3] >> 16);
    p->rot[8] = (int16_t)c[4];
    for (i = 0; i < 3; i++) p->tr[i] = (int32_t)Memories_GteReadControl(5 + i);
    for (i = 0; i < 5; i++) {
        uint32_t l = Memories_GteReadControl(8 + i), k = Memories_GteReadControl(16 + i);
        if (i < 4) {
            p->llm[i * 2] = (int16_t)l;
            p->llm[i * 2 + 1] = (int16_t)(l >> 16);
            p->lcm[i * 2] = (int16_t)k;
            p->lcm[i * 2 + 1] = (int16_t)(k >> 16);
        } else {
            p->llm[8] = (int16_t)l;
            p->lcm[8] = (int16_t)k;
        }
    }
    for (i = 0; i < 3; i++) current->bk[i] = (int32_t)Memories_GteReadControl(13 + i);
    p->used = 1;
    NativeModel_Stats[0]++;
    current->ofx = (int32_t)Memories_GteReadControl(24);
    current->ofy = (int32_t)Memories_GteReadControl(25);
    current->h = (int32_t)(Memories_GteReadControl(26) & 0xffff);
}

void NativeModel_SlotInfo(const NativeSlotInfo *info)
{
    if (current && info) current->info = *info;
}

int NativeModel_EndSlot(void)
{
    int draw;
    NativeModel_Suppress = 0;
    if (!current) return 0;
    NativeModel_Suppress = 0;
    current->id = next_id++;
    NativeModel_Stats[1]++;
    draw = (int)current->id + 1;
    frame_count++;
    current = NULL;
    return draw;
}

void NativeModel_Link(uint32_t *ot, int draw)
{
    /* GsOT: length, org (the entries), offset, ...; entry 0 is drawn last (nearest). */
    uint32_t *entries = (uint32_t *)(uintptr_t)ot[1];
    uint32_t *packet = (uint32_t *)(uintptr_t)D_800FE240;
    if (draw < 1 || !entries || !packet) return;
    packet[0] = (entries[0] & 0x00ffffffu) | (1u << 24);
    packet[1] = NATIVE_MARKER | (uint32_t)((draw - 1) & 0xff);
    entries[0] = (uint32_t)(uintptr_t)packet & 0x00ffffffu;
    D_800FE240 = (uint32_t)(uintptr_t)(packet + 2);
    NativeModel_Stats[2]++;
}

void NativeModel_Take(void)
{
    if (logged && frame_count) { /* how often the pose changes from one frame to the next: 1 = changed, 0 = the same */
        static uint32_t last_hash;
        static char history[65];
        static unsigned n;
        uint32_t hash = 2166136261u;
        size_t i;
        const uint8_t *bytes = (const uint8_t *)frame[0].parts;
        for (i = 0; i < sizeof(frame[0].parts); i++) hash = (hash ^ bytes[i]) * 16777619u;
        history[n % 64] = hash != last_hash ? '1' : '0';
        last_hash = hash;
        if (++n % 120 == 0) {
            char line[65];
            size_t k;
            for (k = 0; k < 64; k++) line[k] = history[(n + k) % 64];
            line[64] = 0;
            fprintf(stderr, "memories-pc: native model: pose changed per frame (oldest first): %s\n", line);
        }
    }
    taken_count = frame_count;
    if (frame_count) NativeModel_Stats[3]++;
    if (logged && frame_count) {
        static unsigned n;
        if (++n % 60 == 1)
            fprintf(stderr, "memories-pc: native model: stats parts %u draws %u linked %u taken %u replayed %u hit %u triangles %u\n",
                    NativeModel_Stats[0], NativeModel_Stats[1], NativeModel_Stats[2], NativeModel_Stats[3],
                    NativeModel_Stats[4], NativeModel_Stats[5], NativeModel_Stats[6]);
    }
    if (frame_count) memcpy(taken, frame, frame_count * sizeof(NativeDraw));
    frame_count = 0;
    current = NULL;
}

const NativeDraw *NativeModel_Taken(size_t *count)
{
    *count = taken_count;
    return taken;
}

/* The arena camera's distance from its look-at point, remapped (model_scene_states.c). The scripted camera is framed for the small PS1
 * models: its close shots (about 460-650 units) are too close for big native models, its wide orbit (1800) is fine. So distances
 * under camera_near are pushed out: d' = near - (near - d) * keep, then everything is multiplied by camera_scale. */
static float arena_camera_distance(float distance)
{
    const NativeTune *t = &NativeModel_Tune;
    if (distance < t->camera_near) distance = t->camera_near - (t->camera_near - distance) * t->camera_keep;
    return distance * t->camera_scale;
}

/* The factor the eye's offset from the look-at point is multiplied by (1 = the game's own camera), only while a native model is loaded. */
float NativeModel_ArenaCameraFactor(float dx, float dy, float dz)
{
    float d;
    if (!loaded) load();
    if (!any_model) return 1.0f;
    d = sqrtf(dx * dx + dy * dy + dz * dz);
    return d > 1.0f ? arena_camera_distance(d) / d : 1.0f;
}
