#!/usr/bin/env python3
"""Wipe and rebuild a blank <build>-fresh-user profile under tmp/pc, with any
installed mods you keep in tmp/pc/shared-mods junctioned back in (no copies,
no duplication), and optionally the real memory card (saves/: the card
collection and duelist progress) pulled in from another profile. Then, with
--launch, start the build straight against it.

Why this exists: a real player's settings.txt/saves/mods accumulate over
time, so testing against your own profile (or a profile that was ever used
for this before) can never again answer "what does a brand-new player see".
This rebuilds a provably blank one every time instead.

Examples:
    python tools/pc/reset_fresh_user.py --build game32dbg --launch
    python tools/pc/reset_fresh_user.py --build game32master --copy-memory-card --launch
    python tools/pc/reset_fresh_user.py --build game32dbg --link-mods assets-hd my-other-mod
"""
import argparse
import ctypes
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TMP_PC = REPO_ROOT / "tmp" / "pc"
SHARED_MODS = TMP_PC / "shared-mods"
DEFAULT_SOURCE_PROFILE = Path(os.environ.get("USERPROFILE", "")) / "OneDrive" / "Documents" / "My Games" / "YFM Re-Decomp"


def _enable_windows_ansi() -> bool:
    if sys.platform != "win32":
        return sys.stdout.isatty()
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        # ENABLE_PROCESSED_OUTPUT | ENABLE_WRAP_AT_EOL_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0001 | 0x0002 | 0x0004))
    except Exception:
        return False


USE_COLOR = not os.environ.get("NO_COLOR") and _enable_windows_ansi()


def _paint(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def bold(t): return _paint("1", t)
def cyan(t): return _paint("36", t)
def green(t): return _paint("32", t)
def yellow(t): return _paint("33", t)
def red(t): return _paint("31", t)


def info(msg): print(f"  {msg}")
def ok(msg): print(f"{green('OK')}    {msg}")
def warn(msg): print(f"{yellow('WARN')}  {msg}", file=sys.stderr)
def err(msg): print(f"{red('ERROR')} {msg}", file=sys.stderr)
def section(title): print(f"\n{bold(cyan(title))}")


def safe_rmtree(path: Path) -> None:
    """Like shutil.rmtree, but a junction/symlink inside is unlinked itself
    -- never walked into -- so it can never delete a shared target's data."""
    if not path.exists():
        return
    for entry in os.scandir(path):
        p = Path(entry.path)
        if entry.is_dir(follow_symlinks=False) and (os.path.isjunction(entry.path) or os.path.islink(entry.path)):
            os.rmdir(entry.path)
        elif entry.is_dir(follow_symlinks=False):
            safe_rmtree(p)  # removes its own contents and itself
        else:
            os.unlink(entry.path)
    os.rmdir(path)


def make_junction(link: Path, target: Path) -> bool:
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        warn(f"junction {link} -> {target} failed: {result.stderr.strip()}")
        return False
    return True


def build_profile(args) -> Path:
    fresh = TMP_PC / f"{args.build}-fresh-user"
    source = Path(args.source)

    section(f"Resetting {fresh}")
    safe_rmtree(fresh)
    (fresh / "mods").mkdir(parents=True)
    ok("wiped and recreated")

    for name in args.link_mods:
        target = SHARED_MODS / name
        if target.exists():
            if make_junction(fresh / "mods" / name, target):
                ok(f"linked mod: {name}")
        else:
            warn(f"no {name} in {SHARED_MODS} -- skipped (drop it there once to make it available everywhere)")

    if args.copy_memory_card:
        section("Copying the memory card")
        saves_src = source / "saves"
        if saves_src.exists():
            shutil.copytree(saves_src, fresh / "saves")
            ok(f"saves/ from {saves_src}")
        else:
            warn(f"no saves/ at {saves_src} -- nothing to copy")
        for mcd in ("memcard1.mcd", "memcard2.mcd"):
            mcd_src = source / mcd
            if mcd_src.exists():
                shutil.copy2(mcd_src, fresh / mcd)
                ok(f"{mcd} from {source}")
        info("(states/ is deliberately never copied -- those are full engine")
        info(" snapshots tied to a build's own compiled checksums and fail to")
        info(" load across builds even at the same commit.)")

    return fresh


def launch(build: str, fresh: Path) -> None:
    exe = TMP_PC / build / "memories-pc.exe"
    section(f"Launching {build}")
    if not exe.exists():
        err(f"{exe} does not exist -- build it first, e.g.:")
        info(f"  python tools\\pc\\build_game32.py --build tmp\\pc\\{build}")
        sys.exit(1)
    env = dict(os.environ)
    env["MEMORIES_USER_DIR"] = str(fresh)
    subprocess.Popen([str(exe)], cwd=str(exe.parent), env=env,
                      creationflags=subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0)
    time.sleep(0.5)
    ok(f"started with MEMORIES_USER_DIR={fresh}")


def print_recap(build: str, fresh: Path, launched: bool) -> None:
    exe = TMP_PC / build / "memories-pc.exe"
    section("Fresh profile ready" if not launched else "Running")
    for entry in sorted(fresh.iterdir()):
        info(entry.name)
    print(f"\n{bold('To relaunch later against this same profile, without resetting it again:')}")
    print(f"\n  {cyan('PowerShell:')}")
    print(f'    $env:MEMORIES_USER_DIR = "{fresh}"')
    print(f'    & "{exe}"')
    print(f"\n  {cyan('cmd.exe:')}")
    print(f'    set MEMORIES_USER_DIR={fresh}')
    print(f'    "{exe}"')
    print(f"\n{bold('To wipe it back to blank and start over:')}")
    print(f"    python tools\\pc\\reset_fresh_user.py --build {build}")


EPILOG = f"""{bold('examples:')}
  python tools/pc/reset_fresh_user.py --build game32dbg --launch
  python tools/pc/reset_fresh_user.py --build game32master --copy-memory-card --launch
  python tools/pc/reset_fresh_user.py --build game32dbg --link-mods assets-hd my-other-mod
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="reset_fresh_user.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=bold(cyan("Rebuild a provably blank player profile for a fresh-install check.")),
        epilog=EPILOG,
    )
    parser.add_argument("--build", choices=["game32dbg", "game32master"], default="game32dbg",
                         help="which build folder under tmp/pc to use (default: game32dbg)")
    parser.add_argument("--link-mods", nargs="+", default=["assets-hd"], metavar="MOD",
                         help="installed mods to junction in from tmp/pc/shared-mods (default: assets-hd). "
                              "Space- or comma-separated.")
    parser.add_argument("--copy-memory-card", action="store_true",
                         help="also copy saves/ (card collection, duelist progress) from --from")
    parser.add_argument("--from", dest="source", default=str(DEFAULT_SOURCE_PROFILE), metavar="PATH",
                         help="profile to pull the memory card from (default: your real Documents profile)")
    parser.add_argument("--launch", action="store_true",
                         help="start the build against the fresh profile once it's ready")
    args = parser.parse_args()
    args.link_mods = [name for item in args.link_mods for name in item.split(",") if name]

    fresh = build_profile(args)

    launched = False
    if args.launch:
        launch(args.build, fresh)
        launched = True

    print_recap(args.build, fresh, launched)
    return 0


if __name__ == "__main__":
    sys.exit(main())
