# Job vip-e9-timemap: time map consumed by the render-side sampler (E9)

Read JOB.md first. One item per session; the check is the line under the item. Run with RALPH_MODEL=vip on Windows.

## Status
Not started.

## Items
- [ ] 1. Baseline: the game builds in this clone (junction tmp/pc/tools to the main checkout, see verify.sh)
  check: bash verify.sh build
- [ ] 2. NativeAnim_TimeMapClip in native_anim.c/.h with the unit cases from JOB.md
  check: bash verify.sh c
- [ ] 3. NativeMesh holds timemaps; native_registry.c parses "timemaps" like "shots" (limits, errors) with a case in native_registry_test.c
  check: bash verify.sh build
- [ ] 4. NativeAnim_Choose uses the map for an act that has one (gated; no map = unchanged)
  check: bash verify.sh build
- [ ] 5. Studio build writes timemaps from acts.<act>.timemap + test_timemap_build.py
  check: bash verify.sh py
- [ ] 6. engine-needs.md E9 and recipe-schema.md updated; `bash verify.sh all` passes
  check: bash verify.sh all
