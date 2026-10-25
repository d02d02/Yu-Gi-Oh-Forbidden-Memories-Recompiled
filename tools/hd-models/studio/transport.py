"""Route B transport for the Studio tab (headless): one live game paused on a saved state, scrubbed by phase.

The game object is injected (yfm_control.Game or a fake): it needs load, anim_resume, anim_pause, anim_phase, anim_get,
step and shot, as transport_demo.py uses them.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

PHASE_MIN, PHASE_MAX = 0.0, 1.0


def clamp(phase: float) -> float:
    return max(PHASE_MIN, min(PHASE_MAX, float(phase)))


class Transport:
    def __init__(self, game: Any, state: str | Path, max_steps: int = 600):
        self.game, self.state, self.max_steps = game, state, max_steps
        self.phase = 0.0
        self.paused = False
        self.ready = False

    def start(self) -> bool:
        """Load the saved attack state and run until the attack scene draws, then pause. False if it never did."""
        self.game.load(self.state)
        self.game.anim_resume()
        for _ in range(self.max_steps):
            self.game.step(1)
            if int(self.game.anim_get().get("al", 0) or 0) > 0:
                self.game.anim_pause()
                self.game.step(1)
                self.paused = self.ready = True
                return True
        return False

    def scrub(self, phase: float) -> float:
        """Pause if needed, go to `phase` (clamped to 0..1) and return the phase the engine reports."""
        if not self.ready:
            raise RuntimeError("the transport has not started")
        if not self.paused:
            self.pause()
        self.phase = clamp(phase)
        self.game.anim_phase(self.phase)
        self.game.step(1)
        return self.current()

    def current(self) -> float | None:
        try:
            return float(self.game.anim_get().get("at", 0.0))
        except (TypeError, ValueError):
            return None

    def pause(self) -> None:
        self.game.anim_pause()
        self.paused = True

    def play(self) -> None:
        if not self.ready:
            raise RuntimeError("the transport has not started")
        self.game.anim_resume()
        self.paused = False

    def shot(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.game.shot(path)
        return path
