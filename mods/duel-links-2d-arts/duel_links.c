/* Duel Links 2D Arts: a code mod of its own that stands a cutout of a
 * Duel Links-style PNG on each face-up monster of the duel field, always
 * facing the camera, with an optional glow. It needs no other mod (3D
 * Monsters need not be on) and no change to the game: the drawing is the 3D
 * Monsters mod's Card art style (mods/3d-monsters/field_art.c), kept the
 * same on purpose so the two look alike, with the same settings.
 *
 * The PNGs are read by the mod itself, one per card (art_files.h, made by
 * make_art_table.py), instead of through a "cards" entry's "field_art": a
 * "replace" entry resets the card's name, text and plate to the disc's, which
 * wiped the names a player had given their cards (the FM Editor's). This mod
 * touches no card data at all. A card without a PNG shows its own picture.
 *
 * Needs only what the v0.3.0 release exports (SoftGpu_Bank, CardArt_
 * FieldArtFromImage, Cards_BaseId, the duel's globals). */
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
#include "game/ordering_tables.h"
#include "game/duel_display.h"
#include "game/model.h"
#include "game/card_constants.h"
#include "pc/render/soft_gpu.h"
#include "pc/mods/modapi.h"
#include "pc/cards/cards.h"
#include "pc/cards/art.h"
#include "art_files.h"
#include <math.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern MATRIX D_800FE148;      /* GsWSMATRIX: GsSetRefView2's world-screen matrix */

static const MemoriesModHost *host;
static unsigned frame;

/* Cards kept loaded, least recently drawn replaced first (3D Monsters' own
 * CACHE and acquire() explain the reasoning; a bank is bank = index + 1,
 * below SOFT_GPU_BANKS). */
#define CACHE 12

typedef struct {
    int card;      /* one-based card id; 0 when the entry is free */
    unsigned used; /* frame number of the last draw, for replacement */
    int bank;      /* its texture bank in the software GPU */
    int w, h;      /* its texture's size in texels (u and v go to w-1, h-1) */
    int clut_y;    /* where its CLUT sits in the bank, below the pixels */
    int semi;      /* whether its CLUT flags some colours half transparent */
    int level;     /* which size of its texture is loaded (level_heights), -1 for a disc picture */
} Art;

static Art cache[CACHE];
static u8 *record;             /* one card's WA_MRG.MRG art record, read whole */
static int mrg_start = -2;

static void reset(void)
{
    int i;
    for (i = 0; i < CACHE; i++) {
        cache[i].card = 0;
    }
}

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

/* Where the art's pixels and its CLUT sit inside the private bank: any two
 * places that do not overlap, since nothing else ever reads this bank. */
#define PIXELS_X 0
#define PIXELS_Y 0
#define CLUT_X 0
#define CLUT_Y CARD_ART_HEIGHT

static void bank_put(u16 *bank, int x, int y, int w, int h, const u16 *pixels)
{
    int row;
    for (row = 0; row < h; row++) {
        memcpy(bank + (size_t)(y + row) * SOFT_GPU_WIDTH + x, pixels + (size_t)row * w, (size_t)w * 2);
    }
}

/* The mod's own texture for a card (make_art_table.py's art_files.h names the
 * file; prepare_art.py writes it): 256-colour pictures of the same card at
 * several sizes, since the renderer samples a texture point by point and a
 * picture drawn much smaller than it is turns to noise (a 241-texel picture
 * at 40 game pixels, at the usual 1x resolution). The one nearest the
 * on-screen size is loaded. Layout, little-endian: u16 level count, then per
 * level (largest first) u16 width (even), u16 height, 256 CLUT words (BGR555,
 * 0 is clear, bit 15 half transparent) and width x height index bytes.
 * Returns 1 and the level's own pieces, 0 when the card has none or the file
 * is not one. */
#define TEX_LEVELS 4
#define TEX_FILE_MAX 200000
static const int level_heights[TEX_LEVELS] = {241, 120, 60, 30};   /* prepare_art.py's LEVELS */
static unsigned char texture[TEX_FILE_MAX];

/* The smallest size that is not smaller than what is drawn, `rendered` pixels
 * tall: a texel is then never skipped more than about one in two. */
static int level_for(int rendered)
{
    int i;
    for (i = TEX_LEVELS - 1; i > 0; i--) {
        if (level_heights[i] >= rendered) return i;
    }
    return 0;
}

