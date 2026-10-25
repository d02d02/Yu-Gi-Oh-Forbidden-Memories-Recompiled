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
do_build() { link_tools; python tools/pc/build_game32.py --build tmp/pc/vip-e5-overlay-build > /tmp/vip-e5-job-build.log 2>&1 || { tail -15 /tmp/vip-e5-job-build.log; exit 1; }; test -f tmp/pc/vip-e5-overlay-build/memories-pc.exe; }
do_c() {
  link_tools
  LM=$(ls -d "$(cygpath -u "$PWD")"/tmp/pc/tools/llvm-mingw/*/bin); export PATH="$LM:$PATH"
  mkdir -p tmp/pc/vip-e5-overlay-ctest
  x86_64-w64-mingw32-clang -std=gnu17 -Wall -Wextra -Wpedantic -Werror -Isrc tests/pc/native_overlay_test.c src/pc/render/native_overlay.c -o tmp/pc/vip-e5-overlay-ctest/no.exe -lm
  tmp/pc/vip-e5-overlay-ctest/no.exe
}
do_py() { python tools/pc/tests/test_yfm_overlay.py; }
case "$mode" in build) do_build;; c) do_c;; py) do_py;; all) do_build; do_c; do_py;; esac
