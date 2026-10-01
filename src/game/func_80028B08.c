#include "../types.h"
#include "text_encode_decimal_digits.h"
#include "display_object_projection.h"
#include "duel_effect_resource_record.h"
#include "../psyq/libgs.h"
#include "display_object.h"
#include "card_preview_callbacks.h"
#include "sprite_primitive.h"
#define DISPLAY_OBJECT_PACKET_SUBMIT_CARD_LIST
#include "display_object_packet_submit.h"
#include "card_constants.h"
#include "../ygo_types.h"
#ifdef MEMORIES_PC
#include "../psyq/libgpu.h"
#include "pc/cards/tables.h"
#include "pc/cards/card_layout.h"
#endif
/*
 * Duel card-detail panel: builds the scratchpad sprite parameters for the
 * panel frame, the card image, the ATK/DEF digit rows, the repeated level
 * icons and the guardian-star tile, and submits each through
 * DisplayObject_SubmitPacket. Byte-exact under gcc_2_8_1_g8_split with no
 * register pins, aliases or inline assembly.
 *
 * Three constructs exist only to steer the compiler and emit no code:
 *
 *  - `sa`/`sb` with the 0x00090009 extent inside a do/while (0): the loop
 *    note after the x load is a scheduling barrier, which gives retail's
 *    `lhu; lui; ori; addiu` order at the level-icon block.
 *
 *  - the two guarded write-backs (`win->flags = flags;` and the second
 *    `PRM->cxcy.h.cy = white;`). Each stores a value its destination already
 *    holds. cse keeps such a store, so the guard and its condition are real
 *    code for flow, both scheduling passes and both register allocators;
 *    reload's cse then deletes the no-op store, and jump2 deletes the empty
 *    branch together with the whole condition chain. Nothing reaches the
 *    object, but while they exist they shape the conflict graph:
 *      - the first makes the 14 (`k`) and the 0xFEFFFFFF mask (`m`) global
 *        pseudos that conflict with each other and with the two temporaries
 *        in v0/v1, so global-alloc gives `k` t1 and `m` t2 as retail has
 *        (local-alloc alone puts the 14 in v0 and the mask in t1). `k` and
 *        `m` are read before their only assignment on purpose: a second
 *        assignment would stop `li k` being placed next to its store and
 *        lift it above the argument moves. `k` is u16 because an SImode 14
 *        lets reload's cse rewrite `addiu t0,t0,14` as `addu t0,t0,t1`.
 *      - the second keeps the 0xF8 (`white`) live while the clamp counter
 *        `i` holds s0, so `white` takes s4. Its condition repeats the shape
 *        of the clamp test that follows, which keeps local-alloc's order
 *        for the two field loads.
 *    With those registers the second scheduling pass floats `li t1,14` and
 *    `li s4,248` to the top of the second submit block by itself.
 */
#ifdef MEMORIES_PC
/* A flat Gouraud-quad plaque behind full-bleed's ATK/DEF (card_layout.c), so
 * retail's own digit draw -- semi-transparent, blended "plate minus digit"
 * -- has the lighter backdrop it was always designed against. Deliberately
 * NOT a textured quad: the shared digit-font atlas (tpage 0x1F) packs glyphs
 * with no clean blank region to sample (confirmed live -- an opaque digit
 * draw showed scratches, the atlas's own inter-glyph padding bleeding
 * through once nothing was there to blend it away), so reusing any of its
 * texels for a "plain" fill risks the same thing.
 *
 * Routed through DisplayObject_SubmitPacket's own case-4 dispatch -- the
 * plain screen-space Gouraud-quad path DisplayObject_RenderGouraudQuadList
 * uses everywhere else in the game -- instead of a raw GsSortPoly bypass.
 * That case treats its first argument's bit 0x04000000 as "project me": set,
 * it subtracts EXT's own origin from each vertex and runs RotAverageNclip4
 * before submitting, exactly like the digit submissions below; clear, it
 * submits the vertices as given. x/y/w/h are this box's own screen-space
 * rectangle, already including whatever base position the caller added
 * (win->field_30 + the element's own offset) -- the same coordinate
 * neighbourhood every other PRM->xy assignment in this file already uses,
 * and exactly what case 4 expects to subtract its origin from.
 *
 * `mode` is the caller's own submit mode (`arg`): its upper halfword is 0xF
 * while this card is mid-rotation (every other element projected through
 * EXT) and 0x1 while it's static (the cheap unprojected GsSortFastSprite
 * path, nothing else this frame projected either) -- the plaque mirrors
 * that choice rather than always projecting, so a static card's plaque
 * isn't run through RotAverageNclip4 for no reason.
 *
 * Confirmed live: the old GsSortPoly bypass stayed flat/static through the
 * card's own turn/reveal rotation while every other element (picture,
 * digits, stars, attribute) rotated with it; routed this way, the plaque
 * rotates too. */
