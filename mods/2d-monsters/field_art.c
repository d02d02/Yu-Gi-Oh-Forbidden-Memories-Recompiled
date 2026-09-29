/* The 2D Monsters mod (mod.json beside this file; notes/modding.md): where
 * the 3D Monsters mod stands a battle model on a face-up field card, this
 * stands an enlarged cutout of the card's own art instead, floating just
 * above it, always facing the camera.
 *
 * The art comes from WA_MRG.MRG the same way the card-detail panel and the
 * Library read it (func_800289BC, Cards_PatchArtRecord), and is uploaded to
 * VRAM the same way that panel shows it: a plain LoadImage, not a private
 * software-GPU bank. That is deliberate, not incidental: a texture pack's HD
 * replacement (notes/modding.md, "Texture packs") only ever applies to a
 * primitive sampling real VRAM (soft_gpu.c's shadow_on is gated on
 * `texture_source == vram`; a bank never qualifies -- the same reason the HD
 * model-texture item, progress.md item 7c, is blocked). Uploading for real,
 * the way retail's own big-card view does, means an installed HD pack's own
 * card art picks this cutout up automatically: no reading of the pack's
 * files, no engine change, nothing kept past the upload itself -- each
 * zone's art and CLUT are re-uploaded every frame (ten uploads of a few KB
 * each, cheap next to a model's textures), never cached.
 *
 * Where they land is VRAM already established safe to write while this mod
 * draws: see VRAM_ART_X/VRAM_ART_Y/VRAM_CLUT_X/VRAM_CLUT_Y below.
 *
 * Unlike a model, a cutout has no size of its own to measure: every card's
 * art is the same 102x96 record, so one world-space height serves every
 * zone, and perspective alone makes a farther card's cutout smaller -- the
 * fitting loop below (fit_height) finds that height once a frame, the same
 * way the 3D Monsters mod's fit() finds a model's scale, but by projecting
 * two points instead of measuring drawn packets.
 *
 * Drawing is a single POLY_FT4 per face-up monster, its four corners placed
 * in screen space from two world points (the card's own field position, and
 * that position lifted by the fitted height) run through RotTransPers under
 * the frame's own world-screen matrix (D_800FE148, GsSetRefView2's own),
 * exactly as func_80015EF4 projects a field card's ground sprite. The same
 * call's returned depth is at RotTransPers' own native resolution, a quarter
 * as fine as the card scale func_80015EF4 sorts a field card's own upright
 * quad at (its own comment on a model's primitives); draw_one() divides it
 * down the same single step the 3D Monsters mod's sort_monster does
 * (`nearest / 4`) before it sorts the cutout into D_800E9D90[2] -- the same
 * table func_80015EF4 sorts that upright quad into, and the one the 3D
 * Monsters mod's own field-standing draw_monster() uses too (as
 * D_800E9D98[0], its own comment's name for the same table): shared with the
 * field's own card geometry, not borrowed for being unused, so a cutout
 * sorts correctly against the card it stands on and against other cutouts. */
#include "types.h"
#include "psyq/libgte.h"
#include "psyq/libgpu.h"
#include "psyq/libgs.h"
#include "ygo_types.h"
#include "game/duel_card.h"
#include "game/duel_card_layout.h"
#define DUEL_SCREEN_TABLES_TYPED_POSITIONS
#include "game/duel_screen_tables.h"
#include "game/view_state.h"
#include "game/main_services.h"
#include "game/duel_display.h"
#include "game/model.h"
#include "game/card_constants.h"
#include "pc/mods/modapi.h"
#include "pc/cards/cards.h"
#include "pc/cards/art.h"
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern GsOT *D_800E9D90[4];    /* the four ordering tables of the frame */
extern MATRIX D_800FE148;      /* GsWSMATRIX: GsSetRefView2's world-screen matrix */

static const MemoriesModHost *host;

static void say(const char *format, ...)
{
    char message[512];
    va_list arguments;
    if (!host->log_enabled(host)) return;
    va_start(arguments, format);
    vsnprintf(message, sizeof(message), format, arguments);
    va_end(arguments);
    host->log(host, "%s", message);
}

