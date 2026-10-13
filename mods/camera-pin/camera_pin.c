/* Camera pin (test tool): holds the duel camera at a chosen angle and distance during chosen scene phases,
 * so a scripted run can look at an attack, a summon or the field from a known viewpoint. Off until a pin is set.
 * The pin is set by a setting (angle 0..4095 in a 4096-unit turn, 1024 is the duel's usual view; distance 200..1400,
 * 600 usual) or at run time through pad 2, which the control channel can write and which a save state does not
 * contain (mod settings are part of a state's signature, so they cannot change between loads of one state):
 *   0x4000 | angle (12 bits)   set the angle      0x8000 | distance (11 bits)  set the distance
 *   0x2000                     clear the pin      (hold each value one VBlank, then 0)
 * PHASES is a bit mask over the scene phase (gDuel_wSceneStateFlags & 0xF; 9 battle, 5 field, 4 hand): default all.
 * Like the Hand camera mod it moves the view state's own numbers and re-applies ViewState_ApplyOrbit, which the
 * game only does itself while one of its own tweens runs; writing the numbers alone changes nothing. */
#include "types.h"
#include "psyq/libgte.h"
#include "psyq/libgpu.h"
#include "psyq/libgs.h"
#include "game/view_state.h"
#include "game/view_state_orbit.h"
#include "pc/mods/modapi.h"
#include <stdint.h>

extern ViewState D_800F2848;
extern u16 gDuel_wSceneStateFlags;
extern void (*D_800E9DB0[4])(void); /* the frame service callbacks */
extern void Duel_DrawFieldCards(void);

#define PHASE_MASK 0xF
#define TURN 0x1000

static const MemoriesModHost *host;
static int pin_angle = -1, pin_distance;

static void frame(void)
{
    uint16_t mailbox = host->pad(host, 1);
    int phases = host->setting(host, "phases", 0xFFFF);
    int angle, distance;
    if (mailbox & 0x2000) pin_angle = -1, pin_distance = 0;
    else if (mailbox & 0x4000) pin_angle = mailbox & 0xFFF;
    else if (mailbox & 0x8000) pin_distance = mailbox & 0x7FF;
    angle = pin_angle >= 0 ? pin_angle : host->setting(host, "angle", -1);
    distance = pin_distance ? pin_distance : host->setting(host, "distance", 0);
    if (angle < 0 && !distance) return;
    if (D_800E9DB0[3] != Duel_DrawFieldCards) return; /* not in the duel scene */
    if (!((phases >> (gDuel_wSceneStateFlags & PHASE_MASK)) & 1)) return;
    if (angle >= 0) D_800F2848.angle = (s16)(angle % TURN);
    if (distance) D_800F2848.field_00 = (s16)distance;
    ViewState_ApplyOrbit();
}

int MemoriesModInit(const MemoriesModHost *from, MemoriesMod *mod)
{
    host = from;
    mod->api = MEMORIES_MOD_API;
    mod->frame = frame;
    return 1;
}