static void CardLayout_DrawPlaque(s32 x, s32 y, s32 w, s32 h, s32 ot, s32 mode,
                                   Func80028B08Extra *EXT)
{
    POLY_G4 plaque;
    s32 projected = ((u32)mode >> 16) == 0xF;
    s32 attribute = projected ? 0x04000000 : 0;
    s32 plaque_mode = (mode & 0xFFFF) | 0x40000;

    setPolyG4(&plaque);
    setRGB0(&plaque, 220, 200, 150); /* parchment beige, per the reference art */
    setRGB1(&plaque, 220, 200, 150);
    setRGB2(&plaque, 220, 200, 150);
    setRGB3(&plaque, 220, 200, 150);
    setXY4(&plaque, (short)x, (short)y, (short)(x + w), (short)y,
           (short)x, (short)(y + h), (short)(x + w), (short)(y + h));

    DisplayObject_SubmitPacket((SpritePrim *)attribute, (Func80028B08Ctx *)&plaque,
                               ot, plaque_mode, EXT);
}

/* Comfortably holds up to 5 digits (step 5px, glyph 6px wide: a 5-digit
 * row spans (5-1)*5+6 = 26px) plus a few pixels of padding on every side. */
#define CARD_LAYOUT_PLAQUE_PAD_X 3
#define CARD_LAYOUT_PLAQUE_PAD_TOP 2
#define CARD_LAYOUT_PLAQUE_PAD_BOTTOM 2
#define CARD_LAYOUT_PLAQUE_W (26 + 2 * CARD_LAYOUT_PLAQUE_PAD_X)
#define CARD_LAYOUT_PLAQUE_H (0x0D + CARD_LAYOUT_PLAQUE_PAD_TOP + CARD_LAYOUT_PLAQUE_PAD_BOTTOM)
#endif