static int tunable(const char *key, int fallback)
{
    return host->setting(host, key, fallback);
}

#define SECTOR 2048
#define ART_SECTORS 7

static u8 *record;             /* one card's WA_MRG.MRG art record, read whole */
static int mrg_start = -2;

static int read_art(int card)
{
    int base, sectors;

    if (mrg_start == -2) {
        mrg_start = host->disc_file_start(host, "\\DATA\\WA_MRG.MRG;1");
        say("WA_MRG.MRG starts at sector %d\n", mrg_start);
    }
    if (mrg_start < 0) {
        return 0;
    }
    if (!record && !(record = malloc(ART_SECTORS * SECTOR))) {
        return 0;
    }
    /* A card past the disc's 722 has no record of its own; it stands as the
     * retail card it is a copy of, exactly as func_80029164 reads it for the
     * card-detail panel. */
    base = Cards_BaseId(card);
    sectors = host->disc_read(host, mrg_start + (base - 1) * ART_SECTORS + CARD_COUNT, ART_SECTORS, record);
    if (sectors != ART_SECTORS) {
        say("card %d: read %d of %d sectors\n", card, sectors, ART_SECTORS);
        return 0;
    }
    /* A mod's own artwork over the base's, exactly as the card-detail panel
     * gets it (func_800289BC). */
    Cards_PatchArtRecord(card, record);
    return 1;
}

/* Every zone's full card art and CLUT fit inside the exact VRAM footprint the
 * 3D Monsters mod already established safe to write while duel_field_up():
 * no 3D model is ever shown then, and that mod is mutually exclusive with
 * this one (mod.json's "conflicts"), so its own reasoning ("the model area of
 * VRAM for slot 0", field_models.c: BLOCK_X/BLOCK_Y/BLOCK_W/BLOCK_H, x
 * 0-0x100 and, "slot 1's block sits 0x100 to the next", x 0x100-0x200, y
 * 0xF0-0x200) carries over unchanged.
 *
 * A texture page's Y origin is only ever 0 or 256 in this software GPU
 * (gpu.page_y: bit 4 of the tpage word, times 256; soft_gpu.c) -- a card
 * placed at y 0xF0 (240) would cross that boundary partway through its 96
 * rows and be unsampleable by a single primitive, so the art starts at y
 * 0x100 (256) instead, clear of it, one row of five zones per side. The
 * CLUTs have no such restriction (clut_y is a free 9-bit field, soft_gpu.c)
 * and live in the 16-row sliver between 0xF0 and 0x100 that the art can't
 * use -- the same x range as the art's own columns, never overlapping
 * because the rows differ. */
#define VRAM_ART_X(zone) ((zone) * 64)
#define VRAM_ART_Y(side) (0x100 + (side) * CARD_ART_HEIGHT)
#define VRAM_CLUT_X 0
#define VRAM_CLUT_Y(slot) (0xF0 + (slot))

static void upload_art(int slot, int side, int zone)
{
    RECT rect;

    rect.x = (short)VRAM_ART_X(zone);
    rect.y = (short)VRAM_ART_Y(side);
    rect.w = CARD_ART_WIDTH / 2;
    rect.h = CARD_ART_HEIGHT;
    LoadImage(&rect, (u32 *)(record + CARD_ART_PIXELS));

    rect.x = VRAM_CLUT_X;
    rect.y = (short)VRAM_CLUT_Y(slot);
    rect.w = 256;
    rect.h = 1;
    LoadImage(&rect, (u32 *)(record + CARD_ART_CLUT));
}

/* A world point to screen, under the frame's own world-screen matrix, as
 * func_80015EF4 projects a field card's flattened ground sprite. Returns
 * RotTransPers' own depth: SZ already shifted the way a model's is (its own
 * comment, "a quarter of its distance"), ready for GsSortPoly. */
static int project(int x, int y, int z, int *sx, int *sy)
{
    SVECTOR v;
    long sxy, p, flag, depth;
    v.vx = (short)x;
    v.vy = (short)y;
    v.vz = (short)z;
    v.pad = 0;
    GsSetLsMatrix(&D_800FE148);
    depth = RotTransPers(&v, &sxy, &p, &flag);
    *sx = (short)((u32)sxy & 0xFFFF);
    *sy = (short)(((u32)sxy >> 16) & 0xFFFF);
    return (int)depth;
}

