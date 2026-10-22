"""Save a game state at vblank K after the attack commit (attack-win/attack.state), so later runs load straight there.
python -I save_moment.py STATE_IN STATE_OUT K   (build-specific: a state only loads in the build that wrote it)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from _paths import HACK, DEV, EXE, STATE
sys.path.insert(0, str(DEV)); import yfm_control as yc
a, b, k = sys.argv[1], sys.argv[2], int(sys.argv[3])
with yc.Game(executable=str(EXE), out=Path(b).parent / "save-moment", headless=True,
             settings={"mod.3d-monsters": 1, "mod.3d-monsters.attack": 0, "mod.2d-monsters": 0, "mod.camera-pin": 1, "internal_scale": 1}) as g:
    g.load(a); g.step(k); g.save(b); print("saved", b, g.info())
