/* Native model pass: the capture side (see native_model.h). */
#include "pc/render/native_model.h"
#include "pc/render/native_registry.h"
#include "pc/render/native_anim.h"
#include "pc/render/native_cinematic.h"
#include "pc/render/soft_gpu.h"
#include "pc/compat/fs.h"
#include "pc/compat/gte.h"
#include "pc/debug/log.h"
#include "pc/sdk/display.h"
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
static int logged; /* MEMORIES_NATIVE_MODEL_LOG */
volatile int NativeModel_Suppress;
volatile int NativeModel_GlReady;
unsigned NativeModel_Nearest = ~0u;

/* NativeModel_SetInstance's, for the next BeginSlot only; then the draw being captured's. */
static NativeInstance pending, instance;
static int pending_set, instance_set;
static int battle_card[2]; /* NativeModel_SetBattleCards */
unsigned NativeModel_Stats[8]; /* parts captured, draws closed, markers linked, takes with draws, replayed ops, markers hit, triangles */

static void load(void)
{
    loaded = 1;
    logged = getenv("MEMORIES_NATIVE_MODEL_LOG") != NULL;
    NativeRegistry_Read();
}

const NativeMesh *NativeModel_MeshById(int id)
{
    return NativeRegistry_Mesh(id);
}

/* The card a slot draw shows: a code mod's word for it, else the battle's card for the arena's two slots. */
static int slot_card(int slot)
{
    if (instance_set) return instance.card;
    return slot >= 0 && slot < 2 ? battle_card[slot] : 0;
}

void NativeModel_SetInstance(const NativeInstance *in)
{
    size_t size;
    if (!in) {
        pending_set = 0;
        return;
    }
    memset(&pending, 0, sizeof(pending));
    pending.contact_frame = -1;
    size = in->size > 0 && (size_t)in->size < sizeof(pending) ? (size_t)in->size : sizeof(pending);
    memcpy(&pending, in, size); /* fields past the caller's size keep their defaults */
    pending.size = (int32_t)sizeof(pending);
    if (pending.context < 0 || pending.context >= NATIVE_CONTEXT_COUNT) pending.context = NATIVE_CONTEXT_ARENA;
    pending.key &= 0xffff;
    pending.fade = pending.fade < 0 ? 0 : pending.fade > 255 ? 255 : pending.fade;
    pending_set = 1;
}

/* What each arena slot last played (the game's own draws): the act and the frame of its row, for the camera's shots. */
static struct {
    int act, frame; /* frame < 0: not drawn since the battle began */
} arena_play[2] = {{0, -1}, {0, -1}};

void NativeModel_SetBattleCards(int card0, int card1)
{
    battle_card[0] = card0;
    battle_card[1] = card1;
    arena_play[0].frame = arena_play[1].frame = -1; /* a new battle: nothing played yet */
}

void NativeModel_BeginSlot(int model, int slot)
{
    int mesh_id;
    current = NULL;
    NativeModel_Suppress = 0;
    NativeModel_Nearest = ~0u;
    instance = pending; /* a code mod's word for this draw, used once */
    instance_set = pending_set;
    pending_set = 0;
    if (!loaded) load();
    if (logged && model >= 0) {
        static int last = -2;
        if (model != last) {
            fprintf(stderr, "memories-pc: native model: a slot draws model %d\n", model);
            last = model;
        }
    }
    if (instance_set && instance.context == NATIVE_CONTEXT_MEASURE) return; /* the mod reads the disc model's packets */
    if (frame_count >= NATIVE_MAX_DRAWS || (mesh_id = NativeRegistry_Find(model, slot_card(slot))) < 0) return;
    current = &frame[frame_count];
    memset(current, 0, sizeof(*current));
    current->model = model;
    current->mesh_id = mesh_id;
    current->tint = D_8009AFB4 & 0x00ffffffu; /* the Gouraud triangle template: its colour is what the lighting scales */
    /* The model's own packets are left out only when the pass will draw it: the GL pass is ready and the picture is
     * recorded for it (2x or more). Otherwise the disc model is drawn, as without a native model. */
    NativeModel_Suppress = NativeModel_GlReady && SoftGpu_Scale() > 1;
}