#define LIFT_PIXELS 8
#define LIFT_UNITS_PER_PIXEL 2
static int lift(void)
{
    return tunable("lift", LIFT_PIXELS * LIFT_UNITS_PER_PIXEL);
}

/* The world-space height that projects to `pixels` game pixels tall at the
 * middle of the field: found the way the 3D Monsters mod's fit() finds a
 * model's scale, by projecting instead of measuring drawn packets, because
 * every card's cutout is the same 102x96 record and needs the same height.
 * DEFAULT_PIXELS matches the 3D Monsters mod's own TALL_PIXELS: the same
 * "about this tall in the middle of the field" target its models are fit to,
 * so a cutout should read at the same scale a battle model would. */
#define MIDDLE_X 0
#define MIDDLE_Z 0
#define HEIGHT_DEFAULT 700
/* A floor only against a degenerate `got` (a near-zero or negative pixel
 * delta), not a realistic lower bound on the answer: live logging under the
 * field's actual camera (target 40, DEFAULT_PIXELS's old value) found 128
 * world units already project to 66 px, well past the target, with the loop
 * wanting to settle around 77. A HEIGHT_SMALLEST of 128 -- copied by analogy
 * from the 3D Monsters mod's SCALE_SMALLEST, a fixed-point scale *fraction*
 * (of MODEL_FIXED_ONE), not a raw world-unit height, so the same number
 * means something else entirely here -- clamped every attempt back up to
 * itself, so the loop could never reach the smaller height it kept computing
 * and every cutout was stuck oversized. */
#define HEIGHT_SMALLEST 16
#define HEIGHT_LARGEST 8192
#define DEFAULT_PIXELS 32

static int fit_height(void)
{
    int target = tunable("pixels", DEFAULT_PIXELS), height = HEIGHT_DEFAULT, attempt;
    for (attempt = 0; attempt < 5; attempt++) {
        int sx, base_sy, top_sy, got, wanted;
        project(MIDDLE_X, -lift(), MIDDLE_Z, &sx, &base_sy);
        project(MIDDLE_X, -lift() - height, MIDDLE_Z, &sx, &top_sy);
        got = base_sy - top_sy;
        if (got <= 0) {
            break;
        }
        wanted = height * target / got;
        if (wanted > height * 15 / 16 && wanted < height * 17 / 16) {
            break;
        }
        height = wanted < HEIGHT_SMALLEST ? HEIGHT_SMALLEST : wanted > HEIGHT_LARGEST ? HEIGHT_LARGEST : wanted;
    }
    return height;
}

/* The duel field seen from above is the one place this draws (field_models.c's
 * own duel_field_up() explains why: the overview camera). */
#define FIELD_PITCH 512

static int duel_field_up(void)
{
    return D_800E9DB0[3] == Duel_DrawFieldCards && D_800F2C40[2].field_E1F != 0 &&
           D_800F2848.field_04 < tunable("pitch", FIELD_PITCH);
}

#define MONSTER_ZONES 5
#define SIDE_ZONE(side, zone) ((side) ? 20 + (zone) : 5 + (zone))
#define DEPTH_STEPS 3

