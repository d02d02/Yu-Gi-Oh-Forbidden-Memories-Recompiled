# Job vip-e1-reload

## Goal
E1 hot reload: a control command `native reload` makes the game forget all native models and re-read manifests, with no restart. Studio use: rebuild a package, send `native reload`, see the new model.

## Facts
- `NativeRegistry_Reset()` (src/pc/render/native_registry.c ~line 663) frees entries; `NativeRegistry_Read()` re-reads on the next `NativeRegistry_Find` (native_model.c line 42; `read_done` is reset by Reset). Meshes are fetched per frame via `NativeRegistry_Mesh(NativeRegistry_Find(...))`, never kept across frames.
- Control commands run synchronously from `handle()` in src/pc/debug/control.c (~line 309: the `anim ` forwarding is the pattern to copy). Reply `ok ...` via `send_line`, errors via `send_error`.
- Command: `native reload` -> `ok native reload N` where N = entry count after the next read is NOT knowable lazily, so reply `ok native reload` only. `native get` -> `ok native entries=N bytes=B` (add `NativeRegistry_Count()` if missing).
- `MEMORIES_NATIVE_MODEL` (test switch) must survive a reload (Read re-creates it from the environment).
- Test: tests/pc/native_registry_test.c (look at how it builds a package dir). Build/check: `bash verify.sh c`; full: `bash verify.sh all`. `verify.sh` is protected.

## Hard rules
- Done only when new tests exist AND pass. Never weaken existing tests.
- Reset must not run while a draw holds a mesh pointer: the command runs between frames; add a comment stating why, and a test that Find/Mesh after Reset returns fresh data (edit the package file between).

## Limits
Edit only: `src/pc/render/native_registry.c`, `native_registry.h`, `src/pc/debug/control.c`, `tests/pc/native_registry_test.c`, `notes/studio/engine-needs.md` (E1 row only). Else write BLOCKED.

## Acceptance
`bash verify.sh all` passes. Final message: files changed, open questions.
