# Anime Art

Anime-style card frames for Yu-Gi-Oh! Forbidden Memories Recompiled (v0.3.0 and later). Every big card view (the card viewer,
the duel hand, field cards, the result screens) gets a full-bleed frame: the picture is enlarged to fill it and ATK/DEF sit in the
frame's two plaques. A standalone mod: it does not need Forbidden Memories HD and does not touch the game's data.

## Install

1. Close the game. Extract the zip into the game folder (next to `memories-pc.exe`), so that `mods/anime-art/mod.json` exists.
2. Start the game. **Everything is on by default**: the anime frames and the HD pictures. **Game > Mods > Anime Art** has the options:
   *Anime card frame* (off = the original card views), *HD assets* (off = the original game pictures), *Ritual monster frames* and *Fusion monster frames* (both off by default), and *Ritual spells: green frame*.
3. Looks best at **Video > Resolution > Internal 4x** with **HD text** on.

You do **not** need the Forbidden Memories HD pack: its pictures are inside this mod. If you already have the pack installed, nothing breaks: leave it or delete it, you see the same HD pictures either way.

## Which frame a card wears

| Frame | Cards |
|---|---|
| gold | monsters |
| orange | effect monsters |
| green | spells and equips (and ritual spells, if *own frame* is off) |
| pink | traps |
| blue (ritual spell) | ritual spells |
| ritual monster (blue) | the 24 monsters the ritual table summons, with *Ritual monster frames* **on** (off by default) |
| fusion (purple) | the well-known fusion monsters, with *Fusion monster frames* **on** (off by default), and any card you tag (below) |
| Obelisk, Ra, Slifer | **only the cards you choose** |

## Choosing the frame of a card

A card wears the frame of its **tag**. Add tags in Anime Art's own `mods/anime-art/mod.json`: open it, find the `"cards"` list (one
line per card; the 24 ritual monsters are there) and add your lines **at the end**, a comma after the previous last line. The shipped lines tag the known ritual monsters `known_ritual`
and the known fusion monsters `known_fusion` (they show only while their option is on); your own tags always show:

```json
        { "replace": 713, "tags": ["known_fusion"] },
        { "replace": "Dark Magician", "tags": ["fusion"] },
        { "replace": 1, "tags": ["slifer"] }
    ],
```

- A card is its **name** (as the game spells it) or its **id** (1 to 722; `notes/card-catalog.csv`).
- A tag is **one word** from the table below (`ritual/blue` is not a tag). `"tags": []` takes a card's tags away.
- To change a known ritual or fusion monster, edit its own line (`[]` = plain gold; a second line for the same card also works, with a harmless log note).
- An update replaces `mod.json`: keep a copy of your lines, or use a mod of your own (below).

| Tag word | Frame |
|---|---|
| `fusion` or `purple` | purple |
| `ritual` or `blue` | blue ritual monster (two plaques) |
| `obelisk` | Obelisk (blue) |
| `ra` | Ra (yellow) |
| `slifer` | Slifer (red) |

Without a tag a card wears its kind's frame (monster gold, effect monster orange, spell and equip green, trap pink, ritual spell
blue). **The gods:** the vanilla game has no Obelisk, Ra or Slifer card and Anime Art does not add any; a mod that adds them tags
them `obelisk`, `ra`, `slifer`; on vanilla you can still give any card a god frame, only for the look.

**Your own mod** (survives updates): `mods/my-frames/mod.json` with `"after": ["anime-art"]` and your lines in its own `"cards"`
list; a ready copy is in `mods/anime-art/examples/my-anime-frames`.

### Your cards keep their name and everything else

The entries above give no `name`, `description`, picture or stats, and so **change none of them**: the card keeps what the disc, or
another mod, gave it. One rule to know: a `replace` entry resets what an *earlier* mod gave that card (name, description, picture,
password) when it does not give it itself. Anime Art loads first of all mods for that reason, so its own tags never reset anything.
For your own mod, either keep `"after": ["anime-art"]` and tag only cards no other mod renames, or load it before the mods that do
(`"priority": -500`). If a card needs two mods to touch it, put the other mod's name/art in that card's entry too.

The game has room for 32 tags in all; Anime Art uses five (`fusion`, `ritual`, `obelisk`, `ra`, `slifer`).

## Together with Forbidden Memories HD

Only one mod's card layout is used at a time, the last one applied. Anime Art is applied after Forbidden Memories HD, so with both
installed the anime frames of Anime Art are shown; switch *Anime card frame* off here to see HD's layout again.

## Trying it quickly

With the optional *Test scenes* mod: on the title screen hold **L1** and press confirm on **Option**: a duel starts with ten monsters
on the field, listed in `test-scenes/field.json`, ready for the card viewer (TRIANGLE).

## For mod authors

- The frames, positions, ATK/DEF digits and the rules that pick a frame are the mod's `card_layout` in `mod.json`
  (see `notes/modding.md`, *Frame styles and the rules that pick them*). Add a style and a rule with your own tag to add a frame.
- The images in `textures/` have power-of-two sizes on purpose (1024x2048, 1024x1024, 256x256): the v0.3.0 engine draws a frame
  of any other size invisibly at Internal 2x/4x on some graphics drivers. `tools/pc/anime_art_textures.py` rebuilds them from the
  original artwork; `tools/pc/anime_art_hd_assets.py` builds the `hd` folder from the HD pack.

## Credits

HD pictures - Forbidden Memories HD by **Unchiga** and **X@nder**.
Anime/Frame Art - **d02d02** and **Hræzlyr**.

Full list in `CREDITS.txt`.
