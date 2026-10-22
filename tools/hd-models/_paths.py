"""Where the capture scripts find the dev checkout's tools/pc (yfm_control, rigs) and the game.

Each is the first that exists of: an environment variable, a place inside this checkout, the old
workspace layout (a sibling "-dev" checkout and a shared folder next to this one)."""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HACK = REPO.parent


def _first(variable, candidates):
    if os.environ.get(variable):
        return Path(os.environ[variable])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


# YGO_DEV_TOOLS = the folder holding yfm_control.py and rigs/ (origin/dev's tools/pc)
DEV = _first("YGO_DEV_TOOLS", [REPO / "tmp/agent/dev/tools/pc",
                               HACK / "Yu-Gi-Oh-Forbidden-Memories-Recompiled-dev/tools/pc"])
# YGO_EXE = the game to run (tools/pc/build_game32.py makes tmp/pc/game32/memories-pc.exe)
EXE = _first("YGO_EXE", [REPO / "tmp/pc/game32/memories-pc.exe",
                         HACK / "shared/tools/hd-models/_exe/memories-pc.exe"])
STATE = HACK / "shared/hd-model-assets/attack-win/attack.state"
