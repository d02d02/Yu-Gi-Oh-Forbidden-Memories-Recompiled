#!/usr/bin/env bash
# Create a delegated job: a shallow, WSL-native clone on its own branch holding the job spec.
#   wsl bash /mnt/c/Users/mda/games/Yu-Gi-Oh-Forbidden-Memories-Recompiled/tools/delegate/job-new.sh <id> <spec-dir> [base-ref]
# <spec-dir> holds progress.md (short: goal, pointer to JOB.md, checklist), JOB.md (full brief), verify.sh (acceptance).
# Optional paths.txt in the spec dir limits the checkout (less to wander through); the spec files are always added.
# The Windows checkout is never touched; the job's commits come back with `git fetch` (see notes/delegation.md).
set -eu
export MSYS_NO_PATHCONV=1   # Git Bash would turn the leading / of sparse-checkout patterns into a Windows path
. "$(dirname "$0")/env.sh"
id="${1:?job id}"; spec="${2:?spec dir}"; base="${3:-feat/native-models-plug-and-play}"
SRC="$DG_SRC"; [ "$DG_WIN" = 1 ] && SRC="$(cygpath -m "$SRC")"
W="$HOME/work/$id"
[ -e "$W" ] && { echo "job exists: $W" >&2; exit 1; }
for f in progress.md JOB.md verify.sh; do [ -f "$spec/$f" ] || { echo "spec needs $f" >&2; exit 1; }; done
mkdir -p "$HOME/work"
if [ -f "$spec/paths.txt" ]; then   # optional: only these paths are checked out (gitignore-style patterns, one per line)
  git clone -q --depth 1 --no-checkout --branch "$base" "file://$SRC" "$W"
  git -C "$W" sparse-checkout set --no-cone --stdin < <(cat "$spec/paths.txt"; echo /progress.md; echo /JOB.md; echo /verify.sh)
  git -C "$W" checkout -q
else
  git clone -q --depth 1 --branch "$base" "file://$SRC" "$W"
fi
git -C "$W" config user.name "ralph-bot"; git -C "$W" config user.email "ralph-bot@localhost"
git -C "$W" config core.autocrlf false
git -C "$W" switch -q -c "ralph/$id"
git -C "$W" rev-parse HEAD > "$HOME/work/$id.base"
cp "$spec/progress.md" "$spec/JOB.md" "$spec/verify.sh" "$W/"
git -C "$W" add progress.md JOB.md verify.sh
git -C "$W" commit -q -m "job $id: plan"
echo "job $id ready: $W (branch ralph/$id, base $(cut -c1-9 "$HOME/work/$id.base"))"
