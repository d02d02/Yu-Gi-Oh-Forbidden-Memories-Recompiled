# Memory cards

A copy of the real PS1 memory card image from this Windows machine's own
game (`saves/slot01.sav` under `Documents\My Games\YFM Re-Decomp`, the
non-portable user directory — `paths.c`), kept here so it travels with the
repo across machines. Standard 8192-byte PS1 card format, card slot 1.

To use it on another machine, copy `slot01.sav` into that machine's user
directory's `saves/` folder (`Paths_UserDir()`, `paths.c`): on Linux,
`$XDG_DATA_HOME/YFM Re-Decomp/saves/` or `~/.local/share/YFM Re-Decomp/saves/`;
in portable mode (a `portable.txt` beside the executable), `user/saves/`
next to the executable.

This is a memory card (in-game progress, decks, cards owned), not a save
*state* (`states/*.state`, a full emulator snapshot). Save states are not
copied here: they are large (~7 MB), build-specific (a per-mod compiled-object
hash check refuses to load a state saved by a different build — `state.c`,
`compatible_mods()`), and not needed to resume general work.

Re-export a fresh copy at any point with:

```
cp "$(python3 -c "import os;print(os.path.expanduser('~'))")/Documents/My Games/YFM Re-Decomp/saves/slot01.sav" memcards/slot01.sav   # Windows, adjust for OneDrive-redirected Documents
cp ~/.local/share/"YFM Re-Decomp"/saves/slot01.sav memcards/slot01.sav   # Linux
```
