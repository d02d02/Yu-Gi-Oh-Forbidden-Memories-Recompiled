#include "card_layout.h"
#include "pc/platform/settings.h"
#include "pc/debug/log.h"

static const char *const element_names[CARD_LAYOUT_ELEMENT_COUNT] = {
    "frame", "title", "description", "level_stars", "attribute", "atk", "def", "art", "row_backdrop"
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

/* The card viewer is actually two independent DisplayObjects, not one: win
 * (every placement in this file is win-relative) and a second, wholly
 * separate backdrop object -- func_800283F4.c's own D_8009B240 -- that the
 * description TextBox sits on top of. Its own sprite, its own slide-in,
 * and created unconditionally: only the text box's own content loop is
 * gated by CARD_LAYOUT_DESCRIPTION, not the backdrop object itself. So in
 * full-bleed mode it's still on screen, just with nothing drawn on it --
 * which is why full-bleed's art rect (ART_X/Y/W/H below) is sized against
 * *that* object, not empty space.
 *
 * win's own base position (duel_effect_resource_setup.c's own
 * `DisplayObject_ConfigureSpriteAtPosition(object, 2, 4, ...)` for its
 * frame object) and the backdrop's own (func_800283F4.c's own
 * `ConfigureSpriteAtPosition(..., 0x148, gDuel_bCardViewerYOffset + 0xE,
 * ...)` for its base, sliding to x=0x94 once open) are both retail's own
 * hand-placed literals, restated here rather than redefined there -- those
 * call sites are not `#ifdef MEMORIES_PC`-gated and keep their own
 * literals for byte-exactness. Both objects' y moves by the same
 * gDuel_bCardViewerYOffset each frame, so the gap between their anchors is
 * constant regardless of scroll position. DX/DY are that anchor-to-anchor
 * gap, exact from source.
 *
 * The backdrop's own *visible* art doesn't start flush at its anchor --
 * its texture has its own bezel margin on both axes -- so DX/DY alone
 * aren't where full-bleed's art needs to reach. INSET_X/_Y below are that
 * margin, measured live (2026-10-02): a headless run of the real save
 * state (slot1.state, MEMORIES_LOAD_STATE=1), a scripted Triangle press to
 * open the viewer (MEMORIES_INPUT), and a native 320x240 frame dump
 * (MEMORIES_DUMP_FRAME=200) read back pixel by pixel. An earlier attempt
 * at this (pixels.png) had recorded a ~15-20px horizontal gap and
 * suspected a vertical one too; that screenshot turned out to be cropped
 * before ever reaching the backdrop's edge, so that number was never real
 * -- superseded by the measurement below. Found: the *horizontal* edge
 * already exact (art's last pixel x=141, backdrop's stone border x=142,
 * zero gap, checked across seven rows spanning the art's full height) --
 * INSET_X is DX minus today's own ART_W, not an independent re-measurement.
 * The *vertical* edge had a real, small gap: art's top (y=24) sat 2px
 * above the backdrop's own top edge (y=26). */
#define CARD_LAYOUT_WIN_ORIGIN_X 2    /* duel_effect_resource_setup.c's ConfigureSpriteAtPosition(object, 2, 4, ...) */
#define CARD_LAYOUT_WIN_ORIGIN_Y 4
#define CARD_LAYOUT_BACKDROP_OPEN_X 0x94        /* func_800283F4.c's Widget_SlideSine/snap target for D_8009B240 */
#define CARD_LAYOUT_BACKDROP_Y_OFFSET 0xE       /* func_800283F4.c's ConfigureSpriteAtPosition y argument, before + gDuel_bCardViewerYOffset */
#define CARD_LAYOUT_BACKDROP_DX (CARD_LAYOUT_BACKDROP_OPEN_X - CARD_LAYOUT_WIN_ORIGIN_X)
#define CARD_LAYOUT_BACKDROP_DY (CARD_LAYOUT_BACKDROP_Y_OFFSET - CARD_LAYOUT_WIN_ORIGIN_Y)
#define CARD_LAYOUT_BACKDROP_INSET_X 6   /* measured 2026-10-02: DX(0x92=146) - the art's own 140 */
#define CARD_LAYOUT_BACKDROP_INSET_Y 8   /* measured 2026-10-02: DY(0xA=10) - the measured 2px gap */

/* The backdrop's own left edge is not one straight line for its whole
 * height -- confirmed live (2026-10-02, same headless method as above,
 * scanned row by row): it sits at win-relative x=140 (INSET_X above,
 * CARD_LAYOUT_BACKDROP_DX - CARD_LAYOUT_BACKDROP_INSET_X) for its full
 * height *except* the bottom (biggest) of its three stacked text-line
 * rows, which is 2px wider on the left -- x=138 there, starting the exact
 * row the art's own last pixel row ends (no frame of overlap where both
 * are actually drawn; the step is a seam in the backdrop's own texture,
 * not a collision). That texture is retail's own, reused as-is from
 * Library/Build Deck (library_runtime.c) and unmodified here -- in
 * retail's own non-full-bleed layout this seam is covered by the
 * description text that normally sits on that row, so nobody built
 * against it being straight. Left as-is on purpose: not a bug this file
 * introduced, and the parked real-texture plan (WIP_NOTES.md) is the
 * right place to actually mask it, if that's ever wanted, rather than
 * nudging ART_W/CardLayout_Get's icon-row constants to chase a seam in
 * someone else's asset. */

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
 * X/W/Y are derived from the backdrop relationship above rather than
 * independent numbers: W reaches exactly to the backdrop's own measured
 * visible edge: DX minus its left bezel. Y drops the art's top down to the
 * backdrop's own measured visible top: DY minus its top bezel. H keeps the
 * bottom edge fixed at ICON_ROW_Y (the no-overlap constraint above) rather
 * than growing it, so only the top moves. */
#define ART_X 0
#define ART_Y (CARD_LAYOUT_BACKDROP_DY - CARD_LAYOUT_BACKDROP_INSET_Y)
#define ART_W (CARD_LAYOUT_BACKDROP_DX - CARD_LAYOUT_BACKDROP_INSET_X)
#define ART_H (ICON_ROW_Y - ART_Y)

/* The frame's own total box (this file's own derivation comment above,
 * duel_effect_resource_setup.c's field_18/field_1A * 2) stated as named
 * constants instead of only living inside that comment -- ART_W above
 * happens to equal WIN_W (140 either way, since the art reaches the
 * backdrop's edge which lines up with the frame's own edge), but the two
 * are derived from unrelated facts, not the same one, so they stay
 * separate constants rather than one reused. */
#define CARD_LAYOUT_WIN_W 0x8C
#define CARD_LAYOUT_WIN_H 0xC4

/* The icon/ATK-DEF row's own backdrop (func_80028B08.c's CardLayout_
 * DrawRowBackdrop, card_layout_art.c's CARD_LAYOUT_ART_ROW): the band
 * below the art, full width, down to the frame's own bottom edge -- the
 * same win-relative box the stars/attribute/ATK/DEF positions above
 * already sit inside, just stated as its own rect instead of left
 * implicit. */
#define ROW_X 0
#define ROW_Y ICON_ROW_Y
#define ROW_W CARD_LAYOUT_WIN_W
#define ROW_H (CARD_LAYOUT_WIN_H - ICON_ROW_Y)

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
    case CARD_LAYOUT_ROW_BACKDROP:
        if (full_bleed) { p.x = ROW_X; p.y = ROW_Y; p.w = ROW_W; p.h = ROW_H; }
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
