"""Headless S9 "Export report" for the Model Studio: a Markdown summary of a
model's stages, findings, build and scene runs. No tkinter.

Findings are dicts {"id": "S4.footprint", "level": "fail"|"warn"|"info",
"message": str, "fix": str, optionally "value"}. A finding's stage is the part
of its id before the first dot (e.g. "S4")."""

STAGES = [
    ("S0", "Intake"),
    ("S1", "Skeleton"),
    ("S2", "Skeleton"),
    ("S3", "Materials"),
    ("S4", "Size"),
    ("S5", "Clips"),
    ("S6", "Timing"),
    ("S7", "Look"),
    ("S8", "Validate"),
    ("S9", "Package"),
]

GROUPS = {
    "S0": "Prepare", "S1": "Prepare", "S2": "Prepare", "S3": "Prepare",
    "S4": "Fit", "S5": "Fit", "S6": "Fit",
    "S7": "Judge", "S8": "Judge", "S9": "Ship",
}


def stage_status(findings_for_stage, acks):
    """Status of one stage given its list of findings.

    None (stage never run) -> "not run". A fail finding makes the stage "fail"
    (never hidden by acknowledgement). Otherwise "warn" if any warn, else
    "pass". acks is accepted for API symmetry but does not change status.
    """
    if findings_for_stage is None:
        return "not run"
    has_fail = False
    has_warn = False
    for f in findings_for_stage:
        level = f.get("level")
        if level == "fail":
            has_fail = True
        elif level == "warn":
            has_warn = True
    if has_fail:
        return "fail"
    if has_warn:
        return "warn"
    return "pass"


def stage_lines(stage, findings_for_stage, acks):
    """Markdown lines for one stage.

    Returns a heading like "### S4 Size - fail" followed by one bullet per
    finding, or "Not run." for a stage that never ran, or "No findings." for
    a stage with no findings.
    """
    # Look up stage name
    stage_name = ""
    for s, name in STAGES:
        if s == stage:
            stage_name = name
            break

    if findings_for_stage is None:
        return ["Not run."]

    if not findings_for_stage:
        return ["No findings."]

    status = stage_status(findings_for_stage, acks)
    lines = [f"### {stage} {stage_name} - {status}"]
    for f in findings_for_stage:
        level = f.get("level", "info")
        msg = f.get("message", "")
        fix = f.get("fix", "")
        bullet = f"- **{level}** {f['id']}: {msg}"
        if fix:
            bullet += f" ({fix})"
        if level == "warn" and f["id"] in acks:
            bullet += " [acknowledged]"
        lines.append(bullet)
    return lines


def summary_table(findings, acks):
    """Markdown table lines for all 10 stages.

    Columns: Group | Stage | Name | Status (header, separator, then one row
    per stage in order). A stage absent from findings is "not run".
    """
    lines = ["| Group | Stage | Name | Status |",
             "| --- | --- | --- | --- |"]
    for stage, name in STAGES:
        status = stage_status(findings.get(stage), acks)
        lines.append(f"| {GROUPS[stage]} | {stage} | {name} | {status} |")
    return lines


def build_lines(build):
    """Markdown lines for the build artifact.

    None -> "Not built.". Otherwise "Build: ok|failed", the file count, and one
    bullet per file "- path sha256[:12]"; at most the first 20 files, then a
    "- ... N more" summary line for the remainder.
    """
    if build is None:
        return ["Not built."]

    ok = "ok" if build.get("ok") else "failed"
    files = build.get("files", [])
    lines = [f"Build: {ok}", f"Files: {len(files)}"]
    shown = files[:20]
    for path, sha in shown:
        lines.append(f"- {path} {sha[:12]}")
    extra = len(files) - len(shown)
    if extra > 0:
        lines.append(f"- ... {extra} more")
    return lines


def runs_lines(runs):
    """Markdown lines for scene run marks.

    None or empty -> "No scene runs recorded.". Otherwise one bullet per row:
    "- row: seen" for a seen mark, or "- row: problem (<problem>)" for a
    problem mark. Only the latest mark (by time) per row is kept, and rows are
    emitted in first-seen order.
    """
    if not runs:
        return ["No scene runs recorded."]

    latest = {}
    order = []
    for m in runs:
        row = m["row"]
        if row not in latest:
            order.append(row)
            latest[row] = m
        elif m["time"] > latest[row]["time"]:
            latest[row] = m

    lines = []
    for row in order:
        m = latest[row]
        if m["result"] == "problem":
            prob = m.get("problem") or ""
            lines.append(f"- {row}: problem ({prob})")
        else:
            lines.append(f"- {row}: seen")
    return lines


def stand_in_lines(entries):
    """Return markdown lines for stand-in entries.

    * If ``entries`` is ``None`` or empty, return a single line:
      ``["None: every part is authentic."]``.
    * Otherwise, for each entry dict in order, produce a line of the form::

        - <check>( <value>)? : <desc>[, source <source>]

      where ``<desc>`` is ``"tool-made stand-in"`` when ``kind`` is ``"fallback"``
      and ``"accepted without it"`` when ``kind`` is ``"accept"``.
      ``<value>`` is included only if the entry's ``value`` is not ``None``.
      ``source`` is appended if ``data`` contains a ``"source"`` key.
    """
    if not entries:
        return ["None: every part is authentic."]
    lines = []
    for e in entries:
        check = e.get("check", "")
        value = e.get("value")
        kind = e.get("kind", "")
        data = e.get("data", {}) or {}
        # Base description
        if kind == "fallback":
            desc = "tool-made stand-in"
        elif kind == "accept":
            desc = "accepted without it"
        else:
            desc = ""
        line = f"- {check}"
        if value is not None:
            line += f" ({value})"
        line += f" : {desc}"
        source = data.get("source")
        if source:
            line += f", source {source}"
        lines.append(line)
    return lines
def render(findings, acks, meta, build, runs, stand_ins=None):
    """Render the full export report as a Markdown string ending with a newline."""
    name = (meta.get("name") if meta else None) or "unnamed"
    out = [f"# Model report: {name}"]

    parts = []
    if meta:
        if meta.get("author"):
            parts.append(f"Author: {meta['author']}")
        if meta.get("license"):
            parts.append(f"License: {meta['license']}")
        if meta.get("url"):
            parts.append(f"URL: {meta['url']}")
    out.append(", ".join(parts) if parts else "Provenance missing.")

    out.append("")
    out.append("## Summary")
    out.extend(summary_table(findings, acks))

    # Stand-ins section
    out.append("")
    out.append("## Stand-ins")
    out.extend(stand_in_lines(stand_ins))

    out.append("")
    out.append("## Stages")
    first = True
    for stage, _name in STAGES:
        fl = findings.get(stage) if findings else None
        if not first:
            out.append("")
        first = False
        out.extend(stage_lines(stage, fl, acks))

    out.append("")
    out.append("## Build")
    out.extend(build_lines(build))

    out.append("")
    out.append("## Scene runs")
    out.extend(runs_lines(runs))

    return "\n".join(out) + "\n"
