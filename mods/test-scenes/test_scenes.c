/* The Test scenes mod (mod.json beside this file; progress.md, item 0): a
 * scene built from fixed data rather than a save state, so it is the same on
 * every build and every machine, and nothing random decides what is in it.
 *
 * Scene "field": hold L1 and confirm Option on the title menu. A duel with
 * Simon Muran on the standard field opens the usual way, and when it stops
 * for the player's first move the ten monster zones already hold the cards
 * field.json names, five a side, face up in attack position. They are real
 * duel cards, so the 3D Monsters mod stands their models on them as it would
 * for cards played by hand. Plain Cross on Option still opens Options.
 *
 * How, in the order the game gets there:
 *  - MainMenu_UpdateFrontendMenu returns 4 (Option) for both title menus, the
 *    one at boot and the one after; L1 held at the press is remembered. The SCENE
 *    event that follows arms the duel as the debug menu's DUEL does
 *    (func_80024DC8) and is handled, so Options does not open. Main_RunMenu
 *    has already faded out and torn the menu down by then.
 *  - Main_RunDuel would open the deck chest first (opponent >= 0); its first
 *    call is let through and then sent straight to Duel_InitScene, as a 2P
 *    duel is, whose way in needs nothing more than the fade already done.
 *  - Duel_ShuffleBothDecks: a field card is set up from a deck position, not
 *    from an id (Duel_SetupCardRecord), with the picture the duel fetched for
 *    that position. So all eighty positions are written after the shuffle:
 *    the chosen five at 35-39 and 75-79, which the first draw (from 0 up)
 *    never reaches, and the same five over and over before them. With no
 *    save loaded the player's deck is empty, and an empty position would
 *    send the picture fetch to sector -1.
 *  - DuelScene_UpdateHandActions, first call: the duel is waiting for the
 *    player. The cards go down the way DuelScene_UpdateResume rebuilds a
 *    field (func_80024D34, then Duel_ApplyCardObjectFlags); flags left at
 *    occupied alone are face up, attack. The player moves first, so the
 *    opponent never touches the field. */
#include "types.h"
#include "game/duel_card.h"
#include "game/duel_card_layout.h"
#include "game/card_constants.h"
#include "game/duel_apply_card_object_flags.h"
#include "pc/mods/modapi.h"
#include "pc/cards/cards.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern uint32_t gRand_dwSeed;     /* pc/rng.h: the game's Psy-Q generator */
extern u8 D_8009B26C;             /* main_mode_state.h: the running mode */
extern u8 D_8009B26E;             /* Main_RunDuel's own step */
extern u8 D_8009B268, D_8009B26D; /* main_services.h: the menu to come back to */
extern u8 D_8009B368;             /* duel_side_state.h: the mode after the duel */
extern u16 gInput_wPad1Held[];    /* input.h: the game's pad words, its own layout */
extern u16 gInput_wPad1Pressed[];
extern char gDuel_awPlayerShuffledDeck[]; /* duel_shuffle_both_decks.h */
s32 MainMenu_UpdateFrontendMenu(void);
void Main_RunDuel(void);
void Duel_ShuffleBothDecks(void *player, void *opponent);
void DuelScene_UpdateHandActions(void);
void func_80024DC8(s32 player, s32 opponent, s32 won, s32 lost);
void func_80024D34(s32 zone, s32 deck_index);

#define MENU_OPTION 4        /* main_menu_selection.h */
#define PAD_L1 0x4           /* input.h, PAD_BUTTON_L1 */
#define SIMON_MURAN 1        /* tables.c's duelist names */
#define MAIN_MODE_MENU 8     /* main_modes.h */
#define MODE_STARTED 0x40    /* a mode runner's first-call bit */
#define DUEL_FIRST_STEP 1    /* Main_RunDuel: Duel_InitScene, past the chest */
#define ZONES 5
#define FIRST_ZONE 5         /* records 0-4 are the hand, 5-9 the monsters */
#define FIELD_POSITION (DECK_SIZE - ZONES) /* 35: the first draw stops at 5 */
#define SEED 0x5EED1234u     /* anything, as long as it is always the same */

static const MemoriesModHost *host;
static s32 (*original_menu)(void);
static void (*original_run_duel)(void);
static void (*original_shuffle)(void *, void *);
static void (*original_hand)(void);

enum { IDLE, ARMED, DEALT };
static int stage;
static int l1_on_option;
static s16 cards[2][ZONES]; /* [0] the player's, [1] Simon's */

/* The numbers in "key": [a, b, c, d, e]; 0 unless all five are there. */
static int read_list(const char *text, const char *key, s16 *out)
{
    const char *at = strstr(text, key);
    char *end;
    int i;
    if (!at || !(at = strchr(at, '['))) return 0;
    at++;
    for (i = 0; i < ZONES; i++) {
        long id = strtol(at, &end, 10);
        if (end == at) return 0;
        out[i] = (s16)id;
        at = end;
        while (*at == ' ' || *at == ',' || *at == '\n' || *at == '\r' || *at == '\t') at++;
    }
    return 1;
}

