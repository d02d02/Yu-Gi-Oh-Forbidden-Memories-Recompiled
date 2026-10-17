# Native models: laptop test results

This branch holds only test results for `feat/native-models-plug-and-play`; it shares no files with the code.
The agent wrote these templates (and one correction: milestones are branches, not tags) and never writes here again: it
only reads (fetch) what you push.

## How to use it

Keep it in a folder of its own, beside your checkout, so the code checkout is never switched away:

```
git fetch origin test-results
git worktree add ../native-test-results test-results
```

For a milestone N:

1. Build the milestone: `git fetch origin && git switch -c test-mN origin/milestone/native-mN` in your code checkout
   (a milestone branch is frozen: the agent never pushes to it again).
2. Fill in `mN.md` here (one line per item: PASS, FAIL or NOT RUN, and a note).
3. Put screenshots, clips and logs in a folder `mN/` here and name them in the item's note.
4. `git add -A && git commit -m "M<N> results" && git push` from this folder.

Partial results are fine: push what you have, add the rest later. A milestone made for a fix (`milestone/native-m1.1`) gets its own
section at the bottom of the same file.
