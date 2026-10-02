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
 * DEF as two side-by-side boxes instead of retail's stacked pair.
 *
 * ICON_ROW_Y, ATTR_X and DEF_X are measured against the real unified frame
 * art (card_layout_art.c's CARD_LAYOUT_ART_FRAME, src/pc/assets/
 * card_layout_frame.png, 919x1319) rather than the original first-pass
 * guess: its attribute-circle cutout flood-filled to image bbox
 * (753,1012)-(842,1101), its stat-box cutouts to (71,1126)-(424,1264) and
 * (491,1126)-(847,1264) (2026-10-02, Python/PIL flood fill on the alpha
 * channel, the same precision the backdrop-alignment measurements above
 * used). Converted at the image's own scale to the frame's 140x196 box
 * (919/140=6.564 a width unit, 1319/196=6.730 a height unit -- not quite
 * uniform, ~2.5% off, the same order of aspect mismatch already accepted
 * for the plaque art): attribute circle centre (121,157), 14px across; left stat box
 * centre (38,178); right stat box centre (102,178). ATTR_X/Y are that
 * centre minus the icon's own half-extent (8, its 0x10x0x10 sprite); ATK/
 * DEF_X are the plaque's own left edge there (CARD_LAYOUT_PLAQUE_W/2
 * before the box centre) plus CARD_LAYOUT_PLAQUE_PAD_X, undoing
 * CardLayout_DrawPlaque's own `x - PAD_X` so the plaque ends up centred
 * on the frame's hole. STAR_X has no cutout to measure against (stars sit
 * directly on the frame's gold, nothing cut out for them) -- kept at its
 * original first-pass value. */
#define ICON_ROW_Y 149
#define VALUES_ROW_Y 171
#define STAR_X 0x50
#define ATTR_X 114
#define ATK_X 25
#define DEF_X 89

/* The card viewer is actually two independent DisplayObjects, not one: win
 * (every placement in this file is win-relative) and a second, wholly
 * separate backdrop object -- func_800283F4.c's own D_8009B240 -- that the
 * description TextBox sits on top of. Its own sprite, its own slide-in,
 * and created unconditionally: only the text box's own content loop is
 * gated by CARD_LAYOUT_DESCRIPTION, not the backdrop object itself. So in
 * full-bleed mode it's still on screen, just with nothing drawn on it.
 *
 * Retired 2026-10-02: win's and the backdrop's own anchor positions used
 * to be restated here as CARD_LAYOUT_WIN_ORIGIN_X/Y and CARD_LAYOUT_
 * BACKDROP_DX/DY/INSET_X/_Y, because full-bleed's art used to be sized to
 * reach the backdrop's own measured visible edge directly (zero gap,
 * confirmed live: art's last pixel x=141, backdrop's stone border x=142,
 * checked across seven rows; vertically art's top (y=24) sat 2px above
 * the backdrop's own top edge (y=26), closed by matching it). Those
 * constants are gone now that ART is a sub-region inside the unified
 * frame instead (below) -- nothing in this file still computes from win's
 * or the backdrop's own anchor. What's still true and still matters: the
 * *frame's* own outer box (CARD_LAYOUT_WIN_W/H, below) has to stay flush
 * against the backdrop the same way ART used to, which is retail's own
 * field_18/field_1A box, not a coincidence -- see its own derivation
 * comment there. If this relationship ever needs re-deriving, the method
 * (a headless run of the real save state, MEMORIES_LOAD_STATE=1, a
 * scripted Triangle press, MEMORIES_INPUT, and a native 320x240 frame
 * dump, MEMORIES_DUMP_FRAME, read back pixel by pixel -- WIP_NOTES.md's
 * Workflow notes) is what found all of this the first time and should be
 * used again rather than re-guessed. */

/* Retired 2026-10-02: the backdrop's own left-edge seam note (its bottom
 * text row 2px wider than the rows above) that used to live here applied
 * to ART_W reaching across to touch that object. ART no longer reaches
 * that far -- it is now inset inside the unified frame's own art cutout
 * (below), not flush against the description backdrop -- so that seam is
 * no longer this file's concern at all. The frame's own *outer* box still
 * has to stay flush with the backdrop, same as ART used to; that's what
 * CARD_LAYOUT_WIN_W/H are, further down, and the seam still exists on the
 * backdrop's side of that join -- just not something ART's own rect has
 * to route around anymore.
 *
 * Full-bleed's own art rect (func_80028B08.c's CardLayout_DrawArt) is now
 * a sub-region of the unified frame (CARD_LAYOUT_ART_FRAME, card_layout_
 * art.c, src/pc/assets/card_layout_frame.png) instead of reaching the
 * frame's own full width/height: that asset's own art cutout, measured
 * the same way as ICON_ROW_Y/ATTR_X/DEF_X above (flood fill, image bbox
 * (23,23)-(896,947), converted at the image's own 6.564/6.730 x/y scale)
 * gives native x=[3.5,136.5] (a real ~3.5px matted margin each side,
 * symmetric in image space: 23px in from both the left and right edges of
 * the 919-wide source) and y=[3.4,140.7]. Rounded to whole px, margin
 * kept symmetric left/right rather than the two edges independently
 * rounded. */
#define ART_X 4
#define ART_Y 3
#define ART_W 132
#define ART_H 138

/* The frame's own total box (duel_effect_resource_setup.c's field_18/
 * field_1A * 2, this file's own long-standing derivation): still what
 * CARD_LAYOUT_ART_FRAME's own draw rect uses (func_80028B08.c), covering
 * art, border and bottom section as one piece -- ART above is a sub-region
 * inside it, not the same rect anymore (see above). Public (card_layout.h),
 * not just internal here: func_80028B08.c needs it to size that draw call. */

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