static void draw_one(int side, int zone, int world_height)
{
    int index = SIDE_ZONE(side, zone);
    int slot = side * MONSTER_ZONES + zone;
    DuelCardRecord *card = &D_801A7AD8[index];
    int id = card->card_id;
    int wx, wz, base_sx, base_sy, top_sx, top_sy, depth;
    int height_px, width_px, cx;
    POLY_FT4 prim;
    GsOT *table;

    if (!(card->flags & DUEL_CARD_FLAG_OCCUPIED) || (card->flags & DUEL_CARD_FLAG_FACE_DOWN) || id <= 0 ||
        ((gDuel_adwCardStats[id - 1] >> 0x1A) & 0x1F) >= 0x14) {
        return; /* empty, face down, or a magic or trap card */
    }
    if (!read_art(id)) {
        return;
    }
    upload_art(slot, side, zone);

    wx = D_800908A0[index].x;
    wz = D_800908A0[index].y;
    depth = project(wx, -lift(), wz, &base_sx, &base_sy);
    project(wx, -lift() - world_height, wz, &top_sx, &top_sy);

    height_px = base_sy - top_sy;
    if (height_px <= 0) {
        return; /* behind the camera, or degenerate */
    }
    width_px = height_px * CARD_ART_WIDTH / CARD_ART_HEIGHT;
    cx = (base_sx + top_sx) / 2;

    setPolyFT4(&prim);
    prim.r0 = prim.g0 = prim.b0 = 0x80;
    prim.tpage = GetTPage(1, 0, VRAM_ART_X(zone), VRAM_ART_Y(side));
    prim.clut = GetClut(VRAM_CLUT_X, VRAM_CLUT_Y(slot));
    prim.x0 = (short)(cx - width_px / 2);
    prim.y0 = (short)top_sy;
    prim.u0 = 0;
    prim.v0 = 0;
    prim.x1 = (short)(cx + width_px / 2);
    prim.y1 = (short)top_sy;
    prim.u1 = CARD_ART_WIDTH - 1;
    prim.v1 = 0;
    prim.x2 = (short)(cx - width_px / 2);
    prim.y2 = (short)base_sy;
    prim.u2 = 0;
    prim.v2 = CARD_ART_HEIGHT - 1;
    prim.x3 = (short)(cx + width_px / 2);
    prim.y3 = (short)base_sy;
    prim.u3 = CARD_ART_WIDTH - 1;
    prim.v3 = CARD_ART_HEIGHT - 1;

    /* D_800E9D90[0] is a real, but tiny, table in this state -- 4 depth
     * slots, confirmed live (table_length 2) -- meant for something else
     * entirely; every cutout's depth would saturate at its ceiling regardless
     * of position, so draw order would come down to insertion order, not
     * depth, against anything sharing that slot. D_800E9D90[2] is what
     * func_80015EF4 actually sorts a field card's own upright quad into, and
     * what the 3D Monsters mod's field-standing draw_monster() uses too (its
     * own D_800E9D98[0]) -- a real-sized table shared with the field's own
     * geometry, so a cutout sorts correctly against the card under it. */
    table = D_800E9D90[2];
    /* RotTransPers's raw depth is at a model's own native resolution, a
     * quarter as fine as this table's card scale (func_80015EF4's own
     * comment on a model's primitives); the 3D Monsters mod's sort_monster
     * divides its own raw "nearest" the same single step, `nearest / 4`,
     * before using it here. */
    depth = depth / 4 - tunable("depth", DEPTH_STEPS);
    depth = depth < 0 ? 0 : depth >= (1 << table->length) ? (1 << table->length) - 1 : depth;
    GsSortPoly(&prim, table, (unsigned short)depth);
}

static void draw_frame(void)
{
    int side, zone, world_height;

    if (!duel_field_up()) {
        return;
    }

    /* The projection the duel draws its own field with, exactly as
     * Duel_DrawFieldCards and the 3D Monsters mod's draw_frame set it up.
     * fit_height()'s own project() calls need this in place first: it
     * calibrates world_height by measuring screen pixels under this same
     * matrix/scale, so it has to run under the field's camera, not whatever
     * was left over from the previous draw call this frame. */
    GsSetRefView2(&D_800F2848.view);
    SetGeomScreen(D_800F2848.projection);
    SetGeomOffset(0xA0, 0x6C);

    world_height = fit_height();

    for (side = 0; side < 2; side++) {
        for (zone = 0; zone < MONSTER_ZONES; zone++) {
            draw_one(side, zone, world_height);
        }
    }
    SetGeomOffset(0, 0);
}

int MemoriesModInit(const MemoriesModHost *from, MemoriesMod *mod)
{
    if (from->api < 2) {
        return 0; /* disc_read and disc_file_start arrived in mod API 2 */
    }
    host = from;
    mod->api = MEMORIES_MOD_API;
    mod->frame = draw_frame;
    return 1;
}
