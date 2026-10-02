#ifndef MEMORIES_PC_CARD_LAYOUT_H
#define MEMORIES_PC_CARD_LAYOUT_H
/* One place that answers "where does this element of the big-card display
 * go, and should it even be drawn" for SET_CARD_LAYOUT (settings.h), so the
 * three call sites that used to each repeat their own Settings_Get check
 * and their own magic numbers -- duel_effect_resource_setup.c's frame
 * list-membership, func_800283F4.c's description box, and func_80028B08.c's
 * title/stats/stars/attribute -- read one shared answer instead. Adding a
 * layout style, or re-tuning where an element sits, touches card_layout.c
 * only; the call sites stay as they are.
 *
 * x/y are an offset in the same coordinate neighbourhood as the retail code
 * they replace (func_80028B08.c's own +0x13, +0x9D, ... constants): added
 * to whatever base the call site already adds its own retail constant to
 * (win->field_30's own position, or a per-star cursor), never an
 * independent origin. */

typedef enum {
    CARD_LAYOUT_FRAME,
    CARD_LAYOUT_TITLE,
    CARD_LAYOUT_DESCRIPTION,
    CARD_LAYOUT_LEVEL_STARS,
    CARD_LAYOUT_ATTRIBUTE,
    CARD_LAYOUT_ATK,
    CARD_LAYOUT_DEF,
    CARD_LAYOUT_ART,
    CARD_LAYOUT_ELEMENT_COUNT
} CardLayoutElement;

typedef struct {
    int visible; /* 0: the call site leaves this element out entirely */
    int x, y;
    /* w/h: only CARD_LAYOUT_ART uses these, to stretch the picture to a
     * size independent of the texel footprint DisplayObject_
     * ConfigureScreenSprite gave it (func_80028B08.c's own CardLayout_
     * DrawArt). Every other element keeps these 0 -- retail's own sprite
     * resource already fixes its draw size. */
    int w, h;
} CardLayoutPlacement;

/* The frame's own total box (card_layout.c's own derivation comment,
 * duel_effect_resource_setup.c's field_18/field_1A * 2): public, not just
 * internal to card_layout.c, since func_80028B08.c needs it to size the
 * unified frame's own draw rect (CardLayout_DrawFrame, CARD_LAYOUT_ART_FRAME
 * -- the whole WIN box, border and bottom section as one piece, card_layout_
 * art.c). */
#define CARD_LAYOUT_WIN_W 0x8C
#define CARD_LAYOUT_WIN_H 0xC4

/* The ATK/DEF plaque's own box (func_80028B08.c's CardLayout_DrawPlaque),
 * anchored at each digit row's own x/y (CARD_LAYOUT_ATK/DEF above) minus
 * this padding. W's aspect matches the real plaque art's own
 * (src/pc/cards/card_layout_art.c's PLAQUE_W/H, 179x71 = ~2.52) instead of
 * an independently chosen number, so the art it now draws (CardLayoutArt_
 * Cell) isn't stretched off its own proportions: H stays fixed at
 * the digit glyph's own height (0x0D) plus top/bottom padding, and
 * PAD_X solves W = H * 179/71. Comfortably holds up to 5 digits either
 * way (step 5px, glyph 6px wide: a 5-digit row spans (5-1)*5+6 = 26px). */
#define CARD_LAYOUT_PLAQUE_PAD_X 9
#define CARD_LAYOUT_PLAQUE_PAD_TOP 2
#define CARD_LAYOUT_PLAQUE_PAD_BOTTOM 2
#define CARD_LAYOUT_PLAQUE_W (26 + 2 * CARD_LAYOUT_PLAQUE_PAD_X)
#define CARD_LAYOUT_PLAQUE_H (0x0D + CARD_LAYOUT_PLAQUE_PAD_TOP + CARD_LAYOUT_PLAQUE_PAD_BOTTOM)

CardLayoutPlacement CardLayout_Get(CardLayoutElement element);
/* True when the frame/title/description plate is hidden: the one thing
 * that tells a call site "there's no plate behind what I'm about to draw
 * anymore" without it having to infer that from an unrelated element. */
int CardLayout_FullBleed(void);

#endif
