# 04 Testing strategy

## Principle
Prove each claim at the **cheapest level that can falsify it**, and say which level you used. Escalate only when a lower level
cannot see the thing (GL path, feel, real hardware).

## Levels
| Level | Proves | Tool | Cost | Determinism |
|---|---|---|---|---|
| L0 | Code compiles; pure functions; data tables | build, CTests (CI), tiny probe exe against the real source file (`..\pc-headless-testing.md`), Python unit tests | s-min | D1 |
| L1 | Game logic/state is as expected | `Game` + `state()/field()/duel()/peek` assertions | 3-10 s | D1 |
| L2 | Nothing else moved | frame hashes: `smoke.py`, replays (`replay.py run`), `hash` before/after | s-min | D1 (same build) |
| L3 | It looks right / differs only where intended | scenario at 1x, then 2x/4x from a 1x state; A/B sheet + % pixels | 3-10 s per shot | D1 |
| L4 | Not slower | same scenario on A and B: vblanks (deterministic) + wall s (repeat 3) | 20-60 s | vblanks D1, wall noisy |
| L5 | Real window / GL path / audio / pacing | `MEMORIES_WINDOW_SHOT`, user plays | human | D0 |
| L6 | Works for a player on the official release | fresh install matrix (official / fix pack / PR), own user dir | human | D0 |

Rule of thumb: logic bugs live at L1, rendering bugs at L3 (+L5 for GL), mod releases need L3 + L6, engine PRs need L2 + L3 + L4.

## Determinism ladder (what you can rely on)
- **Deterministic:** channel-driven run on the virtual clock (`MEMORIES_DETERMINISTIC=1`, `Game` sets it), same exe, same settings, same inputs, same disc: frames, RAM (except `g_SDValue`, spu/libspu chunks), RNG (the seed is in states).
- **Not deterministic:** audio mixer thread, real-time clock sessions, real windows, host keys (F5/F7/menus not recorded), different build/exe, different internal scale for *timing*, `MODE_AT` skipping real setup.
- Different Internal scale changes pixels but not game logic: states made at 1x replay logic identically at 4x.

## Evidence rules
1. Every claim in a PR / release note is labelled **measured** (script output kept) or **seen by eye** (who, which build).
2. Keep per scenario: command line, exe path + build id + commit, settings, mods+versions, outputs (PNG, sheet, `result.json`). Save under `tmp/rig/<tag>/` in the worktree, or `Desktop\<release>\evidence\` for releases.
3. A/B always from the same state/scenario, both sides built from the exact commits named; never compare a dirty tree to a clean one without saying so.
4. Say what you did NOT verify (Linux/mac/Android builds, CTests on Windows, combinations not run). That list is part of the evidence.
5. User's rules for visual work: small increments, one screen, an A/B picture each step, minimal verbosity, no long runs before a proof.

## Pre-flight checklist (run before any scripted session)
- [ ] `git -C <wt> branch --show-current` and `git log --oneline -1` = the commit you think you built (wrong branch tests old code silently).
- [ ] Exe rebuilt after the last source change; mod `.o` rebuilt (`build_mod.py`, llvm-mingw on PATH via `cygpath -u`, `MEMORIES_MOD_CC=clang.exe`).
- [ ] Run games from a PRIVATE COPY of the build folder (rigkit does it: `OUT/_exe`; `--in-place` to opt out). A running exe in the user's build folder makes their link fail "Permission denied". NEVER `taskkill /IM memories-pc.exe` (kills the user's own game too); `Game` ends its own process, kill by PID if needed.
- [ ] No `memories-pc.exe` running (`taskkill /F /IM memories-pc.exe`); stale one makes the link fail "Permission denied".
- [ ] Disc present (`game\ygofm-orig-usa.bin` or `MEMORIES_DISC`); USA image, not `rom\ygo\*.iso`.
- [ ] Throwaway `MEMORIES_USER_DIR` (Game does it); never the real `Documents\My Games\YFM Re-Decomp`.
- [ ] Mods on/off exactly as intended (`mod.<id>=1` + its sub-keys; remember `3d-monsters` conflicts).
- [ ] State files are for THIS exe (build id in the name) AND the same enabled mods with the same mod setting values (`Mods_Signature`); vary things at runtime (pad-2 mailbox, `poke`), not by settings, between loads of one state.
- [ ] Do not run two games at once for a gate (`smoke.py`): main's smoke failed one case (`summon`, exit 0xFFFFFFFF) while other games ran and passed alone.
- [ ] Long runs in background with a log file and a timeout; kill orphans afterwards.
- [ ] PowerShell: `$null = $p.Handle` before `WaitForExit`; `"${Set}:"` not `"$Set:"`.

## Test data catalog
- Cards (`notes/card-catalog.csv`: id,name,type,attribute,level,...): 374 Gate Guardian (11*), 380 Blue-eyes Ultimate Dragon (12*), 332 Mountain (spell), 683 Bear Trap, 364 Black Luster Soldier (ritual monster), 670 Black Luster Ritual; ritual pairs 357 Yamadron/666, 360 Zera the Mant/671, 356 Super War-lion/673; 686 Widespread Ruin (always-trigger trap); 100 plain monster; 30 Slifer, 150 Ra (gold/slifer frame tags); 5 Ryukishin.
- Decks: `MEMORIES_DEBUG_DECK` syntax `ids` and `a-b` ranges, repeated to 40; `"374,380,332,683,364,670"` = frame/viewer kinds.
- Scenes: dev `mods/test-scenes/sets/*.json` (plain, trap, equip, magic, ritual, modified, mixed, trapritual).
- Fusion script: Hitotsu-me Giant (3) + Baby Dragon (4) -> Koumori Dragon (input in `progress.md`).
- Opponents: `goto("duel", opponent=1|3)`; extra duelists 40-55 (Kuriboh port).
- Settings of interest: `internal_scale` 1/2/4, `mod.forbidden-memories-hd(.full_bleed)`, `mod.anime-art(.full_bleed)`, `mod.3d-monsters`, `pgxp`.

## Suggested regression set (build it incrementally, P1 in `02`)
Per mod/feature a fixed list of (scenario x scale x settings) -> frame hash + PNG, stored with the release. Minimum for any rendering change:
hand @1x, card viewer @1x+2x, attack @1x (timing), scene `mixed` @2x, vanilla (`mod=0`) hand @1x byte-identical.

## Results ledger
One line per investigation appended to the relevant topic note: `date | build/commit | scenario | level | result | evidence path`.
Remove lines when the commit message becomes the history.