/* A player's PNG for this card in the mod's art/ folder (card id, or its
 * base card's), as the path the engine's loader wants; 0 when there is none. */
static char png_path[1200];
static int custom_png(int card)
{
    int ids[2], i;
    ids[0] = card;
    ids[1] = Cards_BaseId(card);
    for (i = 0; i < 2; i++) {
        FILE *file;
        char relative[64];
        snprintf(relative, sizeof(relative), "art/%d.png", ids[i]);
        snprintf(png_path, sizeof(png_path), "%s/%s", host->directory, relative);
        file = host->open_asset(host, relative);
        if (file) {
            fclose(file);
            return 1;
        }
    }
    return 0;
}

/* One texture file's `level`, parsed out of the file's bytes (the layout
 * above). Returns 1 and the pieces, 0 when the file is missing or not one. */
static int read_texture(const char *path, int card, int level, int *w, int *h, const u16 **clut, const u16 **pixels)
{
    FILE *file = host->open_asset(host, path);
    size_t got, at;
    int count, i;
    if (!file) return 0;
    got = fread(texture, 1, sizeof(texture), file);
    fclose(file);
    count = got >= 2 ? texture[0] | (texture[1] << 8) : 0;
    if (count < 1 || count > TEX_LEVELS) {
        say("card %d: %s is not a texture of this mod\n", card, path);
        return 0;
    }
    if (level >= count) level = count - 1;
    at = 2;
    for (i = 0; i < count; i++) {
        int lw, lh;
        if (at + 4 + 512 > got) break;
        lw = texture[at] | (texture[at + 1] << 8);
        lh = texture[at + 2] | (texture[at + 3] << 8);
        if (lw < 2 || lw > 256 || (lw & 1) || lh < 1 || lh > 256 || at + 4 + 512 + (size_t)lw * lh > got) break;
        if (i == level) {
            *w = lw;
            *h = lh;
            *clut = (const u16 *)(texture + at + 4);
            *pixels = (const u16 *)(texture + at + 4 + 512);
            return 1;
        }
        at += 4 + 512 + (size_t)lw * lh;
    }
    say("card %d: %s is cut short\n", card, path);
    return 0;
}

/* Where a player's own art goes: art/<card id>.tex (from prepare_art.py, the
 * best quality) or art/<card id>.png (any PNG with a clear background, no
 * tool needed). The id is the card's own, so an added card (past the disc's
 * 722) has its own art; failing that its base card's. Both are found before
 * the table of the mod's shipped textures, so they override it; no rebuild. */
static int own_texture(int card, int level, int *w, int *h, const u16 **clut, const u16 **pixels)
{
    char path[1200];
    int base = Cards_BaseId(card), low = 0, high = (int)(sizeof(art_files) / sizeof(art_files[0])) - 1;
    snprintf(path, sizeof(path), "art/%d.tex", card);
    if (read_texture(path, card, level, w, h, clut, pixels)) return 1;
    if (base != card) {
        snprintf(path, sizeof(path), "art/%d.tex", base);
        if (read_texture(path, card, level, w, h, clut, pixels)) return 1;
    }
    if (custom_png(card)) return 0;   /* the player's PNG outranks the shipped texture */
    while (low <= high) {
        int middle = (low + high) / 2;
        if (art_files[middle].card == base) {
            return read_texture(art_files[middle].file, card, level, w, h, clut, pixels);
        }
        if (art_files[middle].card < base) low = middle + 1;
        else high = middle - 1;
    }
    return 0;
}

