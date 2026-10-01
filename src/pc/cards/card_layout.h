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
    CARD_LAYOUT_ELEMENT_COUNT
} CardLayoutElement;

typedef struct {
    int visible; /* 0: the call site leaves this element out entirely */
    int x, y;
} CardLayoutPlacement;

CardLayoutPlacement CardLayout_Get(CardLayoutElement element);
/* True when the frame/title/description plate is hidden: the one thing
 * that tells a call site "there's no plate behind what I'm about to draw
 * anymore" without it having to infer that from an unrelated element. */
int CardLayout_FullBleed(void);

#endif