int NativeModel_WillDraw(int model, int card)
{
    if (!loaded) load();
    return model >= 0 && NativeModel_GlReady && SoftGpu_Scale() > 1 && NativeRegistry_Find(model, card) >= 0;
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
    NativeSlotInfo *out;
    if (!current || !info) return;
    if (!instance_set && info->slot >= 0 && info->slot < 2) {
        arena_play[info->slot].act = (int)NativeAnim_Act(info->anim_index, info->attack_row);
        arena_play[info->slot].frame = info->anim_frame >> 4;
    }
    out = &current->info;
    *out = *info;
    if (instance_set) { /* a code mod's monster: its own key space per context, so it never shares the arena's state */
        out->context = instance.context;
        out->key = (instance.context << 16) | instance.key;
        out->card = instance.card;
        out->fade = instance.fade;
        out->contact_frame = instance.contact_frame;
    } else { /* the game's own slot */
        out->context = NATIVE_CONTEXT_ARENA;
        out->key = info->slot;
        out->card = info->slot >= 0 && info->slot < 2 ? battle_card[info->slot] : 0;
        out->fade = 0;
        out->contact_frame = -1;
    }
}

int NativeModel_EndSlot(void)
{
    int draw;
    int empty = NativeModel_Nearest == ~0u; /* no packet kept; with a part drawn the slot holds a model anyway */
    int k;
    NativeModel_Suppress = 0;
    if (!current) return 0;
    for (k = 0; k < NATIVE_MAX_PARTS; k++)
        if (current->parts[k].used) empty = 0;
    /* The game's own draw of a slot that drew no part and is in no battle (no card): the slot is empty while a code
     * mod loads a monster into it. There is nothing for the native model to stand for. (Not "no packet was kept": the
     * packets are kept only once the pass is ready, and the first draw is what makes it ready; the Library's model
     * view, which has no battle card, would never show a native model.) */
    if (empty && !instance_set && !current->info.card) {
        current = NULL;
        return 0;
    }
    LOG(LOG_MODEL, "evt native f=%u model=%d mesh=%d context=%d key=%d card=%d row=%d clock=%d fade=%d contact=%d entry=%d",
        Memories_PresentedFrames(), (int)current->model, (int)current->mesh_id, (int)current->info.context, (int)current->info.key,
        (int)current->info.card, (int)current->info.anim_index, (int)current->info.anim_frame, (int)current->info.fade,
        (int)current->info.contact_frame, NativeModel_Nearest == ~0u ? -1 : (int)NativeModel_Nearest);
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
    /* At the nearest entry the model's own packets would have taken (the drivers kept it), so the model sorts at
     * its depth among the rest of the table; entry 0 (drawn last) when none was kept. */
    unsigned at = NativeModel_Nearest != ~0u ? NativeModel_Nearest : 0u;
    if (draw < 1 || !entries || !packet) return;
    packet[0] = (entries[at] & 0x00ffffffu) | (1u << 24);
    packet[1] = NATIVE_MARKER | (uint32_t)((draw - 1) & 0xff);
    entries[at] = (uint32_t)(uintptr_t)packet & 0x00ffffffu;
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
static float arena_camera_distance(const NativeTune *t, float distance)
{
    if (distance < t->camera_near) distance = t->camera_near - (t->camera_near - distance) * t->camera_keep;
    return distance * t->camera_scale;
}

/* The factor the eye's offset from the look-at point is multiplied by (1 = the game's own camera): only in a battle one of
 * whose two monsters the native pass draws, so every other battle, the credits and a 1x picture keep the game's camera. */
float NativeModel_ArenaCameraFactor(int model0, int model1, float dx, float dy, float dz)
{
    const NativeMesh *mesh = NULL;
    float d;
    /* The look of the first of the two the pass draws (the attacker's when both are). */
    if (NativeModel_WillDraw(model0, battle_card[0])) mesh = NativeRegistry_Mesh(NativeRegistry_Find(model0, battle_card[0]));
    else if (NativeModel_WillDraw(model1, battle_card[1])) mesh = NativeRegistry_Mesh(NativeRegistry_Find(model1, battle_card[1]));
    if (!mesh) return 1.0f;
    d = sqrtf(dx * dx + dy * dy + dz * dz);
    return d > 1.0f ? arena_camera_distance(&mesh->tune, d) / d : 1.0f;
}

/* The arena camera's shot: of the two monsters (the attacker's, then the defender's) drawn natively, the strongest shot of
 * their packages that matches what the battle's two monsters are playing. */
int NativeModel_ArenaShot(int model0, int model1, const float look[3], float eye[3])
{
    int s;
    float best = 0.0f;
    NativeCamera camera, chosen;
    chosen.yaw = chosen.pitch = chosen.height = 0.0f;
    chosen.distance = 1.0f;
    for (s = 0; s < 2; s++) {
        int model = s ? model1 : model0;
        const NativeMesh *mesh;
        float w;
        if (arena_play[s].frame < 0 || !NativeModel_WillDraw(model, battle_card[s])) continue;
        mesh = NativeRegistry_Mesh(NativeRegistry_Find(model, battle_card[s]));
        if (!mesh || !mesh->shot_count) continue;
        w = NativeCinematic_Pick(mesh->shots, mesh->shot_count, arena_play[s].act, arena_play[s].frame, arena_play[1 - s].act,
                                 arena_play[1 - s].frame, &camera);
        if (w > best) {
            best = w;
            chosen = camera;
        }
    }
    {
        NativeCamera over;
        if (NativeCinematic_Override(&over)) {
            NativeCinematic_Orbit(look, eye, &over, eye);
            return 1;
        }
    }
    if (best <= 0.0f) return 0;
    NativeCinematic_Orbit(look, eye, &chosen, eye);
    return 1;
}

int NativeModel_FieldShot(NativeFieldShot *shot)
{
    int s;
    float best = 0.0f;
    NativeCamera camera, chosen;
    if (!shot || shot->size < (int32_t)sizeof(NativeFieldShot)) return 0;
    chosen.yaw = chosen.pitch = chosen.height = 0.0f;
    chosen.distance = 1.0f;
    for (s = 0; s < 2; s++) {
        int act[2], frame[2], i;
        const NativeMesh *mesh;
        float w;
        if (shot->card[s] <= 0 || !NativeModel_WillDraw(shot->card[s] - 1, shot->card[s])) continue;
        mesh = NativeRegistry_Mesh(NativeRegistry_Find(shot->card[s] - 1, shot->card[s]));
        if (!mesh || !mesh->shot_count) continue;
        for (i = 0; i < 2; i++) {
            act[i] = shot->row[i] ? (int)NativeAnim_Act(shot->row[i], shot->attack_row[i]) : (int)NATIVE_ACT_IDLE;
            frame[i] = shot->row[i] ? shot->frame[i] : 0;
        }
        w = NativeCinematic_Pick(mesh->shots, mesh->shot_count, act[s], frame[s], act[1 - s], frame[1 - s], &camera);
        if (w > best) {
            best = w;
            chosen = camera;
        }
    }
    {
        NativeCamera over;
        if (NativeCinematic_Override(&over)) {
            shot->yaw = over.yaw;
            shot->pitch = over.pitch;
            shot->distance = over.distance;
            shot->height = over.height;
            return 1;
        }
    }
    shot->yaw = chosen.yaw;
    shot->pitch = chosen.pitch;
    shot->distance = chosen.distance;
    shot->height = chosen.height;
    return best > 0.0f;
}
