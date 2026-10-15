/* Native model pass: the capture side (see native_model.h). */
#include "pc/render/native_model.h"
#include "pc/compat/gte.h"
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
    if (!data || fread(data, 1, (size_t)size, file) != (size_t)size || size < 20 ||
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
