"""S8 run list, marks and checks for Model Studio (headless)."""
from __future__ import annotations
from typing import Any


# --- Row definitions --------------------------------------------------------------------

# --- Status calculations ----------------------------------------------------------

def row_status(marks: list[dict[str, Any]], row_id: str, package_hash: str) -> str:
    """Return the status of a row based on its marks and package hash.

    Args:
        marks: List of mark dicts from recipe["runs"]. The list is ordered newest last.
        row_id: The row id to check.
        package_hash: Current package hash to compare against.

    Returns:
        "not run" if no mark for the row, or if the latest mark's package_hash differs from current.
        Otherwise returns the latest mark's result ("seen" or "problem").
    """
    # Find the latest mark for this row (marks are ordered newest last)
    latest_mark = None
    for mark in marks:
        if mark["row"] == row_id:
            latest_mark = mark
    if not latest_mark:
        return "not run"
    if latest_mark["package_hash"] != package_hash:
        return "not run"
    return latest_mark["result"]


def status_table(marks: list[dict[str, Any]], package_hash: str, disc_available: bool) -> dict[str, str]:
    """Return status table for all rows.

    Args:
        marks: List of mark dicts from recipe["runs"].
        package_hash: Current package hash.
        disc_available: Whether the disc is available.

    Returns:
        Dict mapping row_id to status. Rows needing the disc when unavailable are "not run".
    """
    rows = runs_rows = run_rows(disc_available)
    status = {}
    for row in runs_rows:
        row_id = row["id"]
        status[row_id] = row_status(marks, row_id, package_hash)
        # Override to "not run" if row needs disc and disc not available
        if row["needs_disc"] and not disc_available:
            status[row_id] = "not run"
    return status


# --- Problems and owning stages -----------------------------------------------------------

_SCENES = [
    ("library", "Library turntable", False),
    ("field", "Field attack", True),
    ("arena", "Arena attack", True),
]

_ACTS = ["idle", "enter", "attack", "hit", "destroyed", "win", "guard"]

_ALL_ROW_IDS = [sid for sid, _, _ in _SCENES] + [f"act:{act}" for act in _ACTS]

def run_rows(disc_available: bool) -> list[dict[str, Any]]:
    """Return the 10 scene/act rows for S8 runs.

    Args:
        disc_available: Whether the disc is available (does not affect the list).

    Returns:
        List of 10 row dicts with keys: "id", "label", "needs_disc".
    """
    rows = []
    for row_id, label, needs_disc in _SCENES:
        rows.append({"id": row_id, "label": label, "needs_disc": needs_disc})
    for act in _ACTS:
        rows.append({"id": f"act:{act}", "label": f"Act: {act}", "needs_disc": True})
    return rows


# --- Problems and owning stages -----------------------------------------------------------

_PROBLEM_STAGE = {
    "wrong size": "S4",
    "wrong timing": "S6",
    "clipping": "S5",
    "pose pop": "S5",
    "wrong look": "S7",
}

_VALID_PROBLEMS = set(_PROBLEM_STAGE.keys())
PROBLEMS = tuple(_PROBLEM_STAGE)
_VALID_RESULTS = {"seen", "problem"}


def owning_stage(problem: str) -> str:
    """Return the owning stage id for a problem.

    Args:
        problem: One of the valid problem strings.

    Returns:
        Stage id string (e.g., "S4", "S5", "S6", "S7").

    Raises:
        ValueError: If problem is not a known problem.
    """
    if problem not in _PROBLEM_STAGE:
        raise ValueError(f"Unknown problem: {problem}")
    return _PROBLEM_STAGE[problem]


def make_mark(
    row: str,
    result: str,
    package_hash: str,
    time: float,
    problem: str | None = None,
) -> dict[str, Any]:
    """Create a mark dict with validation.

    Args:
        row: Row id (must be one of the 10 known rows).
        result: "seen" or "problem".
        package_hash: Package hash string.
        time: Timestamp (float).
        problem: Problem string (required when result is "problem", must be None when "seen").

    Returns:
        Mark dict: {"row", "result", "problem", "package_hash", "time"}.

    Raises:
        ValueError: On invalid row, result, or problem combination.
    """
    if row not in _ALL_ROW_IDS:
        raise ValueError(f"Unknown row: {row}")
    if result not in _VALID_RESULTS:
        raise ValueError(f"Invalid result: {result}")
    if result == "problem":
        if problem is None:
            raise ValueError("Problem result requires a problem")
        if problem not in _VALID_PROBLEMS:
            raise ValueError(f"Invalid problem: {problem}")
    else:  # result == "seen"
        if problem is not None:
            raise ValueError("Seen result cannot have a problem")
    return {
        "row": row,
        "result": result,
        "problem": problem,
        "package_hash": package_hash,
        "time": time,
    }


