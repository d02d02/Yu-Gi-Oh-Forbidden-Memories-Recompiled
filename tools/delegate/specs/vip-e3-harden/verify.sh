#!/usr/bin/env bash
# Supervisor-owned (protected). Usage: bash verify.sh build|c|py|all   (Git Bash on Windows, repo root = clone root)
set -e
MAIN=/c/Users/mda/games/Yu-Gi-Oh-Forbidden-Memories-Recompiled
mode="${1:-all}"
link_tools() {   # the toolchain and downloaded deps live in the main checkout's tmp/pc; share them read-only via junctions
  mkdir -p tmp/pc
  for d in tools; do
    [ -e "tmp/pc/$d" ] || cmd //c mklink //J "$(cygpath -w "$PWD/tmp/pc/$d")" "$(cygpath -w "$MAIN/tmp/pc/$d")" >/dev/null
  done
}
do_build() { link_tools; python tools/pc/build_game32.py --build tmp/pc/e3h-build > /tmp/e3h-job-build.log 2>&1 || { tail -15 /tmp/e3-job-build.log; exit 1; }; test -f tmp/pc/e3h-build/memories-pc.exe; }
do_c() {
  link_tools
  LM=$(ls -d "$PWD"/tmp/pc/tools/llvm-mingw/*/bin); export PATH="$LM:$PATH"
  mkdir -p tmp/pc/e3h-ctest
  x86_64-w64-mingw32-clang -std=gnu17 -Wall -Wextra -Wpedantic -Werror -Isrc tests/pc/native_anim_test.c src/pc/render/native_anim.c -o tmp/pc/e3h-ctest/na.exe -lm
  tmp/pc/e3h-ctest/na.exe
}
do_san() {   # same test under UBSan (trap mode needs no runtime library)
  link_tools
  LM=$(ls -d "$PWD"/tmp/pc/tools/llvm-mingw/*/bin); export PATH="$LM:$PATH"
  mkdir -p tmp/pc/e3h-ctest
  x86_64-w64-mingw32-clang -std=gnu17 -g -fsanitize=undefined -fsanitize-trap=undefined -Wall -Wextra -Wpedantic -Werror -Isrc tests/pc/native_anim_test.c src/pc/render/native_anim.c -o tmp/pc/e3h-ctest/na-san.exe -lm
  tmp/pc/e3h-ctest/na-san.exe
}
do_py() { python tools/pc/tests/test_yfm_anim.py; }
root=$(git rev-list --max-parents=0 HEAD | head -1)
untouched() { for f in src/pc/render/gl_picture.c tools/pc/yfm_control.py; do git diff --quiet "$root" -- "$f" || { echo "$f must not change"; exit 1; }; done; }
case "$mode" in build) do_build;; c) do_c;; san) do_san;; py) do_py;; all) untouched; do_build; do_c; do_san; do_py;; esac
