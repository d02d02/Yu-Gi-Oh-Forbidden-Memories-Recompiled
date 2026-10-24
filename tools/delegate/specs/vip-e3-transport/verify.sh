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
do_build() { link_tools; python tools/pc/build_game32.py --build tmp/pc/e3-build > /tmp/e3-job-build.log 2>&1 || { tail -15 /tmp/e3-job-build.log; exit 1; }; test -f tmp/pc/e3-build/memories-pc.exe; }
do_c() {
  link_tools
  LM=$(ls -d "$PWD"/tmp/pc/tools/llvm-mingw/*/bin); export PATH="$LM:$PATH"
  mkdir -p tmp/pc/e3-ctest
  x86_64-w64-mingw32-clang -std=gnu17 -Wall -Wextra -Wpedantic -Werror -Isrc tests/pc/native_anim_test.c src/pc/render/native_anim.c -o tmp/pc/e3-ctest/na.exe -lm
  tmp/pc/e3-ctest/na.exe
}
do_py() { python tools/pc/tests/test_yfm_anim.py; }
case "$mode" in build) do_build;; c) do_c;; py) do_py;; all) do_build; do_c; do_py;; esac
