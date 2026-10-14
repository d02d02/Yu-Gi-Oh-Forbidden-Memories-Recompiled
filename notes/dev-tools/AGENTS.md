# AGENTS.md: how an LLM or script uses the YFM dev tools (read this first, 1 page)

**What it is:** `rigkit.py` + `pxkit.py` drive the Yu-Gi-Oh Forbidden Memories Recompiled game headlessly through its
control channel, reach a chosen situation, take screenshots, and compare pixels exactly (runs are bit-identical).
Code: `<dev worktree>\tools\pc\rigs\` (copy in `recipes\`). Needs the USA disc image in the checkout's `game\`.

**Use it when** you must see or verify what the game draws or does: a rendering/mod change, an A/B between builds,
a regression check, a bug repro, a screenshot at 1x/2x/4x. **Do not use it** for pure code logic with a C/Python unit test,
or to play the game for the user.

## Rules (hard)
1. Games run from a **private copy** of the build folder (`OUT/_exe`; rigkit does it). Never `--in-place` on the user's build:
   a running exe there makes their link fail "Permission denied".
2. **Never kill games by name** (`taskkill /IM memories-pc.exe`): it kills the user's own game. `Game` ends its own process.
3. One heavy run at a time: rigkit takes a machine-wide lock itself (waits for another run, takes over a dead owner's lock; `--lock-timeout`). Other tools (smoke.py, replay.py) do not: do not start them during a rig run. Long runs: background + log + timeout.
4. Outward actions (PR, release, Discord, push to upstream) are the user's to confirm. Pushes to `origin/dev` only if asked.
5. Never commit disc data: goldens, screenshots, states stay in `shared\` (git-ignored).
6. Check you test the build you think: `git log -1` in the worktree, exe rebuilt, mod `.o` rebuilt.

## Pick the command (python -I rigkit.py <kind> ... --repo <checkout> --out <dir>)
| You want | Kind | Cost |
|---|---|---|
| Hand + card viewer shot | `hand --deck ids [--press triangle --steps 40] --scale 4` | 5 s |
| Test-scenes duel (5+5 monsters) | `scene --set plain\|trap\|...` / `sets` (sheet of all) | 9 s each |
| Cards of any kind on the field | `duel --hand a,b,c,d,e --plays 0:up,0:down` | 6-11 s |
| An attack, shots per battle step, camera pinned | `attack --camera angle,dist --at 2,4,10 [--every 12]` | 10 s |
| A declared situation (hand, plays into columns, attack, camera, shots, checks) | `situation spec.json [--record\|--check]` | 6-9 s |
| Same situation on two builds / one setting changed | `ab spec.json --exe-a A --exe-b B [--settings-b k=v]` | 2 x spec |
| Mod x scale QA | `matrix matrix.json --golden-dir G --record\|--check` | 35 min full |
| The GAME's own 3D battle (arena, two 3D monsters, attack; NOT the 3D Monsters mod) | `arena --models 374,380 [--stage 0-6] --vb 781,1141,1861,2161 --scale 2` | ~10-20 s |
| Exact pixel diff / count / golden | `pxkit.py diff\|count\|golden` | instant |
| Replay regression gate (repo's recorded replays) | `replays --repo R --out D` (private exe, skips x64-data-mods without game\DATA) | ~5 min |
| This table, from the tool itself | `guide` | instant |

Exit codes: 0 = pass, 1 = pixel difference / failed check, 2 = a side produced no result. Outputs: PNGs, `result.json`,
`ab.json`, `ab-sheet.png`, `matrix-report.json`. Specs: `recipes\situations\*.json` (keys in `run_situation`'s docstring).

## Facts that decide success
- Make a situation once at 1x, look at 2x/4x from the saved state (about 1 s). Building at 4x directly costs 100 s.
- A state loads only in the same exe with the same enabled mods **and mod setting values**; vary things at runtime (pad-2 camera
  mailbox, `poke`), not by settings.
- Shots right after a change may not show it: `delay` (default 3 vblanks). A green cell proves nothing until you looked at the picture once.
- Native 3D battle (debug menu `3D` = main mode 1, ~2400 vblanks): fade-in to ~240, summoning circle ~480-780, monsters ~840-1740 (the scene cuts between the two), attack flash ~1860-2260. Pick monsters by poking the two property records `D_800EF658` (8 bytes each, model id = card id first) and `gDuel_bTerrain` BEFORE pressing Cross on the entry; without it the pair is Blue-Eyes White Dragon. Bit-identical on repeat.
- Battle phase: steps 3-10 are full-screen cards (no field); field art/models show at vb 0-30 and after ~228; camera pin matters there only.
- A big data mod (Duel Links art) delays boot ~120 s: set `boot_timeout`. Two mods with one id = game never connects.
- `goto("title")` returns during the logo; use rigkit's `title_menu` / `test_scene` (closed loop on the menu's green highlight; scene in ~3 s).

## Where to read more
`README.md` (index), `01-state-of-the-art.md` (all tools, measured), `03-playbook.md` (per use case), `04-testing-strategy.md`
(levels, pre-flight checklist), `05-release-strategy.md`, `02-gaps-and-roadmap.md` (what is missing), `evidence\` (proofs).

## Known gaps
`smoke.py` / `replay.py` do not take the run lock; no opponent-side slot placement; goldens per build; `x64-data-mods` replay needs an extracted `game\DATA`.
