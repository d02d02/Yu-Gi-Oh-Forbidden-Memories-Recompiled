# Job vip-e9b-timemap: time map consumed by the render-side sampler (E9), retry

Read JOB.md first (including the retry note). One item per session; the check is the line under the item. Run with RALPH_MODEL=vip on Windows.

## Items
- [ ] 1. Write NativeAnim_TimeMapClip in native_anim.c/.h and add its unit cases to tests/pc/native_anim_test.c (the numbers in JOB.md)
  check: grep -q TimeMapClip tests/pc/native_anim_test.c && bash verify.sh c
- [ ] 2. NativeMesh holds timemaps; native_registry.c parses "timemaps" like "shots" (limits, errors) with a case in tests/pc/native_registry_test.c
  check: grep -q timemaps src/pc/render/native_registry.c && grep -qi timemap tests/pc/native_registry_test.c && bash verify.sh build
- [ ] 3. NativeAnim_Choose uses the map for an act that has one (gated; no map = unchanged)
  check: test "$(grep -c NativeAnim_TimeMapClip src/pc/render/native_anim.c)" -ge 2 && bash verify.sh build
- [ ] 4. recipe.py model_json_members writes timemaps; CREATE tools/hd-models/tests/test_timemap_build.py (map present -> timemaps, absent -> no key, non-monotonic rejected)
  check: test -f tools/hd-models/tests/test_timemap_build.py && bash verify.sh py
- [ ] 5. engine-needs.md E9 row and recipe-schema.md timemap row marked done; `bash verify.sh all` passes
  check: bash verify.sh all