def check_coverage(table: dict[str, str], disc_available: bool) -> list[dict[str, Any]]:
    """Check coverage: return finding if any rows are still not run.

    Args:
        table: Status table from status_table().
        disc_available: Whether the disc is available.

    Returns:
        List of findings (empty if all covered). Finding S8.coverage fail
        lists rows with "not run" status. Rows needing the disc are skipped
        when disc is unavailable.
    """
    from studio import audit

    rows = run_rows(disc_available)
    not_run = []
    for row in rows:
        row_id = row["id"]
        if row["needs_disc"] and not disc_available:
            continue
        if table.get(row_id) == "not run":
            not_run.append(row_id)
    if not_run:
        return [
            audit.finding(
                "S8.coverage",
                "fail",
                f"Not run yet: {', '.join(not_run)}.",
                fix="Run the remaining rows.",
            )
        ]
    return []


def check_problem(marks: list[dict[str, Any]], package_hash: str) -> list[dict[str, Any]]:
    """Check for problem rows: return findings for each row with status "problem".

    Args:
        marks: List of mark dicts from recipe["runs"].
        package_hash: Current package hash.

    Returns:
        List of findings S8.problem fail, one per problem row.
        Message: "<row>: <problem>.", fix: "Open the stage named on the row.",
        value: owning stage id.
    """
    from studio import audit

    rows = run_rows(disc_available=True)  # all rows; disc doesn't affect problem check
    findings = []
    for row in rows:
        row_id = row["id"]
        status = row_status(marks, row_id, package_hash)
        if status == "problem":
            # Find the latest mark for this row to get the problem
            latest_mark = None
            for mark in marks:
                if mark["row"] == row_id:
                    latest_mark = mark
            problem = latest_mark["problem"]
            stage = owning_stage(problem)
            findings.append(
                audit.finding(
                    "S8.problem",
                    "fail",
                    f"{row_id}: {problem}.",
                    fix="Open the stage named on the row.",
                    value=stage,
                )
            )
    return findings


def check_stale(marks: list[dict[str, Any]], stage_times: dict[str, float] | None) -> list[dict[str, Any]]:
    """Check for stale runs: return warning findings for rows older than latest stage change.

    Args:
        marks: List of mark dicts from recipe["runs"].
        stage_times: Dict mapping stage ids (S0..S7) to last-change timestamps.

    Returns:
        List of findings S8.stale-run warn, one per stale row.
        Message: "<row> ran before the latest change.", fix: "Run it again."
        Returns empty list if stage_times is empty or no rows are stale.
    """
    from studio import audit

    if not stage_times:
        return []
    latest_stage_time = max(stage_times.values())

    rows = run_rows(disc_available=True)  # all rows; disc doesn't affect stale check
    findings = []
    for row in rows:
        row_id = row["id"]
        # Find the latest mark for this row
        latest_mark = None
        for mark in marks:
            if mark["row"] == row_id:
                latest_mark = mark
        if latest_mark is None:
            continue  # never run, not stale
        if latest_mark["time"] < latest_stage_time:
            findings.append(
                audit.finding(
                    "S8.stale-run",
                    "warn",
                    f"{row_id} ran before the latest change.",
                    fix="Run it again.",
                )
            )
    return findings


def check_disc(disc_available: bool) -> list[dict[str, Any]]:
    """Check disc availability: return info finding when disc is unavailable.

    Args:
        disc_available: Whether the disc is available.

    Returns:
        List with one finding S8.disc info when disc_available is False.
        Message: "Field and arena scenes need the disc.",
        fix: "Library turntable only; set MEMORIES_DISC for field and arena."
        Returns empty list when disc_available is True.
    """
    from studio import audit

    if disc_available:
        return []
    return [
        audit.finding(
            "S8.disc",
            "info",
            "Field and arena scenes need the disc.",
            fix="Library turntable only; set MEMORIES_DISC for field and arena.",
        )
    ]


def run_s8(
    recipe: dict[str, Any],
    package_hash: str,
    disc_available: bool,
    stage_times: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Run all S8 checks and return rows, status table, and findings.

    Args:
        recipe: Recipe dict; marks come from recipe.get("runs", []).
        package_hash: Current package hash.
        disc_available: Whether the disc is available.
        stage_times: Dict of stage ids (S0..S7) to last-change timestamps, or None.

    Returns:
        Dict with keys:
            "rows": run_rows(disc_available)
            "status": status_table(marks, package_hash, disc_available)
            "findings": combined list of findings from check_coverage,
                        check_problem, check_stale, and check_disc.
    """
    marks = recipe.get("runs", [])
    rows = run_rows(disc_available)
    table = status_table(marks, package_hash, disc_available)
    findings: list[dict[str, Any]] = []
    findings.extend(check_coverage(table, disc_available))
    findings.extend(check_problem(marks, package_hash))
    findings.extend(check_stale(marks, stage_times))
    findings.extend(check_disc(disc_available))
    return {"rows": rows, "status": table, "findings": findings}