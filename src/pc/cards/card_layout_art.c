/* See card_layout_art.h. Decode-once-and-cache + store-into-bank, the same
 * shape as star_icons.c's make()/store()/Stars_IconCell() trio -- the
 * difference is colour depth: guardian star icons and glyphs are 4 bits a
 * texel (packed four to a VRAM word, tpage depth field 0), these assets are
 * CardArt_IndexedImageFromMemory's own 8-bit-a-texel output (up to 255
 * colours plus transparent 0), packed two to a word, tpage depth field 1
 * (getTPage's own encoding, psyq/libgpu.h) -- there is no existing 8bpp
 * bank user in this codebase to copy, so that packing and tpage math are
 * derived here from the PS1's own hardware layout, not guessed.
 *
 * All of CARD_LAYOUT_ART_COUNT's assets share one bank (SOFT_GPU_WIDTH x
 * SOFT_GPU_HEIGHT = 1024 x 512 texels, 16-bit words -- plenty for a
 * handful of small UI textures): each gets its own fixed y-origin in the
 * table below, high enough above the next to leave room for its own
 * pixel rows plus one more for its clut, and decodes/uploads independently
 * the first time something asks for it. */
#include "card_layout_art.h"
#include "art.h"
#include "pc/render/soft_gpu.h"
#include "../assets/card_layout_plaque_png.h"
#include "../assets/card_layout_row_png.h"
#include <stdlib.h>
#include <string.h>

#define ASSET_BANK 13   /* 1-12 the 3D Monsters mod, 14 star icons, 15 glyphs, 0 is real VRAM */

typedef struct {
    const unsigned char *png;
    unsigned long png_size;
    int w, h;       /* stored (decoded) size -- u8-safe, POLY_GT4's u/v are u8, so <= 255 either way */
    int bank_y;     /* this asset's own row origin within the shared bank; bank_y + h is its own clut row */
    unsigned char made;   /* 0 not yet, 1 made, 2 failed */
} Asset;

/* Both source PNGs (src/pc/assets/) are bigger than their stored size here:
 * halved from 358x142 and 919x348, the largest even multiple that still
 * fits a u8 UV coordinate (<= 255 either axis) with headroom at Internal
 * 2x/4x left over -- not resampled all the way down to the tiny on-screen
 * boxes themselves (card_layout.c's CARD_LAYOUT_PLAQUE_W/H, ROW_W/H). */
static Asset assets[CARD_LAYOUT_ART_COUNT] = {
    [CARD_LAYOUT_ART_PLAQUE] = { card_layout_plaque_png, sizeof(card_layout_plaque_png), 179, 71, 0, 0 },
    [CARD_LAYOUT_ART_ROW]    = { card_layout_row_png,    sizeof(card_layout_row_png),    230, 87, 100, 0 },
};

static int make(Asset *a, uint16_t *bank)
{
    unsigned char *indices = malloc((size_t)a->w * a->h);
    unsigned short clut[256];
    int x, y;
    if (!indices) return 0;
    if (!CardArt_IndexedImageFromMemory(a->png, a->png_size, a->w, a->h, indices, clut)) {
        free(indices);
        return 0;
    }
    for (y = 0; y < a->h; y++) {
        for (x = 0; x < a->w; x += 2) {
            unsigned char lo = indices[y * a->w + x];
            unsigned char hi = x + 1 < a->w ? indices[y * a->w + x + 1] : 0;
            bank[(a->bank_y + y) * SOFT_GPU_WIDTH + x / 2] = (uint16_t)(lo | (hi << 8));
        }
    }
    memcpy(&bank[(a->bank_y + a->h) * SOFT_GPU_WIDTH], clut, 256 * sizeof(uint16_t));
    free(indices);
    return 1;
}

int CardLayoutArt_Cell(CardLayoutArtAsset asset, int *tpage, int *u, int *v, int *clut, int *w, int *h)
{
    Asset *a;
    uint16_t *bank;
    if (asset < 0 || asset >= CARD_LAYOUT_ART_COUNT) return 0;
    a = &assets[asset];
    if (a->made == 2) return 0;
    if (!(bank = SoftGpu_Bank(ASSET_BANK))) return 0;
    if (!a->made) a->made = make(a, bank) ? 1 : 2;
    if (a->made != 1) return 0;
    *tpage = 0x80 | (ASSET_BANK << 11);   /* getTPage(1, 0, 0, 0) | bank<<11: 8bpp, page (0,0) in the bank */
    *u = 0;
    *v = a->bank_y;
    *clut = (uint16_t)(((a->bank_y + a->h) << 6) | 0);   /* getClut(0, bank_y + h) */
    *w = a->w;
    *h = a->h;
    return 1;
}
