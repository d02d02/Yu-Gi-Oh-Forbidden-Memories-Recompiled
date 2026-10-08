#ifndef MEMORIES_PC_CARDS_CARD_LAYOUT_ART_H
#define MEMORIES_PC_CARDS_CARD_LAYOUT_ART_H
/* The unified card frame (card_layout.h's CardLayout_Get(CARD_LAYOUT_FRAME)
 * w/h) -- a layout mod's own PNG, no disc counterpart and no counterpart
 * compiled into the port either (card_layout.h's CardLayout_FramePath),
 * decoded once into a SoftGpu_Bank the same way src/pc/cards/star_icons.c
 * and src/pc/text/glyphs.c already do for theirs, then read back as an
 * ordinary tpage/u/v/clut cell. */

/* The frame is FRAME_COLS x FRAME_ROWS tiles (card_layout_art.c explains
 * why), drawn as that many abutting quads. */
#define CARD_LAYOUT_FRAME_COLS 3
#define CARD_LAYOUT_FRAME_ROWS 3

/* 1 on success (`*tpage`/`*clut` filled, the tile's own texel w/h in
 * `*w`/`*h`; its texels start at u = v = 0 of that page), 0 when no mod
 * gives a frame path, or it could not be decoded or the bank could not be
 * allocated -- the caller (func_80028B08.c) simply doesn't draw it then,
 * purely decorative. */
int CardLayoutArt_FrameTile(int col, int row, int *tpage, int *clut, int *w, int *h);

/* The layout's ATK/DFD digits (card_layout.h's CardLayout_Digits): one PNG,
 * DIGIT_COLS x DIGIT_ROWS cells of DIGIT_CELL_W x DIGIT_CELL_H texels, digit
 * d in column d % 5, row d / 5 -- 200x96 (4 texels a card unit, one a
 * screen pixel at Internal 4x), which tools/pc/hd_assets_pack.py
 * draws from a font. 1 on success (the cell's page, u, v, clut and texel
 * size filled), 0 when the layout gives none or it could not be built: the
 * caller draws the retail digits then. */
#define CARD_LAYOUT_DIGIT_COLS 5
#define CARD_LAYOUT_DIGIT_ROWS 2
#define CARD_LAYOUT_DIGIT_CELL_W 40
#define CARD_LAYOUT_DIGIT_CELL_H 48
int CardLayoutArt_DigitCell(int digit, int *tpage, int *u, int *v, int *clut, int *w, int *h);

/* Once a frame (cards.c's Cards_Frame): builds, one a call and only now and
 * then, any frame image of the active layout not built yet, so the cost of
 * building one (decoding a 919x1319 PNG and a 255-colour median cut of it,
 * tens to hundreds of milliseconds) is paid off screen, not on the frame a
 * card first draws. */
void CardLayoutArt_Prewarm(void);

#endif
