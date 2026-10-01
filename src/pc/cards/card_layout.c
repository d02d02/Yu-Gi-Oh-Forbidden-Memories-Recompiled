#include "card_layout.h"
#include "pc/platform/settings.h"
#include "pc/debug/log.h"

static const char *const element_names[CARD_LAYOUT_ELEMENT_COUNT] = {
    "frame", "title", "description", "level_stars", "attribute", "atk", "def", "art"
};

/* Logged only on change (MEMORIES_TRACE=card_layout), not every frame:
 * func_80028B08.c asks for atk/def/stars/attribute every frame a card
 * viewer is open, but a layout answer only actually changes when the
 * setting flips or this file's own constants are re-tuned. */
static CardLayoutPlacement last[CARD_LAYOUT_ELEMENT_COUNT];
static int last_set[CARD_LAYOUT_ELEMENT_COUNT];

/* Layout 1 (settings.c): a row directly under the picture, stars on the
 * left and the attribute icon on the right; directly under that, ATK and
 * DEF as two side-by-side boxes instead of retail's stacked pair. The
 * picture's own real bottom edge is 0x32 + 0x60 = 0x92
 * (func_80028B08.c's own research comment). First pass for live tuning,
 * not a final measurement. */
#define ICON_ROW_Y (0x92 + 4)
#define VALUES_ROW_Y (ICON_ROW_Y + 20)
#define STAR_X 0x50
#define ATTR_X 0x69
#define ATK_X 0x1A
#define DEF_X 0x50

/* Full-bleed's own art rect (func_80028B08.c's CardLayout_DrawArt): retail's
 * own frame, not an arbitrary guess, on three sides. duel_effect_resource_
 * setup.c sets the frame object's field_18/field_1A to 0x46,0x62, and
 * func_80028B08.c's own clip test reads them as a centre-point offset from
 * win's own origin (win->field_30 + win->field_18/1A) -- so the frame's own
 * box, in this same win-relative neighbourhood, is 2*(0x46,0x62) =
 * (0x8C,0xC4) starting at win's origin (0,0). That checks out exactly
 * against the picture's own retail placement: inset 0x13,0x32 (19,50) sized
 * 0x66x0x60 (102,96) leaves a 19px right margin (140-121) and a 50px bottom
 * margin (196-146) -- matching its own left/top inset symmetrically, which
 * only happens if this is really the frame's own box.
 *
 * The bottom edge does NOT go all the way to the frame's own 0xC4, though
 * (confirmed live -- doing so widened the ATK/DEF look, the art bleeding in
 * behind/around the icon and value rows). It stops at ICON_ROW_Y instead,
 * right where that row starts, so there's no overlap at all. That lines up
 * with the Duel Links reference art's own proportions, measured off the
 * reference screenshot: its picture spans roughly the top 56% of the
 * card's height and stops around 79% of the way down (the rest is its own
 * type-line/description block, which full-bleed doesn't have); ICON_ROW_Y
 * (150) is 150/0xC4 = 77% of this frame's own height -- close enough to
 * use directly instead of a separately re-derived ratio.
 *
 * Known gap, deferred on purpose (2026-10-02): at this width the art falls
 * short of the card-viewer's own wider backdrop (the one that also covers
 * where description text sits, off to the right) by roughly 15-20px,
 * exposing the duel field's stone-textured background through that gap --
 * confirmed by pixel-measuring a live screenshot (pixels.png), not the
 * left/right translation issue it first looked like (the left edge has no
 * matching gap, just its own thin ~8px bezel on every row). Left as-is
 * until this whole rect is rethought to include that wider right-hand
 * backdrop -- see the next-steps note in memory. */
#define ART_X 0
#define ART_Y 0
#define ART_W 0x8C
#define ART_H ICON_ROW_Y

CardLayoutPlacement CardLayout_Get(CardLayoutElement element)
{
    CardLayoutPlacement p = {1, 0, 0, 0, 0};
    int full_bleed = Settings_Get(SET_CARD_LAYOUT);

    switch (element) {
    case CARD_LAYOUT_FRAME:
    case CARD_LAYOUT_TITLE:
    case CARD_LAYOUT_DESCRIPTION:
        p.visible = !full_bleed;
        break;
    case CARD_LAYOUT_LEVEL_STARS:
        if (full_bleed) { p.x = STAR_X; p.y = ICON_ROW_Y; }
        else             { p.x = 0x77;  p.y = 0x20; }
        break;
    case CARD_LAYOUT_ATTRIBUTE:
        if (full_bleed) { p.x = ATTR_X; p.y = ICON_ROW_Y; }
        else             { p.x = 0x6E;  p.y = 0xD; }
        break;
    case CARD_LAYOUT_ATK:
        if (full_bleed) { p.x = ATK_X; p.y = VALUES_ROW_Y; }
        else             { p.x = 0x61; p.y = 0x9D; }
        break;
    case CARD_LAYOUT_DEF:
        if (full_bleed) { p.x = DEF_X; p.y = VALUES_ROW_Y; }
        else             { p.x = 0x61; p.y = 0xAB; }
        break;
    case CARD_LAYOUT_ART:
        if (full_bleed) { p.x = ART_X; p.y = ART_Y; p.w = ART_W; p.h = ART_H; }
        break;
    default:
        break;
    }

    if (element >= 0 && element < CARD_LAYOUT_ELEMENT_COUNT &&
        (!last_set[element] || last[element].visible != p.visible ||
         last[element].x != p.x || last[element].y != p.y ||
         last[element].w != p.w || last[element].h != p.h)) {
        LOG(LOG_CARD_LAYOUT, "%s: visible=%d x=%d y=%d w=%d h=%d (full_bleed=%d)",
            element_names[element], p.visible, p.x, p.y, p.w, p.h, full_bleed);
        last[element] = p;
        last_set[element] = 1;
    }
    return p;
}

int CardLayout_FullBleed(void)
{
    return Settings_Get(SET_CARD_LAYOUT) != 0;
}
