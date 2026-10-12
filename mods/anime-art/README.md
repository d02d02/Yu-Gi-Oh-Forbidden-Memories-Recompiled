# Anime Art

Anime-style card frames for Yu-Gi-Oh! Forbidden Memories Recompiled (v0.3.0 and later). Every big card view (the card viewer,
the duel hand, field cards, the result screens) gets a full-bleed frame: the picture is enlarged to fill it and ATK/DEF sit in the
frame's two plaques. A standalone mod: it does not need Forbidden Memories HD and does not touch the game's data.

## Install

1. Close the game. Extract the zip into the game folder (next to `memories-pc.exe`), so that `mods/anime-art/mod.json` exists.
2. Start the game. The mod is on by default; **Game > Mods** shows it. *Anime card frame* turns the frames on and off, and
   *Ritual spells: own frame* switches the ritual-spell frame between blue and the magic green.
3. Looks best at **Video > Resolution > Internal 4x**.

## Which frame a card wears

| Frame | Cards |
|---|---|
| gold | monsters |
| orange | effect monsters |
| green | spells and equips (and ritual spells, if *own frame* is off) |
| pink | traps |
| blue (ritual spell) | ritual spells |
| ritual monster (blue) | the monsters the ritual table summons (the 24 of the disc) |
| fusion (purple) | **only the cards you choose** (below) |
| Obelisk, Ra, Slifer | **only the cards you choose** |

## Choosing the frame of a card

Frames follow a card's *tag*. A card with the tag `fusion` wears the purple fusion frame, `ritual` the ritual-monster frame, and
`obelisk`, `ra`, `slifer` the god frames. Nothing in the disc is a fusion monster or a god, so **you decide**, with a small mod of
your own that gives the cards a tag. It lives next to Anime Art in the `mods` folder:

`mods/my-frames/mod.json`
```json
{
    "id": "my-frames",
    "name": "My frames",
    "min_api": 11,
    "enabled": true,
    "after": ["anime-art"],
    "cards": [
        { "replace": "Thousand Dragon",       "tags": ["fusion"] },
        { "replace": 392,                     "tags": ["fusion"] },
        { "replace": "Black Luster Soldier",  "tags": ["fusion"] },
        { "replace": 380,                     "tags": [] }
    ]
}
```

- A card is its **name** (as the game spells it) or its **id** (1 to 722; `notes/card-catalog.csv` lists them).
- `"tags": ["fusion"]` gives the frame. `"tags": []` takes a tag away (the last line above puts Blue-eyes Ultimate Dragon back to the
  plain gold frame). A card with no tag wears its kind's frame.
- A ready copy of this example is in `mods/anime-art/examples/my-anime-frames`. Copy the folder up into `mods/` and edit.
- The FM Editor's Cards tab sets the same tags (its **Tags** box) if you would rather not write JSON.

### Your cards keep their name and everything else

The entries above give no `name`, `description`, picture or stats, and so **change none of them**: the card keeps what the disc, or
another mod, gave it. One rule to know: a `replace` entry resets what an *earlier* mod gave that card (name, description, picture,
password) when it does not give it itself. Anime Art loads first of all mods for that reason, so its own tags never reset anything.
For your own mod, either keep `"after": ["anime-art"]` and tag only cards no other mod renames, or load it before the mods that do
(`"priority": -500`). If a card needs two mods to touch it, put the other mod's name/art in that card's entry too.

The game has room for 32 tags in all; Anime Art uses five (`fusion`, `ritual`, `obelisk`, `ra`, `slifer`).

## Together with Forbidden Memories HD

Only one mod's card layout is used at a time, the last one applied. Anime Art is applied after Forbidden Memories HD, so with both
installed the anime frames of Anime Art are shown; turn *Anime card frame* off here to see HD's layout again.

## Trying it quickly

With the optional *Test scenes* mod: on the title screen hold **L1** and press confirm on **Option**: a duel starts with ten monsters
on the field, listed in `test-scenes/field.json`, ready for the card viewer (TRIANGLE).

## For mod authors

- The frames, positions, ATK/DEF digits and the rules that pick a frame are the mod's `card_layout` in `mod.json`
  (see `notes/modding.md`, *Frame styles and the rules that pick them*). Add a style and a rule with your own tag to add a frame.
- The images in `textures/` have power-of-two sizes on purpose (1024x2048, 1024x1024, 256x256): the v0.3.0 engine draws a frame
  of any other size invisibly at Internal 2x/4x on some graphics drivers. `tools/pc/anime_art_textures.py` rebuilds them from the
  original artwork.