void func_80028B08(DisplayObject *obj, s32 arg1) {
    u8 buf1[5];
    u8 buf2[5];
    Func80028B08Extra *EXT;
    SpritePrim *PRM;
    Func80028B08Ctx *CTX;
    DisplayObject *win;
    DuelEffectResourceRecord *rec;
    s32 arg;
    s32 i;
    u16 flags;
    u32 f4;
    u32 tile;
    u32 lo;
    s32 wrap;
    u16 k;
    s32 white;
    s32 sa;
    s32 sb;
    u32 m;
#ifdef MEMORIES_PC
    /* Card layout (card_layout.h): win's own position is close to screen
     * origin (~2,4) -- retail's own offsets below (+0x13, +0x9D, ...) are
     * the entire positioning mechanism, not padding inside an
     * already-placed frame, confirmed by research before touching this a
     * second time. So every placement below stays in retail's own
     * coordinate neighbourhood, not a reset-to-zero origin: card_layout.c
     * is the single place that knows where each element sits for either
     * layout. Enlarging the art itself is separate, later work (extent is
     * the texel-read size for every submission path reachable here, not an
     * independent draw size -- confirmed by research -- so it needs a
     * hand-built POLY_FT4 like field_art.c's own cutout, not a bigger
     * PRM->extent). */
    CardLayoutPlacement title_layout = CardLayout_Get(CARD_LAYOUT_TITLE);
    CardLayoutPlacement atk_layout = CardLayout_Get(CARD_LAYOUT_ATK);
    CardLayoutPlacement def_layout = CardLayout_Get(CARD_LAYOUT_DEF);
    CardLayoutPlacement star_layout = CardLayout_Get(CARD_LAYOUT_LEVEL_STARS);
    CardLayoutPlacement attr_layout = CardLayout_Get(CARD_LAYOUT_ATTRIBUTE);
#endif

    wrap = 0xFFFF;
    win = (DisplayObject *)obj->field_54;
    if ((obj->attribute & (1<<31) ) != 0) {
        return;
    }
    flags = win->flags;
    if ((obj->field_66 & m) ^ (obj->field_67 & k)) {
        win->flags = flags;
    }
    if ((flags & 0x40) == 0) {
        return;
    }
    EXT = (Func80028B08Extra *)0x1F800398;
    PRM = (SpritePrim *)0x1F800320;
    CTX = (Func80028B08Ctx *)0x1F800344;
    arg = (((s16)win->field_14 - 1) & 0xFFFF) | 0x10000;
    if (flags & 0x4) {
        obj->field_20.word = win->field_20.word;
        f4 = obj->attribute & ~(1<<27) ;
        obj->field_44.word = win->field_44.word;
        obj->attribute = f4;
        f4 = f4 | (win->attribute & 0x08000000);
        obj->attribute = f4;
        if (func_80041F90(
                (struct DisplayObject *)obj, (s16)win->field_30.h.field_30 + (s16)win->field_18,
                (s16)win->field_30.h.field_32 + (s16)win->field_1A, (struct ProjectionOut *)EXT
            ) <= 0) {
            return;
        }
        arg = (((s16)win->field_14 - 1) & 0xFFFF) | 0xF0000;
        *(u32 *)&CTX->field_4 = win->field_0C;
        CTX->field_3 = 9;
        CTX->field_7 = 0x2C;
    }

    PRM->attribute = obj->attribute;
    PRM->xy.h.x = win->field_30.h.field_30 + 0x13;
    PRM->xy.h.y = win->field_30.h.field_32 + 0x32;
    PRM->extent.wh.w.word = 0x66;
    PRM->extent.wh.h = 0x60;
    PRM->rgb = win->field_0C;
    PRM->cxcy.word = obj->field_40.word;
    PRM->uv.word = obj->field_5C;
    PRM->tpage = obj->field_66;
    DisplayObject_SubmitPacket(PRM, CTX, arg1, arg, EXT);

    CTX->field_7 |= 2;
    PRM->xy.h.x = win->field_30.h.field_30 + 0xC;
    PRM->xy.h.y = win->field_30.h.field_32 + 0xE;
    PRM->uv.b.hi = PRM->uv.b.hi + 0x60;
    m = 0xFEFFFFFF;
    PRM->attribute = (PRM->attribute & m) | 0x60000000;
    PRM->extent.wh.w.word = 0x60;
    k = 0xE;
    PRM->extent.wh.h = k;
    PRM->cxcy.h.cx = 0x1E0;
    white = 0xF8;
    PRM->cxcy.h.cy = white;
#ifdef MEMORIES_PC
    /* Card layout (card_layout.h): no title plate, part of the retail
     * frame this style leaves out. white/m/k above are still real code
     * either way -- they are read again below, submitted or not. */
    if (title_layout.visible)
#endif
    DisplayObject_SubmitPacket(PRM, CTX, arg1, arg, EXT);

    EXT->field_4 = 0;
    rec = &D_800EA0E8[obj->field_67];
    PRM->tpage = 0x1F;
    PRM->cxcy.h.cx = PRM->cxcy.h.cx + 0x10;
    PRM->xy.h.x = win->field_30.h.field_30 + obj->field_30.h.field_30;
    PRM->xy.h.y = win->field_30.h.field_32 + obj->field_30.h.field_32;
    PRM->extent.word = obj->field_3C.word;
    PRM->uv.word = obj->field_5E;
    if (obj->field_68 < 0x14) {
        if (rec->field_3C & 0x80) {
            PRM->cxcy.h.cy = PRM->cxcy.h.cy + 1;
        }
#ifdef MEMORIES_PC
        /* Card layout: "ATK"/"DFD" (same shared font page as the digits,
         * positioned via obj->field_30 -- a fixed per-screen offset set at
         * setup, never touched by card_layout.c). Retail's stacked layout
         * has room for this label to the left of each value; full-bleed's
         * relocated, side-by-side boxes do not, and the reference layout
         * (bewd.jpeg) reads the boxes by position alone, no label text. */
        if (!CardLayout_FullBleed())
#endif
        DisplayObject_SubmitPacket(PRM, CTX, arg1, arg, EXT);
        PRM->cxcy.h.cy = white;
        PRM->uv.b.hi = PRM->uv.b.hi + *(u8 *)&PRM->extent.wh.h;
        PRM->xy.h.y = PRM->xy.h.y + (PRM->extent.wh.h + wrap);
        if (rec->field_3C & 0x40) {
            PRM->cxcy.h.cy = 0xF9;
        }
#ifdef MEMORIES_PC
        if (!CardLayout_FullBleed())
#endif
        DisplayObject_SubmitPacket(PRM, CTX, arg1, arg, EXT);
        PRM->cxcy.h.cy = white;

#ifdef MEMORIES_PC
        {
            /* The caps are a mod's "limits" (pc/cards/tables.h). Past 9999
               the numbers take five digits, five pixels apart (the digits'
               own width, so they touch), where four six apart go: the ATK
               and DFD labels on the left and the plate's edge on the right
               leave no room for more. */
            s32 attack = rec->field_32 + rec->field_36;
            s32 defense = rec->field_34 + rec->field_38;
            s32 digits, step, atk_left, def_left;

            if (attack > Tables_StatCap(0)) {
                attack = Tables_StatCap(0);
            }
            if (defense > Tables_StatCap(1)) {
                defense = Tables_StatCap(1);
            }
            digits = attack >= 10000 || defense >= 10000 ? 5 : 4;
            step = digits == 5 ? 5 : 6;
            atk_left = digits == 5 ? atk_layout.x - 1 : atk_layout.x;
            def_left = digits == 5 ? def_layout.x - 1 : def_layout.x;
            Text_EncodeDecimalDigits(attack, digits, buf1);
            Text_EncodeDecimalDigits(defense, digits, buf2);

            PRM->uv.b.hi = (PRM->uv.b.hi & 0x80) + 0x10;
            PRM->xy.h.x = win->field_30.h.field_30 + atk_left;
            PRM->xy.h.y = win->field_30.h.field_32 + atk_layout.y;
            *(u32 *)&PRM->extent = 0x000D0006;
            if (rec->field_3C & 0x80) {
                PRM->cxcy.h.cy = 0xF9;
            }
            for (i = digits - 1; i >= 0; i--) {
                PRM->uv.b.lo = buf1[i] * 6 + 0x10;
                DisplayObject_SubmitPacket(PRM, CTX, arg1, arg, EXT);
                PRM->xy.h.x = PRM->xy.h.x + step;
            }
            if (CardLayout_FullBleed()) {
                /* Submitted AFTER its digits on purpose: this port's own OT
                 * (src/pc/sdk/libgs.c's make_packet) prepends each new
                 * submission to its depth bucket's head, and the head is
                 * what gets walked/drawn first -- so the most recently
                 * submitted primitive at a shared depth ends up drawn
                 * first (underneath), not on top. */
                CardLayout_DrawPlaque(win->field_30.h.field_30 + atk_layout.x - CARD_LAYOUT_PLAQUE_PAD_X,
                                      win->field_30.h.field_32 + atk_layout.y - CARD_LAYOUT_PLAQUE_PAD_TOP,
                                      CARD_LAYOUT_PLAQUE_W, CARD_LAYOUT_PLAQUE_H, arg1, arg, EXT);
            }

            PRM->xy.h.x = win->field_30.h.field_30 + def_left;
            PRM->xy.h.y = win->field_30.h.field_32 + def_layout.y;
            PRM->cxcy.h.cy = 0xF8;
            if (rec->field_3C & 0x40) {
                PRM->cxcy.h.cy = 0xF9;
            }
            for (i = digits - 1; i >= 0; i--) {
                PRM->uv.b.lo = buf2[i] * 6 + 0x10;
                DisplayObject_SubmitPacket(PRM, CTX, arg1, arg, EXT);
                PRM->xy.h.x = PRM->xy.h.x + step;
            }
            if (CardLayout_FullBleed()) {
                CardLayout_DrawPlaque(win->field_30.h.field_30 + def_layout.x - CARD_LAYOUT_PLAQUE_PAD_X,
                                      win->field_30.h.field_32 + def_layout.y - CARD_LAYOUT_PLAQUE_PAD_TOP,
                                      CARD_LAYOUT_PLAQUE_W, CARD_LAYOUT_PLAQUE_H, arg1, arg, EXT);
            }
        }
#else
        i = rec->field_32 + rec->field_36;
        if (i > 9999) {
            PRM->cxcy.h.cy = white;
        }
        if (i > 9999 ) {
            i = 9999 ;
        }
        Text_EncodeDecimalDigits(i, 4, buf1);
        i = rec->field_34 + rec->field_38;
        if (i > 9999 ) {
            i = 9999 ;
        }
        Text_EncodeDecimalDigits(i, 4, buf2);

        PRM->uv.b.hi = (PRM->uv.b.hi & 0x80) + 0x10;
        PRM->xy.h.x = win->field_30.h.field_30 + 0x61;
        PRM->xy.h.y = win->field_30.h.field_32 + 0x9D;
        *(u32 *)&PRM->extent = 0x000D0006;
        if (rec->field_3C & 0x80) {
            PRM->cxcy.h.cy = 0xF9;
        }
        i = 3;
        do {
            PRM->uv.b.lo = buf1[i] * 6 + 0x10;
            DisplayObject_SubmitPacket(PRM, CTX, arg1, arg, EXT);
            PRM->xy.h.x = PRM->xy.h.x + 6;
            i--;
        } while (i >= 0);

        PRM->xy.h.x = win->field_30.h.field_30 + 0x61;
        PRM->xy.h.y = win->field_30.h.field_32 + 0xAB;
        PRM->cxcy.h.cy = 0xF8;
        if (rec->field_3C & 0x40) {
            PRM->cxcy.h.cy = 0xF9;
        }
        i = 3;
        do {
            PRM->uv.b.lo = buf2[i] * 6 + 0x10;
            DisplayObject_SubmitPacket(PRM, CTX, arg1, arg, EXT);
            PRM->xy.h.x = PRM->xy.h.x + 6;
            i--;
        } while (i >= 0);
#endif

        sa = win->field_30.h.field_30;
        do { sb = 0x00090009; } while (0);
        PRM->xy.h.x = sa + 0x77;
        PRM->xy.h.y = win->field_30.h.field_32 + 0x20;
#ifdef MEMORIES_PC
        PRM->xy.h.x = sa + star_layout.x;
        PRM->xy.h.y = win->field_30.h.field_32 + star_layout.y;
#endif
        *(u32 *)&PRM->extent = sb;
        PRM->uv.b.lo = 0;
        PRM->cxcy.h.cx = 0x1C0;
        PRM->cxcy.h.cy = 0xF8;
        if (rec->field_3A != 0) {
            i = 0;
            do {
                DisplayObject_SubmitPacket(PRM, CTX, arg1, arg, EXT);
                PRM->xy.h.x = PRM->xy.h.x - 9;
                i++;
            } while (i < (s32)rec->field_3A);
        }
    } else {
        DisplayObject_SubmitPacket(PRM, CTX, arg1, arg, EXT);
    }

    PRM->xy.h.x = win->field_30.h.field_30 + 0x6E;
    PRM->xy.h.y = win->field_30.h.field_32 + 0xD;
#ifdef MEMORIES_PC
    PRM->xy.h.x = win->field_30.h.field_30 + attr_layout.x;
    PRM->xy.h.y = win->field_30.h.field_32 + attr_layout.y;
#endif
    *(u32 *)&PRM->extent = 0x00100010;
    lo = rec->field_3B << 4;
    PRM->uv.b.lo = lo;
    PRM->uv.b.hi = PRM->uv.b.hi & 0x80;
    tile = PRM->uv.b.lo;
    PRM->cxcy.h.cx = win->field_40.h.field_40 + tile;
    PRM->cxcy.h.cy = 0xFF;
    DisplayObject_SubmitPacket(PRM, CTX, arg1, arg, EXT);
}

