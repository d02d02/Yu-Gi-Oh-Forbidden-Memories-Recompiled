# Job e7-stream: frame stream over the control channel (Route B, E7), phase 1

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. `Frame` dataclass and `FrameStream.frames()` with change detection (hash), rate cap, max_frames, close(); fake-game tests for: yields only changed frames, rate cap via injected clock, max_frames, close, ControlError ends the stream and sets error
  check: python tools/hd-models/tests/test_studio_stream.py
- [ ] 2. `stats()` and `latest()`; tests incl. a slow consumer (no pile-up: frames skipped, not queued)
  check: python tools/hd-models/tests/test_studio_stream.py
- [ ] 3. `stream_demo.py --selftest` on the fake game (valid PNG written with zlib/struct), plus the real-game mode
  check: python tools/hd-models/stream_demo.py --selftest
- [ ] 4. Notes: E7 row in engine-needs.md says phase 1 done (shot+hash polling, measured rate = from selftest only, real rate to be measured by the user)
  check: grep -q "E7.*phase 1" notes/studio/engine-needs.md
