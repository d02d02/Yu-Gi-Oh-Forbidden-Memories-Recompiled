"""S9 package checks (headless): judge outputs of native_check and builds."""
from __future__ import annotations
import re
from . import audit

# Default native model budget in MB (see native_spec.BUDGET_MB).
DEFAULT_BUDGET_MB = 512

# Matches: "<mod>: 12.5 MB for all its models, ... (the game's budget: 512 MB)"
_MB_RE = re.compile(
    r"^(.+?): (\d+(?:\.\d+)?) MB for all its models.*?the game's budget: (\d+) MB\)$"
)


def parse_native_check(text: str) -> dict:
    """Parse `native_check.py` captured stdout into structured data.

    Returns {"errors": [(where, text)], "warnings": [(where, text)],
             "total_mb": float|None, "budget_mb": int|None}.
    Tolerant of blank/None text; ignores descriptive lines.
    """
    errors: list = []
    warnings: list = []
    total_mb = None
    budget_mb = None
    for line in (text or "").splitlines():
        if line.startswith("error: "):
            rest = line[len("error: "):]
            where, _, msg = rest.partition(": ")
            errors.append((where, msg))
        elif line.startswith("warning: "):
            rest = line[len("warning: "):]
            where, _, msg = rest.partition(": ")
            warnings.append((where, msg))
        else:
            m = _MB_RE.match(line)
            if m and total_mb is None:
                total_mb = float(m.group(2))
                budget_mb = int(m.group(3))
    return {"errors": errors, "warnings": warnings,
            "total_mb": total_mb, "budget_mb": budget_mb}


def check_native(parsed: dict) -> list:
    """Judge the output of `native_check.py`: fail per error, warn per warning.

    Each finding id is "S9.native_check", with message "<where>: <text>",
    value = where, and fix "Open the stage named in the message.".
    """
    out: list = []
    fix = "Open the stage named in the message."
    for where, text in parsed.get("errors", []):
        out.append(audit.finding(
            "S9.native_check", "fail", f"{where}: {text}", fix, value=where))
    for where, text in parsed.get("warnings", []):
        out.append(audit.finding(
            "S9.native_check", "warn", f"{where}: {text}", fix, value=where))
    return out


def check_budget(parsed: dict) -> list:
    """Judge the budget from native_check output.

    Finding id "S9.budget": fail when total_mb > budget_mb,
    warn when total_mb >= 0.8 * budget_mb.
    Message: "Native models use N MB of B MB." (N one decimal).
    Fix: "Lower the atlas or triangle count.".
    Returns [] when either value is None or below threshold.
    """
    total_mb = parsed.get("total_mb")
    budget_mb = parsed.get("budget_mb")
    if total_mb is None or budget_mb is None:
        return []
    out: list = []
    fix = "Lower the atlas or triangle count."
    msg = f"Native models use {total_mb:.1f} MB of {budget_mb} MB."
    if total_mb > budget_mb:
        out.append(audit.finding("S9.budget", "fail", msg, fix))
    elif total_mb >= 0.8 * budget_mb:
        out.append(audit.finding("S9.budget", "warn", msg, fix))
    return out


def check_identical(build_a: list, build_b: list) -> list:
    """Judge whether two builds are identical.

    Each build is a list of (relative_path, sha256_hex) pairs, compared as sets.
    Finding id "S9.identical": fail when sets differ.
    Message: "N file(s) differ between two builds."
    Fix: "Report this: the recipe is not deterministic."
    Value = sorted list of differing paths.
    Returns [] when equal.
    """
    set_a = {(p, h) for p, h in build_a}
    set_b = {(p, h) for p, h in build_b}
    if set_a == set_b:
        return []

    # Symmetric difference by path only
    paths_a = {p for p, _ in set_a}
    paths_b = {p for p, _ in set_b}
    diff_paths = sorted(paths_a ^ paths_b)

    msg = f"{len(diff_paths)} file(s) differ between two builds."
    fix = "Report this: the recipe is not deterministic."
    return [audit.finding("S9.identical", "fail", msg, fix, value=diff_paths)]


_PROVENANCE_KEYS = ("author", "license", "url")


def check_provenance(meta: dict) -> list:
    """Judge provenance metadata.

    Finding id "S9.provenance": fail per missing/empty key of
    author, license, url (message "Missing <key>.", fix "Fill S0.").
    Returns [] when all three are non-empty strings.
    """
    out: list = []
    fix = "Fill S0."
    for key in _PROVENANCE_KEYS:
        value = meta.get(key)
        if not isinstance(value, str) or not value.strip():
            out.append(audit.finding("S9.provenance", "fail", f"Missing {key}.", fix))
    return out


def valid_package_name(name: str) -> bool:
    """Return True if `name` is a valid S9 package name.

    Rules: 1..64 chars, only [A-Za-z0-9_-], first char not '-'.
    """
    if not isinstance(name, str) or not (1 <= len(name) <= 64):
        return False
    if name[0] == "-":
        return False
    return all(c.isalnum() or c in "_-" for c in name)


def run_s9(meta: dict, native_text: str,
           build_a: list | None = None,
           build_b: list | None = None) -> dict:
    """Run all S9 package checks (items 2-5) and return findings.

    Returns {"parsed": <parse result>, "findings": [...]}.
    Identity check (S9.identical) only runs when both build_a and build_b
    are given.
    """
    parsed = parse_native_check(native_text)
    findings: list = []
    findings += check_native(parsed)
    findings += check_budget(parsed)
    findings += check_provenance(meta)
    if build_a is not None and build_b is not None:
        findings += check_identical(build_a, build_b)
    return {"parsed": parsed, "findings": findings}
