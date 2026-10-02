#ifndef MEMORIES_PC_CARDS_CARD_LAYOUT_ART_H
#define MEMORIES_PC_CARDS_CARD_LAYOUT_ART_H
/* Real art for full-bleed's own UI pieces (card_layout.c) that have no disc
 * counterpart -- port-owned PNGs, compiled in (src/pc/assets/), decoded
 * once each into a shared SoftGpu_Bank the same way src/pc/cards/
 * star_icons.c and src/pc/text/glyphs.c already do for theirs, then read
 * back as an ordinary tpage/u/v/clut cell. */

typedef enum {
    CARD_LAYOUT_ART_PLAQUE,       /* the ATK/DEF plaque backdrop (CardLayout_DrawPlaque) */
    CARD_LAYOUT_ART_FRAME,        /* the unified card frame: border + bottom section as one piece (CardLayout_DrawFrame) */
    CARD_LAYOUT_ART_COUNT
} CardLayoutArtAsset;

/* 1 on success (`*tpage`/`*u`/`*v`/`*clut` filled, its own stored w/h in
 * `*w`/`*h`), 0 if the asset could not be decoded or the bank could not be
 * allocated -- callers keep their own fallback (a flat fill, or simply not
 * drawing it) for that case. */
int CardLayoutArt_Cell(CardLayoutArtAsset asset, int *tpage, int *u, int *v, int *clut, int *w, int *h);

#endif
