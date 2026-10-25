# Job j5-transport-tests

## Items
- [ ] 1. Edge cases of Transport: double start, play/pause/scrub order, current() returns None when anim_get has no or bad "at", shot path creation, max_steps=0, state passed as Path
  check: python -I tools/hd-models/tests/test_j5_transport_1.py
- [ ] 2. Resolutions: offered resolutions for S2.map, S1.skin, S2.skin are exactly provide.file; unknown check ids offer nothing; the result is stable across calls
  check: python -I tools/hd-models/tests/test_j5_transport_2.py
