#ifndef MEMORIES_PC_NATIVE_REGISTRY_H
#define MEMORIES_PC_NATIVE_REGISTRY_H
/* The native models the applied mods supply (native_model.h draws them; notes/native-models.md is the modder's side):
 *
 *   manifest "native_models": [{"cards": [364], "package": "angel/model.json"},   a package (model.json, below)
 *                              {"card": 1, "file": "dragon.hdm"},                 or a bare HDM4 file
 *                              {"model": 363, "file": "angel.hdm"}]               a disc model id (card id - 1)
 *
 * An entry names the cards it is for (or a disc model), may carry a "setting" as other rule lists do
 * (Mods_EntryUsed), and is only read when a slot first needs it: a mod with models for every card costs nothing
 * until they show. A model that cannot be used is a note beside its mod, and the slot falls back to an earlier
 * mod's model for the same card, else to the disc model.
 *
 *   model.json  {"format": 1, "model": "angel.hdm",
 *                "textures": {"base": "base.png", "normal": "normal.png", "metal_roughness": "mr.png"},
 *                "clips": {"idle": "Idle", "enter": "Taunt", "attack": "Sword_Attack", "hit": "Hit_Chest",
 *                          "destroyed": "Death01", "win": "Victory", "guard": "Block"},
 *                "strike": {"attack": [11, 30]}, "scale": 100,
 *                "look": {"ambient": 20, "light_gain": 100, "normal_strength": 180, "highlight": 100, "flip_green": 1,
 *                         "camera_near": 1000, "camera_keep": 50, "camera_scale": 100},
 *                "name": "...", "author": "...", "license": "...", "source": "...", "converter": {...}}
 *
 * Every member but "model" is optional. Files are named from the package's folder and stay inside the mod. A PNG
 * replaces the model file's own texture (so a texture is swapped without converting again); textures above the cap
 * (MEMORIES_NATIVE_TEXTURE_MAX, default 2048) are halved until they fit. "clips" maps acts (NativeAct) to the model's
 * clips (an act left out plays the default names); "strike" lists the attack clip's frames where its blows land;
 * "shots" are camera moves in the arena (native_cinematic.h); "scale" is in percent, about the soles; "offset": [x, y, z] moves it along its own axes (x right, y down, z forward, game
 * units, whole numbers from -2000 to 2000); "look" is in percent (camera_near in game units, flip_green 0/1) under the
 * mod's settings of the same names, under the environment (MEMORIES_NATIVE_*, MEMORIES_ARENA_CAMERA_*).
 *
 * MEMORIES_NATIVE_MODEL=<file.hdm or model.json> is a test switch: that model for disc model
 * MEMORIES_NATIVE_MODEL_ID (default 363, Black Luster Soldier; -2: every duel slot), over every mod's.
 *
 * Memory: the models read stay for the run (a mod with native models needs a restart to change). Their total is kept
 * under MEMORIES_NATIVE_BUDGET_MB (default 512: the game is a 32-bit program); a model past it is not read. */
#include "pc/render/native_model.h"
#include <stddef.h>

#define NATIVE_REGISTRY_MAX 64    /* entries in all the manifests */
#define NATIVE_REGISTRY_CARDS 64  /* cards per entry */
#define NATIVE_TEST_MODEL 363     /* MEMORIES_NATIVE_MODEL without MEMORIES_NATIVE_MODEL_ID */

/* The manifests and the test switch, once (the first slot draw). */
void NativeRegistry_Read(void);
/* The model for a slot drawing disc model `model` (>= 0) for `card` (0: unknown), read now if it was not; -1: none.
 * The test switch first, then an entry naming the card, then one for the disc model (an entry with cards stands for
 * their disc models when the card is unknown); among equals the later mod's. */
int NativeRegistry_Find(int model, int card);
/* The mesh of a model Find returned, or NULL. */
const NativeMesh *NativeRegistry_Mesh(int id);
/* What a note calls it: "<mod>: native_models[2]" or the test switch's file. */
const char *NativeRegistry_Name(int id);
/* The bytes the models read hold. */
size_t NativeRegistry_Bytes(void);
/* How many entries the manifests and the test switch hold (0 until Read, i.e. a Find). */
int NativeRegistry_Count(void);
/* Everything freed and forgotten; the next Read starts again (tests, and `native reload`). */
void NativeRegistry_Reset(void);
#endif
