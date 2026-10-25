#!/usr/bin/env bash
# Supervisor-owned (protected). Usage: bash verify.sh c|all   (Git Bash on Windows, repo root = clone root)
set -e
MAIN=/c/Users/mda/games/Yu-Gi-Oh-Forbidden-Memories-Recompiled
mode="${1:-all}"
link_tools() {
  mkdir -p tmp/pc
  [ -e tmp/pc/tools ] || cmd //c mklink //J "$(cygpath -w "$PWD/tmp/pc/tools")" "$(cygpath -w "$MAIN/tmp/pc/tools")" >/dev/null
}
do_c() {
  link_tools
  LM=$(ls -d "$(cygpath -u "$PWD")"/tmp/pc/tools/llvm-mingw/*/bin); export PATH="$LM:$PATH"
  D="$MAIN/tmp/pc/win32-deps"; mkdir -p tmp/pc/e1r-ctest
  i686-w64-mingw32-clang -std=gnu17 -Wall -Wextra -Werror -Isrc -Itests/pc -I"$D/include" tests/pc/native_registry_test.c \
    src/pc/render/native_registry.c src/pc/render/native_format.c src/pc/render/native_anim.c src/pc/render/native_cinematic.c \
    src/pc/mods/json.c src/pc/platform/paths.c src/pc/compat/fs.c -o tmp/pc/e1r-ctest/nr.exe "$D/lib/libpng.a" "$D/lib/libzs.a" -lm
  tmp/pc/e1r-ctest/nr.exe
}
case "$mode" in c|all) do_c;; esac
