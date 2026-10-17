/* The native model pass's capture (src/pc/render/native_model.h), with the game around it stood in for: a slot draw
 * is the game's own (key = slot, the battle's card) unless a code mod named it just before (NativeModel_SetInstance:
 * used once, a smaller struct's missing fields at their defaults, a measuring draw captures nothing); the model's
 * packets are left out only when the pass will draw it (GL ready, a picture of 2x or more); the marker goes where the
 * model's nearest packet would have; and the arena camera moves only for a battle a native model is in. */
#define _POSIX_C_SOURCE 200809L /* setenv, mkdtemp (scratch.h) */
#include "pc/render/native_model.h"
#include "pc/debug/log.h"
#include "scratch.h"
#include <assert.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int failures;

#define CHECK(condition)                                                              \
    do {                                                                              \
        if (!(condition)) {                                                           \
            fprintf(stderr, "%s:%d: CHECK(%s) failed\n", __FILE__, __LINE__, #condition); \
            failures++;                                                               \
        }                                                                             \
    } while (0)

/* --- what native_model.c reaches outside itself ----------------------------------------------------------------- */
uint32_t D_800FE240;              /* the packet cursor */
uint32_t D_8009AFB4 = 0x00808080u; /* the slot's polygon template colour */
static int test_scale = 2;
int SoftGpu_Scale(void) { return test_scale; }
uint32_t Memories_GteReadControl(unsigned index) { return index == 26 ? 1000u : 0u; }
unsigned Memories_PresentedFrames(void) { return 0; }
int Log_Wanted(LogChannel channel) { (void)channel; return 0; }
void Log_Printf(LogChannel channel, const char *format, ...) { (void)channel; (void)format; }
struct JsonValue;
void Mods_VisitManifests(void (*visit)(const char *, const char *, const struct JsonValue *, void *), void *context)
{
    (void)visit;
    (void)context;
}
int Mods_Setting(const char *id, const char *key, int fallback)
{
    (void)id;
    (void)key;
    return fallback;
}
void Mods_Note(const char *id, const char *format, ...)
{
    (void)id;
    (void)format;
}
int Mods_EntryUsed(const char *id, const struct JsonValue *entry, const char *where)
{
    (void)id;
    (void)entry;
    (void)where;
    return 1;
}

/* --- a one-bone model on disc ------------------------------------------------------------------------------------ */
static void put_float(uint32_t *word, float value)
{
    memcpy(word, &value, sizeof(value));
}

static void write_model(const char *path)
{
    uint32_t w[8 + 16 + 3 * 13 + 3 + 1];
    FILE *file;
    size_t at = 8, i;
    memset(w, 0, sizeof(w));
    memcpy(w, "HDM4", 4);
    w[1] = 3;  /* vertices */
    w[2] = 3;  /* indices */
    w[3] = 1;  /* bones */
    w[4] = 1;  /* texture 1 x 1 */
    w[5] = 1;
    w[8] = (uint32_t)-1; /* the root */
    put_float(&w[9], 1.0f);
    put_float(&w[14], 1.0f);
    put_float(&w[19], 1.0f);
    at += 16;
    for (i = 0; i < 3; i++, at += 13) put_float(&w[at + 9], 1.0f);
    for (i = 0; i < 3; i++) w[at++] = (uint32_t)i;
    file = fopen(path, "wb");
    assert(file);
    assert(fwrite(w, sizeof(w), 1, file) == 1);
    fclose(file);
}

static void set_env(const char *name, const char *value)
{
#ifdef _WIN32
    assert(!_putenv_s(name, value));
#else
    assert(!setenv(name, value, 1));
#endif
}

/* One slot draw as func_800540B4 makes it: Begin, (the drivers), SlotInfo, End. */
static int slot_draw(int model, int slot, int nearest)
{
    NativeSlotInfo info;
    NativeModel_BeginSlot(model, slot);
    if (nearest >= 0 && NativeModel_Suppress) NativeModel_Nearest = (unsigned)nearest; /* what the drivers keep */
    memset(&info, 0, sizeof(info));
    info.slot = slot;
    info.anim_index = 3;
    NativeModel_SlotInfo(&info);
    return NativeModel_EndSlot();
}

static const NativeDraw *last_taken(size_t *count)
{
    const NativeDraw *draws;
    NativeModel_Take();
    draws = NativeModel_Taken(count);
    return *count ? &draws[*count - 1] : NULL;
}

int main(void)
{
    char root[SCRATCH_MAX], path[SCRATCH_MAX + 16];
    const NativeDraw *d;
    size_t count;
    NativeInstance in;

    assert(scratch_dir(root, sizeof(root), "memories-native"));
    snprintf(path, sizeof(path), "%s/m.hdm", root);
    write_model(path);
    set_env("MEMORIES_NATIVE_MODEL", path);
    set_env("MEMORIES_NATIVE_MODEL_ID", "363");
    NativeModel_GlReady = 1;

    /* The game's own slot: key = slot, the battle's card, no fade; its packets left out. */
    NativeModel_SetBattleCards(364, 58);
    CHECK(slot_draw(363, 1, -1) > 0);
    d = last_taken(&count);
    CHECK(count == 1 && d && d->model == 363 && d->mesh_id >= 0 && NativeModel_MeshById(d->mesh_id));
    CHECK(d && d->info.context == NATIVE_CONTEXT_ARENA && d->info.key == 1 && d->info.card == 58);
    CHECK(d && d->info.fade == 0 && d->info.contact_frame == -1 && d->info.anim_index == 3);
    NativeModel_SetBattleCards(0, 0);
    slot_draw(363, 0, -1);
    d = last_taken(&count);
    CHECK(d && d->info.card == 0);

    /* Left out only when the pass will draw it. */
    NativeModel_BeginSlot(363, 0);
    CHECK(NativeModel_Suppress == 1);
    NativeModel_EndSlot();
    CHECK(NativeModel_Suppress == 0);
    test_scale = 1;
    NativeModel_BeginSlot(363, 0);
    CHECK(NativeModel_Suppress == 0);
    NativeModel_EndSlot();
    test_scale = 2;
    NativeModel_GlReady = 0;
    NativeModel_BeginSlot(363, 0);
    CHECK(NativeModel_Suppress == 0);
    NativeModel_EndSlot();
    NativeModel_GlReady = 1;
    NativeModel_BeginSlot(100, 0); /* no model for it: the disc model, captured for nothing */
    CHECK(NativeModel_Suppress == 0 && NativeModel_EndSlot() == 0);
    NativeModel_Take();

    /* A code mod's monster: its context and key, card, fade and contact; used once. */
    memset(&in, 0, sizeof(in));
    in.size = (int32_t)sizeof(in);
    in.context = NATIVE_CONTEXT_FIELD;
    in.key = 7;
    in.card = 364;
    in.fade = 128;
    in.contact_frame = 75;
    NativeModel_SetInstance(&in);
    slot_draw(363, 0, -1);
    d = last_taken(&count);
    CHECK(d && d->info.context == NATIVE_CONTEXT_FIELD && d->info.key == ((NATIVE_CONTEXT_FIELD << 16) | 7));
    CHECK(d && d->info.card == 364 && d->info.fade == 128 && d->info.contact_frame == 75);
    slot_draw(363, 0, -1);
    d = last_taken(&count);
    CHECK(d && d->info.context == NATIVE_CONTEXT_ARENA && d->info.key == 0); /* used once */

    /* A mod built against a smaller struct: the missing fields take their defaults. Bad values are kept in range. */
    memset(&in, 0x7f, sizeof(in));
    in.size = (int32_t)(3 * sizeof(int32_t)); /* size, context, key */
    in.context = NATIVE_CONTEXT_BIG_CARD;
    in.key = 0x12345;
    NativeModel_SetInstance(&in);
    slot_draw(363, 0, -1);
    d = last_taken(&count);
    CHECK(d && d->info.context == NATIVE_CONTEXT_BIG_CARD && d->info.key == ((NATIVE_CONTEXT_BIG_CARD << 16) | 0x2345));
    CHECK(d && d->info.card == 0 && d->info.fade == 0 && d->info.contact_frame == -1);
    memset(&in, 0, sizeof(in));
    in.size = (int32_t)sizeof(in);
    in.context = 99;
    in.fade = 999;
    NativeModel_SetInstance(&in);
    slot_draw(363, 0, -1);
    d = last_taken(&count);
    CHECK(d && d->info.context == NATIVE_CONTEXT_ARENA && d->info.fade == 255);

    /* A measuring draw: nothing captured, nothing left out. */
    in.context = NATIVE_CONTEXT_MEASURE;
    in.fade = 0;
    NativeModel_SetInstance(&in);
    NativeModel_BeginSlot(363, 0);
    CHECK(NativeModel_Suppress == 0);
    CHECK(NativeModel_EndSlot() == 0);
    NativeModel_Take();
    NativeModel_Taken(&count);
    CHECK(count == 0);
    NativeModel_SetInstance(NULL); /* cleared without a draw */

    /* The marker: at the nearest entry the drivers kept, else entry 0. The table and the packet cursor hold 32-bit
     * addresses, so this runs where the buffers' addresses fit in 32 bits (always in the 32-bit build the game is). */
    {
        static uint32_t entries[16], packets[8];
        static uint32_t table[4];
        if ((uintptr_t)entries <= 0xffffffffu && (uintptr_t)packets <= 0xffffffffu) {
            int k, draw;
            for (k = 0; k < 16; k++) entries[k] = 0x00ffffffu;
            table[1] = (uint32_t)(uintptr_t)entries;
            D_800FE240 = (uint32_t)(uintptr_t)packets;
            draw = slot_draw(363, 0, 5);
            NativeModel_Link(table, draw);
            CHECK(entries[5] == ((uint32_t)(uintptr_t)packets & 0x00ffffffu));
            CHECK((packets[1] & 0xffffff00u) == NATIVE_MARKER && entries[0] == 0x00ffffffu);
            D_800FE240 = (uint32_t)(uintptr_t)packets;
            draw = slot_draw(363, 0, -1);
            NativeModel_Link(table, draw);
            CHECK(entries[0] == ((uint32_t)(uintptr_t)packets & 0x00ffffffu));
        } else {
            printf("native_capture_test: the marker's links are not checked here (addresses above 32 bits)\n");
        }
        NativeModel_Take();
    }

    /* The arena camera: pushed out only when a slot's model is drawn natively. */
    CHECK(NativeModel_WillDraw(363, 0) && !NativeModel_WillDraw(100, 0) && !NativeModel_WillDraw(-1, 0));
    CHECK(NativeModel_ArenaCameraFactor(363, -1, 0.0f, 0.0f, 500.0f) > 1.4f);   /* a close shot, pushed to 750 */
    CHECK(NativeModel_ArenaCameraFactor(-1, 363, 0.0f, 0.0f, 2000.0f) == 1.0f); /* the far orbit is left alone */
    CHECK(NativeModel_ArenaCameraFactor(100, -1, 0.0f, 0.0f, 500.0f) == 1.0f);  /* no native model in the battle */
    test_scale = 1;
    CHECK(!NativeModel_WillDraw(363, 0) && NativeModel_ArenaCameraFactor(363, 363, 0.0f, 0.0f, 500.0f) == 1.0f);
    test_scale = 2;

    if (failures) {
        fprintf(stderr, "native_capture_test: %d failed\n", failures);
        return 1;
    }
    printf("native_capture_test: ok\n");
    return 0;
}
