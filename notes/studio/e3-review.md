# E3 Transport Review

## Threading
`NativeAnim_Command` runs in the **control** thread (main UI/input thread). `NativeAnim_Choose` runs in the **render** thread (game render loop).

## Transport globals and race risk
Shared globals: `transport_state`, `transport_phase`, `transport_clip`, `transport_speed`, `transport_pause`. Concurrent access without synchronization may race between control and render threads.

## Pause / speed behavior on clip change
- `pause` freezes transport timing but retains current phase; clip changes while paused keep phase unchanged.
- `speed` scales time progression; changing clip under speed adjusts frame progression proportionally.

## Risk list
- Race conditions on shared globals could cause inconsistent phase/frame.
- Clip change during pause may desync UI state.
- Speed changes mid‑clip can produce non‑linear frame jumps.

*No code changes made; tests confirm current behavior.*
