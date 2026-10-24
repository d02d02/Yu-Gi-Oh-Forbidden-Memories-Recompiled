"""S9 build step: turn a recipe into a new_native_mod.py command, run it
twice through an injectable runner, hash the outputs and feed package.run_s9.
Headless; no tkinter."""

import hashlib
import subprocess
import sys
from pathlib import Path

import recipe
from studio import audit, package

# Map each known recipe dest -> its command-line flag.
_FLAGS = {
    "clips": "--clips",
    "clips_from": "--clips-from",
    "rig": "--rig",
    "root": "--root",
    "root_height": "--root-height",
    "origin_height": "--origin-height",
    "height": "--height",
    "extent": "--extent",
    "scale": "--scale",
    "texture_max": "--texture-max",
    "follow": "--follow",
    "procedural": "--procedural",
    "no_center": "--no-center",
    "keep_root_motion": "--keep-root-motion",
    "no_pbr": "--no-pbr",
    "name": "--name",
    "author": "--author",
    "license": "--license",
}

# Dests whose value is a boolean: bare flag when True, nothing when False.
_BOOL_DESTS = {"no_center", "keep_root_motion", "no_pbr"}
# Dests whose value is a list: repeat the flag per item.
_LIST_DESTS = {"follow", "procedural"}


def flags(args):
    """Turn a dict of dests into a sorted list of command tokens.

    Raises ValueError on an unknown dest.  Booleans: bare flag when True,
    nothing when False.  Lists repeat the flag.  Other values become
    [flag, str(value)].
    """
    tokens = []
    for dest in sorted(args):
        if dest not in _FLAGS:
            raise ValueError(f"unknown dest: {dest}")
        flag = _FLAGS[dest]
        value = args[dest]
        if dest in _BOOL_DESTS:
            if value:
                tokens.append(flag)
        elif dest in _LIST_DESTS:
            for item in value:
                tokens.extend((flag, str(item)))
        else:
            tokens.extend((flag, str(value)))
    return tokens


_NEW_NATIVE_MOD = Path(__file__).resolve().parent.parent / "new_native_mod.py"


def command(rec, glb, out_dir, cards):
    """Return the full argv to invoke new_native_mod.py for the given recipe.

    Parameters:
        rec: Recipe dict (not the recipe module).
        glb: Path to the .glb file.
        out_dir: Output directory path.
        cards: List of card numbers (ints).

    Raises ValueError if pkg.name is invalid or cards is empty.
    Omits the '--' separator when there are no native_convert flags.
    """
    if not cards:
        raise ValueError("cards must not be empty")

    pkg_name = rec.get("pkg", {}).get("name")
    if not pkg_name:
        pkg_name = Path(glb).stem
    if not package.valid_package_name(pkg_name):
        raise ValueError(f"invalid package name: {pkg_name}")

    argv = [
        sys.executable,
        "-I",
        str(_NEW_NATIVE_MOD),
        str(glb),
    ]
    for card in cards:
        argv.extend(("--card", str(card)))
    argv.extend(("--out", str(out_dir), "--id", pkg_name))

    native_args = recipe.convert_args(rec)
    if native_args:
        argv.append("--")
        argv.extend(flags(native_args))

    return argv


def hash_tree(folder):
    """Return a sorted list of (relative_posix_path, sha256_hex) pairs for
    every file under *folder*.

    Returns [] when *folder* does not exist."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    pairs = []
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            rel = path.relative_to(folder).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            pairs.append((rel, digest))
    pairs.sort(key=lambda p: p[0])
    return pairs


def real_runner(argv):
    """Run *argv* exactly and return (returncode, text).

    Captures stdout, merges stderr into stdout, decodes as UTF-8."""
    proc = subprocess.run(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout


def build_twice(rec, glb, out_dir, cards, runner=real_runner):
    """Build into out_dir/"a" then out_dir/"b", hashing each output tree.

    Stops after the first nonzero return code.  Returns a dict with keys
    "ok", "text" (text of build a), "build_a", "build_b" and "returncode"
    (the last executed code).  build_b is [] when build b did not run.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dir_a = out_dir / "a"
    rc_a, text_a = runner(command(rec, glb, dir_a, cards))
    if rc_a != 0:
        return {
            "ok": False,
            "text": text_a,
            "build_a": hash_tree(dir_a),
            "build_b": [],
            "returncode": rc_a,
        }

    dir_b = out_dir / "b"
    rc_b, _text_b = runner(command(rec, glb, dir_b, cards))
    return {
        "ok": rc_b == 0,
        "text": text_a,
        "build_a": hash_tree(dir_a),
        "build_b": hash_tree(dir_b),
        "returncode": rc_b,
    }


def run_build_s9(rec, glb, out_dir, cards, runner=real_runner):
    """Run build_twice and feed results to package.run_s9.

    On build failure (that["ok"] is False), returns a dict with a
    "build" key containing the build_twice result and a "findings"
    list containing a single S9.build fail finding with the return code.

    On build success, returns a dict with "build" and "findings"
    from package.run_s9(meta, text, build_a, build_b).
    """
    that = build_twice(rec, glb, out_dir, cards, runner)
    if not that["ok"]:
        return {
            "build": that,
            "findings": [
                audit.finding(
                    "S9.build",
                    "fail",
                    f"The build failed (code {that['returncode']}).",
                    "Open the stage named in the log.",
                )
            ],
        }
    return {
        "build": that,
        "findings": package.run_s9(
            rec.get("meta", {}),
            that["text"],
            that["build_a"],
            that["build_b"],
        )["findings"],
    }
