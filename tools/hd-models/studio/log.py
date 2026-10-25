"""Studio session log: one line per step, size-capped so long runs never grow it past ~2 MB.

    log.attach(dir)                  the file is dir/studio.log (rotates at 512 KB, keeps 3 older files)
    log.event("S5", "run", "3 findings")
    log.error("build", exc)          the line is also kept as log.last_error for the window
"""
import logging
import logging.handlers
from pathlib import Path

MAX_BYTES = 512 * 1024
BACKUPS = 3
MAX_LINE = 1000         # a long message (a build's output) is cut to head and tail

class _Handler(logging.handlers.RotatingFileHandler):
    """Closes the file after every line: events are sparse, and an open handle blocks deleting the folder on Windows."""

    def emit(self, record):
        super().emit(record)
        self.close()


_logger = logging.getLogger("studio")
_logger.setLevel(logging.INFO)
_logger.propagate = False
_handler = None
last_error = ""


def attach(directory):
    """Write to directory/studio.log from now on (replaces the previous file); returns the path."""
    global _handler
    detach()
    path = Path(directory) / "studio.log"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _handler = _Handler(path, maxBytes=MAX_BYTES, backupCount=BACKUPS, encoding="utf-8", delay=True)
    except OSError:
        return None     # no log is better than no Studio
    _handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S"))
    _logger.addHandler(_handler)
    return path


def detach():
    global _handler
    if _handler is not None:
        _logger.removeHandler(_handler)
        _handler.close()
        _handler = None


def clip(text):
    text = " | ".join(str(text).split("\n")).strip()
    if len(text) <= MAX_LINE:
        return text
    half = MAX_LINE // 2
    return f"{text[:half]} ...[{len(text) - MAX_LINE} chars cut]... {text[-half:]}"


def event(stage, what, detail=""):
    _logger.info("%-6s %-10s %s", stage, what, clip(detail))


def error(what, exc):
    """Log a failure and remember it for the window."""
    global last_error
    last_error = f"{what}: {exc}"
    _logger.error("ERROR  %-10s %s: %s", what, type(exc).__name__, clip(exc))
