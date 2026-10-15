/* Native model pass: the capture side (see native_model.h). */
#include "pc/render/native_model.h"
#include "pc/compat/gte.h"
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

static void load(void)
{
    const char *path = getenv("MEMORIES_NATIVE_MODEL");
    const char *id = getenv("MEMORIES_NATIVE_MODEL_ID");
    FILE *file;
    long size;
    uint32_t *data;
    loaded = 1;
    logged = getenv("MEMORIES_NATIVE_MODEL_LOG") != NULL;
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
        const uint32_t *w = data;
        size_t at = 8 + (size_t)w[3] * 16, k;
        memset(&mesh, 0, sizeof(mesh));
        mesh.vertices = w[1];
        mesh.index_count = w[2];
        mesh.bones = w[3];
        mesh.tex_w = w[4];
        mesh.tex_h = w[5];
        mesh.clip_count = w[6] < NATIVE_MAX_CLIPS ? w[6] : NATIVE_MAX_CLIPS;
        mesh.stride = 13;
        mesh.bone_table = w + 8;
        mesh.words = w + at;
        at += (size_t)mesh.vertices * 13;
        mesh.indices = w + at;
        at += mesh.index_count;
        mesh.rgba = (const uint8_t *)(w + at);
        at += (size_t)mesh.tex_w * mesh.tex_h;
        for (k = 0; k < mesh.clip_count; k++) {
            const uint32_t *c = w + at;
            if (at * 4 + 48 > (size_t)size) break;
            memcpy(mesh.clips[k].name, c, 32);
            mesh.clips[k].name[31] = 0;
            mesh.clips[k].frames = c[8];
            memcpy(&mesh.clips[k].fps, c + 9, 4);
            mesh.clips[k].data = (const float *)(c + 12);
            at += 12 + (size_t)c[8] * mesh.bones * 7;
        }
        if (mesh.bones > NATIVE_MAX_BONES || at * 4 != (size_t)size) {
            fprintf(stderr, "memories-pc: native model: %s (HDM4) has the wrong size or too many bones\n", path);
            memset(&mesh, 0, sizeof(mesh));
            free(data);
            fclose(file);
            return;
        }
        fclose(file);
        mesh_model = id ? atoi(id) : 364;
        fprintf(stderr, "memories-pc: native model: %s (HDM4) for model %d (%u vertices, %u bones, %u clips)\n", path, mesh_model,
                mesh.vertices, mesh.bones, mesh.clip_count);
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
    return (model == mesh_model || (mesh_model == -2 && model >= 0)) && mesh.words ? &mesh : NULL;
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
    if ((model != mesh_model && !(mesh_model == -2 && model >= 0)) || !mesh.words || frame_count >= NATIVE_MAX_DRAWS) return;
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
 * under MEMORIES_ARENA_CAMERA_NEAR (default 1000) are pushed out: d' = NEAR - (NEAR - d) * KEEP (MEMORIES_ARENA_CAMERA_KEEP, 0.2..1,
 * default 0.5; 1 = unchanged), then everything is multiplied by MEMORIES_ARENA_CAMERA_SCALE (0.2..6, default 1). */
static float arena_camera_distance(float distance)
{
    static float near_distance = -1.0f, keep = 0.5f, scale = 1.0f;
    if (near_distance < 0.0f) {
        const char *n = getenv("MEMORIES_ARENA_CAMERA_NEAR"), *kp = getenv("MEMORIES_ARENA_CAMERA_KEEP"), *sc = getenv("MEMORIES_ARENA_CAMERA_SCALE");
        near_distance = n && *n ? (float)atof(n) : 1000.0f;
        keep = kp && *kp ? (float)atof(kp) : 0.5f;
        scale = sc && *sc ? (float)atof(sc) : 1.0f;
        if (keep < 0.2f || keep > 1.0f) keep = 0.5f;
        if (scale < 0.2f || scale > 6.0f) scale = 1.0f;
        if (near_distance < 100.0f) near_distance = 1000.0f;
    }
    if (distance < near_distance) distance = near_distance - (near_distance - distance) * keep;
    return distance * scale;
}

/* The factor the eye's offset (only while a native model is loaded) from the look-at point is multiplied by (1 = the game's own camera). */
float NativeModel_ArenaCameraFactor(float dx, float dy, float dz)
{
    if (!loaded) load();
    if (!mesh.words) return 1.0f; /* no native model: the game's own camera, as it was */
    float d = sqrtf(dx * dx + dy * dy + dz * dz);
    return d > 1.0f ? arena_camera_distance(d) / d : 1.0f;
}