static int load_art(Art *art, int card, int level)
{
    int base, sectors, w = CARD_ART_WIDTH, h = CARD_ART_HEIGHT;
    u16 *bank;
    const unsigned char *field_art = NULL;
    const u16 *pixels, *clut;

    /* The mod's own texture first, at its own size; failing that a card's
     * "field_art" from another mod, then the card's own picture off the disc,
     * both the game's 102x96. */
    art->level = level;
    if (own_texture(card, level, &w, &h, &clut, &pixels)) {
    } else {
        art->level = -1;
        w = CARD_ART_WIDTH;
        h = CARD_ART_HEIGHT;
        if (custom_png(card) && (record || (record = malloc(ART_SECTORS * SECTOR)))) {
            char why[200];
            if (CardArt_FieldArtFromImage(png_path, record, why, sizeof(why))) {
                field_art = record;
            } else {
                say("card %d: %s: %s\n", card, png_path, why);
            }
        }
        if (!field_art) field_art = Cards_FieldArtRecord(card);
        if (!field_art) {
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
            /* A card past the disc's 722 has no record of its own; it stands
             * as the retail card it is a copy of, exactly as func_80029164
             * reads it for the card-detail panel. */
            base = Cards_BaseId(card);
            sectors = host->disc_read(host, mrg_start + (base - 1) * ART_SECTORS + CARD_COUNT, ART_SECTORS, record);
            if (sectors != ART_SECTORS) {
                say("card %d: read %d of %d sectors\n", card, sectors, ART_SECTORS);
                return 0;
            }
            /* A mod's own "art" artwork over the base's, exactly as the
             * card-detail panel gets it (func_800289BC). */
            Cards_PatchArtRecord(card, record);
            field_art = record;
        }
        pixels = (const u16 *)(field_art + CARD_ART_PIXELS);
        clut = (const u16 *)(field_art + CARD_ART_CLUT);
    }

    bank = SoftGpu_Bank(art->bank);
    if (!bank) {
        say("no bank %d\n", art->bank);
        return 0;
    }
    bank_put(bank, PIXELS_X, PIXELS_Y, w / 2, h, pixels);
    bank_put(bank, CLUT_X, h, 256, 1, clut);
    art->w = w;
    art->h = h;
    art->clut_y = h;
    /* Only the mod's own textures flag colours half transparent on purpose:
     * a disc picture's CLUT may carry the bit on every colour. */
    art->semi = 0;
    if (field_art == NULL) {
        int i;
        for (i = 1; i < 256; i++) {
            if (clut[i] & 0x8000) art->semi = 1;
        }
    }
    art->card = card;
    return 1;
}

/* `rendered` is how many pixels tall the cutout is drawn, at the internal
 * resolution. A cached card keeps its size while that stays a fair match
 * (no more than about 2.3x too big, never much too small), so the camera
 * moving does not reload it every frame. */
static Art *acquire(int card, int rendered)
{
    Art *art = NULL;
    int i, level = level_for(rendered);
    for (i = 0; i < CACHE; i++) {
        if (cache[i].card == card) {
            Art *held = &cache[i];
            if (held->level >= 0 && held->level != level) {
                int current = level_heights[held->level];
                if (current * 100 >= rendered * 85 && current * 100 <= rendered * 230) level = held->level;
            }
            if (held->level < 0 || held->level == level) {
                held->used = frame;
                return held;
            }
            art = held;   /* the same card, at the size it needs now */
            break;
        }
    }
    if (!art) {
        for (i = 0; i < CACHE; i++) {
            if (!cache[i].card) {
                art = &cache[i];
                break;
            }
            if (!art || cache[i].used < art->used) {
                art = &cache[i];
            }
        }
    }
    art->bank = (int)(art - cache) + 1;
    art->card = 0;
    if (!load_art(art, card, level)) {
        return NULL;
    }
    art->used = frame;
    return art;
}

/* A world point to screen, under the frame's own world-screen matrix, as
 * func_80015EF4 projects a field card's flattened ground sprite. Returns
 * RotTransPers' own depth: SZ already shifted the way a model's is (its own
 * comment, "a quarter of its distance"), ready for GsSortPoly. */
