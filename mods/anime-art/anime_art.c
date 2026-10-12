/* Anime Art's one piece of code: it makes "Anime card frame" start ON.
 *
 * The engine reads a card layout's own `full_bleed` setting as 0 until the player has saved it (card_layout.c: "Off until the
 * player turns it on"); the `default` a manifest declares is only what the Mods window shows. So a data mod alone starts with its
 * frame off while the window says on. This asks for the setting at start and, only if the player has never set it (no value
 * stored, no environment override), stores 1. After that the player's own choice is what is read: switching it off in the Mods
 * window stores 0 and stays off. Nothing else is touched, and the mod does no drawing or hooking.
 *
 * Built against host API 2 (setting, set_setting): it runs on every game that has a mod API at all. */
#include "pc/mods/modapi.h"

int MemoriesModInit(const MemoriesModHost *host, MemoriesMod *mod)
{
    mod->api = 2;
    if (host->setting(host, "full_bleed", -1) < 0) host->set_setting(host, "full_bleed", 1);
    return 1;
}
