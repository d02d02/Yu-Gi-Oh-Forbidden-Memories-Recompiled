#include "card_layout.h"
#include "pc/mods/mods.h"
#include "pc/mods/json.h"
#include "pc/platform/paths.h"
#include "pc/debug/log.h"
#include <stdio.h>
#include <string.h>

static const char *const element_names[CARD_LAYOUT_ELEMENT_COUNT] = {
    "frame", "title", "description", "level_stars", "attribute", "atk", "def", "art"
};

/* Logged only on change (MEMORIES_TRACE=card_layout), not every frame:
 * func_80028B08.c asks for atk/def/stars/attribute every frame a card
 * viewer is open, but a layout answer only actually changes when the
 * active mod's settings or manifest change. */
static CardLayoutPlacement last[CARD_LAYOUT_ELEMENT_COUNT];
static int last_set[CARD_LAYOUT_ELEMENT_COUNT];

typedef struct {
    int mod;                   /* -1: no applied mod declares "card_layout" */
    const JsonValue *layout;   /* that mod's "card_layout" object */
    char frame_path[1024];     /* its "frame" image, joined with the mod's own directory; "" for none */
} LayoutSource;

/* The last applied mod, in load order, that declares a "card_layout" key --
 * the same "a later mod's value wins" rule every other manifest key
 * follows (notes/modding.md). Re-walked on every call rather than cached:
 * this only runs while a big card is actually being drawn (a card viewer
 * open, a duel's own field or result cards), never the main loop, so
 * walking a handful of loaded mods is nothing worth caching against. */
static LayoutSource find_source(void)
{
    LayoutSource source;
    int i;

    source.mod = -1;
    source.layout = NULL;
    source.frame_path[0] = 0;
    for (i = 0; i < Mods_LoadedCount(); i++) {
        int mod = Mods_Loaded(i);
        const JsonValue *layout;
        if (!Mods_Active(mod)) continue;
        layout = Json_Member(Mods_Manifest(mod), "card_layout");
        if (!layout) continue;
        source.mod = mod;
        source.layout = layout;
    }
    if (source.mod >= 0) {
        const JsonValue *frame = Json_Member(source.layout, "frame");
        const char *file = Json_String(Json_Member(frame, "image"), NULL);
        if (file && *file) {
            if (!Paths_Contained(file) ||
                snprintf(source.frame_path, sizeof(source.frame_path), "%s/%s", Mods_Directory(source.mod), file) >=
                    (int)sizeof(source.frame_path)) {
                Mods_Note(Mods_Id(source.mod), "card_layout: \"frame\" \"image\" \"%s\" is outside the mod", file);
                source.frame_path[0] = 0;
            }
        }
    }
    return source;
}

static int full_bleed_of(const LayoutSource *source)
{
    return source->mod >= 0 && Mods_Setting(Mods_Id(source->mod), "full_bleed", 1) != 0;
}

/* "<key>": {"x": ..., "y": ...}, each defaulting to retail's own place. */
static void point(const JsonValue *layout, const char *key, int *x, int *y, int dx, int dy)
{
    const JsonValue *part = Json_Member(layout, key);
    *x = (int)Json_Number(Json_Member(part, "x"), dx);
    *y = (int)Json_Number(Json_Member(part, "y"), dy);
}

/* "<key>": {"x": ..., "y": ..., "width": ..., "height": ...}, same defaults
 * convention as a "title" mod's image (title_config.h's TitleImage). */
static void rect(const JsonValue *layout, const char *key, int *x, int *y, int *w, int *h,
                 int dx, int dy, int dw, int dh)
{
    const JsonValue *part = Json_Member(layout, key);
    *x = (int)Json_Number(Json_Member(part, "x"), dx);
    *y = (int)Json_Number(Json_Member(part, "y"), dy);
    *w = (int)Json_Number(Json_Member(part, "width"), dw);
    *h = (int)Json_Number(Json_Member(part, "height"), dh);
}

int CardLayout_FullBleed(void)
{
    LayoutSource source = find_source();
    return full_bleed_of(&source);
}

const char *CardLayout_FramePath(void)
{
    static char path[1024];
    LayoutSource source = find_source();
    snprintf(path, sizeof(path), "%s", source.frame_path);
    return path;
}

CardLayoutPlacement CardLayout_Get(CardLayoutElement element)
{
    CardLayoutPlacement p = {1, 0, 0, 0, 0};
    LayoutSource source = find_source();
    int full_bleed = full_bleed_of(&source);

    switch (element) {
    case CARD_LAYOUT_FRAME: {
        /* "frame": {"image": ..., "width": ..., "height": ...} -- the whole
         * box CardLayout_DrawFrame (func_80028B08.c) draws its texture
         * into; 140x196 with no mod's own size given is this feature's own
         * first measured value, kept as the sensible default, not a retail
         * equivalent (retail has no unified frame concept to default to). */
        const JsonValue *frame = Json_Member(source.layout, "frame");
        p.visible = !full_bleed;
        p.w = (int)Json_Number(Json_Member(frame, "width"), 140);
        p.h = (int)Json_Number(Json_Member(frame, "height"), 196);
        break;
    }
    case CARD_LAYOUT_TITLE:
        p.visible = !full_bleed;
        break;
    case CARD_LAYOUT_DESCRIPTION:
        /* Always visible, independent of full_bleed: the description
         * TextBox's own backdrop (func_800283F4.c's D_8009B240) is on
         * screen either way, so hiding only the text would leave it
         * looking empty for no reason. */
        p.visible = 1;
        break;
    case CARD_LAYOUT_LEVEL_STARS:
        if (full_bleed) point(source.layout, "stars", &p.x, &p.y, 0x77, 0x20);
        else { p.x = 0x77; p.y = 0x20; }
        break;
    case CARD_LAYOUT_ATTRIBUTE:
        if (full_bleed) rect(source.layout, "attribute", &p.x, &p.y, &p.w, &p.h, 0x6E, 0xD, 0, 0);
        else { p.x = 0x6E; p.y = 0xD; }
        break;
    case CARD_LAYOUT_ATK:
        if (full_bleed) point(source.layout, "atk", &p.x, &p.y, 0x61, 0x9D);
        else { p.x = 0x61; p.y = 0x9D; }
        break;
    case CARD_LAYOUT_DEF:
        if (full_bleed) point(source.layout, "def", &p.x, &p.y, 0x61, 0xAB);
        else { p.x = 0x61; p.y = 0xAB; }
        break;
    case CARD_LAYOUT_ART:
        /* w/h at 0 (retail) unless full-bleed and the mod gives a rect:
         * func_80028B08.c reads w != 0 as "stretch the art", so an empty
         * "art" key here (no mod, or full_bleed off) correctly draws
         * nothing special. */
        if (full_bleed) rect(source.layout, "art", &p.x, &p.y, &p.w, &p.h, 0, 0, 0, 0);
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
