#ifndef MEMORIES_PC_CARDS_CARD_LAYOUT_ART_H
#define MEMORIES_PC_CARDS_CARD_LAYOUT_ART_H
/* The unified card frame (card_layout.c's CARD_LAYOUT_WIN_W/H, the whole
 * WIN box) -- a port-owned PNG with no disc counterpart, compiled in
 * (src/pc/assets/card_layout_frame.png), decoded once into a SoftGpu_Bank
 * the same way src/pc/cards/star_icons.c and src/pc/text/glyphs.c already
 * do for theirs, then read back as an ordinary tpage/u/v/clut cell.
 *
 * One asset, one purpose: this used to be a small per-asset table
 * (CardLayoutArtAsset) shared with a separate ATK/DEF plaque texture: the
 * frame now bakes that plaque's own look (its ornate border, its cream
 * background) into itself as painted art, so the plaque is retired and
 * this is single-purpose again. */

/* 1 on success (`*tpage`/`*u`/`*v`/`*clut` filled, its own stored w/h in
 * `*w`/`*h`), 0 if the asset could not be decoded or the bank could not be
 * allocated -- the caller (func_80028B08.c) simply doesn't draw it then,
 * purely decorative. */
int CardLayoutArt_FrameCell(int *tpage, int *u, int *v, int *clut, int *w, int *h);

#endif