static int project(int x, int y, int z, int *sx, int *sy)
{
    SVECTOR v;
    PSXLONG sxy, p, flag, depth;   /* the Psy-Q long: 32 bits on every target */
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
#define DEFAULT_PIXELS 40

static int fit_height(void)
{
    int target = tunable("size", DEFAULT_PIXELS), height = HEIGHT_DEFAULT, attempt, got = 0;
    for (attempt = 0; attempt < 5; attempt++) {
        int sx, base_sy, top_sy, wanted;
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
    /* Left in deliberately, gated on the same mods log the rest of this file
     * uses: cheap to check against next time the size looks off. */
    say("fit_height: target %d px, got %d px, height %d after %d attempt(s)\n", target, got, height, attempt + 1);
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

/* A pulsing glow diffusing outward from the cutout's own rectangle ("glow"
 * setting; on by default): one continuous, soft gradient -- bright right at
 * the card's edge, fading smoothly out with distance, rounded at the
 * corners rather than four strips meeting at a seam (which is what the
 * first attempt at this did: visible double-bright overlaps at the
 * corners, and banding read as "on/off" rather than a smooth breathing
 * glow). A bank of its own past the per-card cache (CACHE banks 1..CACHE,
 * so GLOW_BANK is always free) holds one square texture, GLOW_SIZE across,
 * generated once: at each texel, in coordinates normalised to [-1, 1]
 * across the texture, INNER_HALF is the half-width of a middle square left
 * untouched (it sits under the cutout itself, which draws over it, so its
 * exact brightness there does not matter); outside it, the texel's index is
 * the Euclidean distance to the middle square's nearest edge or corner,
 * scaled so it reaches 0 -- fully transparent, the same hardware rule as
 * the earlier attempts relied on -- at the texture's own edge along x or y,
 * and clamps there before the actual corners, which is what rounds them off
 * rather than squaring them like the first attempt's strips did. A
 * 256-entry CLUT turns every other index into that much white, STP set
 * (BGR555's bit 15, the semi-transparency flag the renderer reads alongside
 * the primitive's own setSemiTrans -- both must be on, or it draws opaque,
 * gl_picture.c). The glow's own colour is entirely the primitive's
 * r0/g0/b0 modulation (setting glow_color), scaled each frame by a sine
 * wave (glow_period, frames per full pulse) between a floor and full
 * brightness -- never down to fully off, which is what read as "on/off"
 * rather than a breathing pulse -- for the "shining" look; abr 1 (GetTPage's
 * second argument) is the additive blend equation, so the glow brightens
 * whatever is under it instead of covering it. One quad, its middle square
 * scaled to match the cutout's own rectangle exactly (so the diffusing part
 * sits outside it) and its overall size then scaled again by glow_reach, at
 * the cutout's own depth so it sorts with it. */
#define GLOW_BANK (CACHE + 1)
#define GLOW_SIZE 48
#define GLOW_PIXELS_X 0
#define GLOW_PIXELS_Y 0
#define GLOW_CLUT_X 0
#define GLOW_CLUT_Y GLOW_SIZE
#define GLOW_INNER_HALF 0.30 /* the middle square's half-width, normalised */
#define GLOW_REACH_DEFAULT 50
#define GLOW_PERIOD_DEFAULT 90
#define GLOW_FLOOR 0.35 /* the pulse's dimmest point: never fully off */
/* The "glow_color" choices, in mod.json's order; the first is the colour the
 * glow always had (255, 255, 90). */
static const unsigned char glow_colors[][3] = {
    {255, 255, 90}, {255, 200, 40}, {255, 255, 255}, {255, 60, 60}, {255, 140, 30},
    {80, 255, 80}, {60, 230, 255}, {70, 110, 255}, {190, 80, 255}, {255, 110, 200},
};
#define GLOW_COLORS ((int)(sizeof(glow_colors) / sizeof(glow_colors[0])))

static int glow_ready;

static void glow_init(void)
{
    u16 *bank;
    u16 pixels[GLOW_SIZE * GLOW_SIZE / 2], clut[256];
    double middle = (GLOW_SIZE - 1) / 2.0, max_distance = 1.0 - GLOW_INNER_HALF;
    int x, y, i;

    if (glow_ready) return;
    bank = SoftGpu_Bank(GLOW_BANK);
    if (!bank) return;

    for (y = 0; y < GLOW_SIZE; y++) {
        double ny = (y - middle) / middle, dy = fabs(ny) > GLOW_INNER_HALF ? fabs(ny) - GLOW_INNER_HALF : 0.0;
        for (x = 0; x < GLOW_SIZE; x++) {
            double nx = (x - middle) / middle, dx = fabs(nx) > GLOW_INNER_HALF ? fabs(nx) - GLOW_INNER_HALF : 0.0;
            double distance = sqrt(dx * dx + dy * dy) / max_distance;
            /* Squared falloff, softer near the card and steeper further
             * out, than a linear ramp would read. */
            double level = distance >= 1.0 ? 0.0 : (1.0 - distance) * (1.0 - distance);
            int index = (int)(level * 255.0 + 0.5), word = x / 2;
            u16 texel = (u16)(index & 0xff) << ((x & 1) * 8);
            if (x & 1) pixels[y * (GLOW_SIZE / 2) + word] |= texel;
            else pixels[y * (GLOW_SIZE / 2) + word] = texel;
        }
    }
    clut[0] = 0; /* never sampled: index 0 is always transparent */
    for (i = 1; i < 256; i++) {
        int component = i * 31 / 255;
        clut[i] = (u16)(0x8000 | (component << 10) | (component << 5) | component); /* white, STP set */
    }
    bank_put(bank, GLOW_PIXELS_X, GLOW_PIXELS_Y, GLOW_SIZE / 2, GLOW_SIZE, pixels);
    bank_put(bank, GLOW_CLUT_X, GLOW_CLUT_Y, 256, 1, clut);
    glow_ready = 1;
}

static void draw_glow(GsOT *table, unsigned short depth, int cx, int cy, int width_px, int height_px)
{
    POLY_FT4 prim;
    int reach, period, phase, half_w, half_h, r, g, b, choice;
    double level;

    if (!tunable("glow", 0)) return;
    reach = tunable("glow_reach", GLOW_REACH_DEFAULT);
    period = tunable("glow_period", GLOW_PERIOD_DEFAULT);
    if (reach < 1 || period < 1) return;
    glow_init();
    if (!glow_ready) return;

    /* The quad's half-size such that its middle GLOW_INNER_HALF fraction
     * matches the cutout's own half-size exactly, then scaled again by the
     * user's reach. */
    half_w = (int)(width_px / (2.0 * GLOW_INNER_HALF) * reach / 100.0);
    half_h = (int)(height_px / (2.0 * GLOW_INNER_HALF) * reach / 100.0);
    if (half_w < 1 || half_h < 1) return;

    phase = (int)(frame % (unsigned)period);
    level = GLOW_FLOOR + (1.0 - GLOW_FLOOR) * (sin(2.0 * 3.14159265358979323846 * phase / period) * 0.5 + 0.5);
    choice = tunable("glow_color", 0);
    if (choice < 0 || choice >= GLOW_COLORS) choice = 0;
    r = (int)(glow_colors[choice][0] * level);
    g = (int)(glow_colors[choice][1] * level);
    b = (int)(glow_colors[choice][2] * level);

    /* Zeroed first: the port reads pad2 as the bank fade (SOFT_GPU_FADE). */
    memset(&prim, 0, sizeof(prim));
    setPolyFT4(&prim);
    setSemiTrans(&prim, 1);
    prim.r0 = (u8)r;
    prim.g0 = (u8)g;
    prim.b0 = (u8)b;
    prim.tpage = GetTPage(1, 1, GLOW_PIXELS_X, GLOW_PIXELS_Y) | (u16)(GLOW_BANK << 11);
    prim.clut = GetClut(GLOW_CLUT_X, GLOW_CLUT_Y);
    prim.x0 = (short)(cx - half_w);
    prim.y0 = (short)(cy - half_h);
    prim.u0 = 0;
    prim.v0 = 0;
    prim.x1 = (short)(cx + half_w);
    prim.y1 = (short)(cy - half_h);
    prim.u1 = GLOW_SIZE - 1;
    prim.v1 = 0;
    prim.x2 = (short)(cx - half_w);
    prim.y2 = (short)(cy + half_h);
    prim.u2 = 0;
    prim.v2 = GLOW_SIZE - 1;
    prim.x3 = (short)(cx + half_w);
    prim.y3 = (short)(cy + half_h);
    prim.u3 = GLOW_SIZE - 1;
    prim.v3 = GLOW_SIZE - 1;
    GsSortPoly(&prim, table, depth);
}

static void draw_one(int index, int world_height)
{
    DuelCardRecord *card = &D_801A7AD8[index];
    Art *art;
    int id = card->card_id;
    int wx, wz, base_sx, base_sy, top_sx, top_sy, depth;
    int height_px, width_px, cx;
    POLY_FT4 prim;
    GsOT *table;

    if (!(card->flags & DUEL_CARD_FLAG_OCCUPIED) || (card->flags & DUEL_CARD_FLAG_FACE_DOWN) || id <= 0 ||
        ((gDuel_adwCardStats[id - 1] >> 0x1A) & 0x1F) >= 0x14) {
        return; /* empty, face down, or a magic or trap card */
    }
    wx = D_800908A0[index].x;
    wz = D_800908A0[index].y;
    depth = project(wx, -lift(), wz, &base_sx, &base_sy);
    project(wx, -lift() - world_height, wz, &top_sx, &top_sy);

    height_px = base_sy - top_sy;
    if (height_px <= 0) {
        return; /* behind the camera, or degenerate */
    }
    art = acquire(id, height_px * SoftGpu_Scale());
    if (!art) {
        return;
    }
    width_px = height_px * CARD_ART_WIDTH / CARD_ART_HEIGHT; /* the shape every picture is fitted to (prepare_art.py) */
    cx = (base_sx + top_sx) / 2;

    /* A gentle rise and fall ("bob" setting: amplitude in game pixels, 0 is
     * off; "bob_period": frames per cycle), each zone a little out of step
     * with the others so the monsters do not move as one. */
    {
        int amplitude = tunable("bob", 0), period = tunable("bob_period", 120);
        if (amplitude > 0 && period > 0) {
            int shift = (int)floor(amplitude * sin(2.0 * 3.14159265358979323846 * (double)((frame + (unsigned)index * 17) % (unsigned)period) / period) + 0.5);
            top_sy += shift;
            base_sy += shift;
        }
    }

    /* Zeroed first: the port reads pad2 as the bank fade (SOFT_GPU_FADE). */
    memset(&prim, 0, sizeof(prim));
    setPolyFT4(&prim);
    /* Half transparent only for the texels whose palette colour says so (the
     * PS1 blends a texel with its bit 15 set, and draws the rest as they are). */
    if (art->semi) setSemiTrans(&prim, 1);
    prim.r0 = prim.g0 = prim.b0 = 0x80;
    prim.tpage = GetTPage(1, 0, PIXELS_X, PIXELS_Y) | (u16)(art->bank << 11);
    prim.clut = GetClut(CLUT_X, art->clut_y);
    prim.x0 = (short)(cx - width_px / 2);
    prim.y0 = (short)top_sy;
    prim.u0 = 0;
    prim.v0 = 0;
    prim.x1 = (short)(cx + width_px / 2);
    prim.y1 = (short)top_sy;
    prim.u1 = (u8)(art->w - 1);
    prim.v1 = 0;
    prim.x2 = (short)(cx - width_px / 2);
    prim.y2 = (short)base_sy;
    prim.u2 = 0;
    prim.v2 = (u8)(art->h - 1);
    prim.x3 = (short)(cx + width_px / 2);
    prim.y3 = (short)base_sy;
    prim.u3 = (u8)(art->w - 1);
    prim.v3 = (u8)(art->h - 1);

    /* D_800E9D90[0] (what this used to target) is a real, but tiny, table in
     * this state -- 4 depth slots, confirmed live (table_length 2) -- meant
     * for something else entirely; every cutout's depth saturated at its
     * ceiling regardless of position, so draw order came down to insertion
     * order, not depth, against anything sharing that slot. D_800E9D90[2] is
     * what func_80015EF4 actually sorts a field card's own upright quad into,
     * and what the 3D Monsters mod's field-standing draw_monster() uses too
     * (its own D_800E9D98[0]) -- a real-sized table shared with the field's
     * own geometry, so a cutout sorts correctly against the card under it. */
    table = D_800E9D90[2];
    /* RotTransPers's raw depth is at a model's own native resolution, a
     * quarter as fine as this table's card scale (func_80015EF4's own
     * comment on a model's primitives); the 3D Monsters mod's sort_monster
     * divides its own raw "nearest" the same single step, `nearest / 4`,
     * before using it here. */
    depth = depth / 4 - tunable("depth", DEPTH_STEPS);
    depth = depth < 0 ? 0 : depth >= (1 << table->length) ? (1 << table->length) - 1 : depth;
    GsSortPoly(&prim, table, (unsigned short)depth);
    draw_glow(table, (unsigned short)depth, cx, (top_sy + base_sy) / 2, width_px, height_px);
}

static void draw_frame(void)
{
    int side, zone, world_height;

    if (!duel_field_up()) {
        return;
    }
    frame++;

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
            draw_one(SIDE_ZONE(side, zone), world_height);
        }
    }
    SetGeomOffset(0, 0);
}

int MemoriesModInit(const MemoriesModHost *from, MemoriesMod *mod)
{
    host = from;
    mod->api = MEMORIES_MOD_API;
    mod->frame = draw_frame;
    mod->reset = reset;
    return 1;
}
