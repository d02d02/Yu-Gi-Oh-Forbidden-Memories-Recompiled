# Job vip-e1-reload: native reload command

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. Registry: `NativeRegistry_Count()` (entries) if missing; test: build package A, Find works, rewrite package file (change `scale`), `NativeRegistry_Reset()`, Find+Mesh shows the new value, count stable; test-switch env survives Reset.
  check: bash verify.sh c && grep -q "reload" tests/pc/native_registry_test.c
- [ ] 2. control.c: `native reload` and `native get` forwarded like `anim `; reply format per JOB.md; unknown subcommand -> `err native: unknown`.
  check: bash verify.sh c && grep -q '"native ' src/pc/debug/control.c
- [ ] 3. Full gate and engine-needs.md E1 row marked done.
  check: bash verify.sh all
