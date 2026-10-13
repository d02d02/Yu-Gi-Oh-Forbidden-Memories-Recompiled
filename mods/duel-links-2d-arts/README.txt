Duel Links 2D Arts (v2.4, in progress)

High-resolution Duel Links style artwork for the monsters on the duel field, always facing
the camera, with an optional glow. Needs release v0.3.0 or later of YFM Re-Decomp. Does not
need 3D Monsters, and never changes a card's name.

IMPORTANT: turn 3D Monsters OFF to use this mod (Mods window). Both draw a monster on the
field and would double up, so the game will not start this mod while 3D Monsters is on.

INSTALL
Extract this zip so the "duel-links-2d-arts" folder sits inside the game's "mods" folder
(next to "3d-monsters"). Start the game, open Mods and turn on "Duel Links 2D Arts".

UPDATING FROM v2.2 OR OLDER (v2.3 reorganised the folder)
  1. Copy out of the old duel-links-2d-arts folder: your art folder (if you made one) and the
     "cards" list in mod.json (if you added entries).
  2. Delete the old duel-links-2d-arts folder and extract this zip in its place.
  3. Put your art folder's files back in art/, and paste your "cards" list back into mod.json.

SETTINGS (Mods window)
  Art size (40), Height above the card (16).
  Float height (Off) and Float length (180): turn Float height up (1 to 8) and the art floats gently
  up and down.
  Gold outline (on), Outline style (Sharp, or Flowing halos: halos that leave the line and fade
  outward), Outline thickness (Hairline, the thinnest, then 1 to 4 pixels; for halos, how far they
  travel) and Halo speed.
  Glow (off), Glow colour (Yellow, Gold, White, Red, Orange, Green, Cyan, Blue, Purple, Pink),
  Glow size (50), Glow pulse length (90).

CHANGING A CARD'S FIELD ART (no JSON, no tools)
1. Find the card's id in card-ids.txt (e.g. 22 is Summoned Skull).
2. Save your picture as a PNG with a transparent background, named after the id, in this
   mod's "art" folder:  art/22.png
3. Restart the game. Delete the file to go back to the shipped art.
Your file wins over the shipped art. Works for any card, including cards added by other
mods (ids after 722). A PNG is cropped to the card's shape by the game; for the best
quality make a .tex with prepare_art.py (art/22.tex wins over art/22.png).

CHANGING WHAT A CARD IS (spell <-> monster <-> trap, new cards)
Open this mod's mod.json and put entries in the "cards" list (it ships empty: "cards": []).
Restart the game after editing. Every key is in the game's notes/more-cards.md.
Do NOT use "replace" just to change a picture: use art/<id>.png. A "replace" entry resets
the card's name, so always give it a "name". If your changes do not show, check the Mods window
for a message about the mod.

  Spell or trap -> monster (replace card 332 "Mountain"; "model" gives it a 3D model to fight with):
    { "replace": 332, "name": "Mountain Dragon", "type": "Dragon", "attribute": "Earth",
      "level": 4, "attack": 1500, "defense": 1200, "model": "Kuriboh" }

  Monster -> spell (card 12; "effect" names the disc card whose effect it takes):
    { "replace": 12, "name": "Swamp Raigeki", "type": "Magic", "effect": "Raigeki" }

  Monster -> trap (card 30):
    { "replace": 30, "name": "Swamp Bear Trap", "type": "Trap", "effect": "Bear Trap" }

  A new card, a copy of Kuriboh:
    { "copy": "Kuriboh", "name": "Test Kuriboh", "attack": 1000, "defense": 1000 }

Keep "name" in every "replace" entry, or the card's name goes back to the disc's. A new card's
id is the next free one after 722; its field art is art/<that id>.png. A monster made a
spell or trap does nothing when played without "effect"; a spell or trap made a monster has
no 3D model without "model". Nothing of this goes in your save: remove the entries (or the mod) and restart to go back.

FOLDERS
  art/          your own pictures go here (never touched by updates)
  card-ids.txt  every card's id
  shipped-art/  the mod's own pictures; leave alone
  code/         the mod's program; leave alone
  mod.json      the settings, and the "cards" list you may edit

Art by WillliTo & d02d02. The shipped pictures were prepared (trimmed, fitted to the card
art's shape, shrunk, sharpened and defringed) with prepare_art.py from the original PNGs,
into the mod's own texture files (shipped-art/*.tex).