static int monster(int id)
{
    return Cards_Valid(id) &&
        ((gDuel_adwCardStats[id - 1] >> CARD_STAT_TYPE_SHIFT) & CARD_STAT_TYPE_MASK) < CARD_TYPE_MAGIC;
}

/* field.json, read each time so an edit shows on the next duel. */
static int load_field(void)
{
    char text[1024];
    size_t size;
    int side, i;
    FILE *file = host->open_asset(host, "field.json");
    if (!file) {
        host->log(host, "field.json is missing");
        return 0;
    }
    size = fread(text, 1, sizeof text - 1, file);
    fclose(file);
    text[size] = '\0';
    if (!read_list(text, "\"player\"", cards[0]) || !read_list(text, "\"opponent\"", cards[1])) {
        host->log(host, "field.json needs \"player\" and \"opponent\", five card ids each");
        return 0;
    }
    for (side = 0; side < 2; side++) {
        for (i = 0; i < ZONES; i++) {
            if (!monster(cards[side][i])) {
                host->log(host, "card %d is not a monster", cards[side][i]);
                return 0;
            }
        }
    }
    return 1;
}

/* The menu answers only once its exit animation has run, by when L1 may be
 * up again: what counts is L1 at the last press before it answers. */
static s32 update_menu(void)
{
    static int l1_at_press;
    s32 result;
    if (gInput_wPad1Pressed[0] & ~PAD_L1) l1_at_press = (gInput_wPad1Held[0] & PAD_L1) != 0;
    result = original_menu();
    if (result >= 0) {
        l1_on_option = result == MENU_OPTION && l1_at_press;
        l1_at_press = 0;
    }
    return result;
}

static void scene(MemoriesModEvent *event)
{
    if (event->phase != MEMORIES_BEFORE || event->a != MENU_OPTION || !l1_on_option) return;
    l1_on_option = 0;
    if (!load_field()) return; /* Options, as if L1 had not been held */
    D_8009B268 = 1;
    D_8009B26D = MENU_OPTION; /* back on Option after the duel */
    func_80024DC8(-1, SIMON_MURAN, 0, 0);
    D_8009B368 = MAIN_MODE_MENU;
    stage = ARMED;
    event->handled = 1;
    host->log(host, "field scene armed");
}

static void run_duel(void)
{
    int first = stage == ARMED && !(D_8009B26C & MODE_STARTED);
    original_run_duel();
    if (first) D_8009B26E = DUEL_FIRST_STEP;
}

static void shuffle(void *player, void *opponent)
{
    u16 *deck = (u16 *)gDuel_awPlayerShuffledDeck;
    int i;
    if (stage == ARMED) gRand_dwSeed = SEED;
    original_shuffle(player, opponent);
    if (stage != ARMED) return;
    for (i = 0; i < DECK_SIZE; i++) {
        deck[i] = (u16)cards[0][i % ZONES];
        deck[DECK_SIZE + i] = (u16)cards[1][i % ZONES];
    }
    stage = DEALT;
}

static void hand_actions(void)
{
    int side, zone;
    if (stage == DEALT) {
        stage = IDLE;
        for (side = 0; side < 2; side++) {
            for (zone = 0; zone < ZONES; zone++) {
                int record = side * DUEL_CARD_SIDE_RECORD_COUNT + FIRST_ZONE + zone;
                func_80024D34(record, side * DECK_SIZE + FIELD_POSITION + zone);
                Duel_ApplyCardObjectFlags((DuelCardDisplayObject *)D_801A7AD8[record].object);
            }
        }
        host->log(host, "field filled");
    }
    original_hand();
}

static void forget(void)
{
    stage = IDLE;
    l1_on_option = 0;
}

static void applied(int on)
{
    if (!on) forget();
}

int MemoriesModInit(const MemoriesModHost *from, MemoriesMod *mod)
{
    if (from->api < 4) return 0;
    host = from;
    mod->api = MEMORIES_MOD_API;
    mod->applied = applied;
    mod->reset = forget;
    return host->subscribe(host, MEMORIES_EVENT_SCENE, 0, scene) &&
        host->hook(host, (void *)MainMenu_UpdateFrontendMenu, (void *)update_menu, (void **)&original_menu) &&
        host->hook(host, (void *)Main_RunDuel, (void *)run_duel, (void **)&original_run_duel) &&
        host->hook(host, (void *)Duel_ShuffleBothDecks, (void *)shuffle, (void **)&original_shuffle) &&
        host->hook(host, (void *)DuelScene_UpdateHandActions, (void *)hand_actions, (void **)&original_hand);
}
