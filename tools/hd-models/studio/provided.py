def _finding(check, level, message, fix=""):
    """Create a finding dict as specified in JOB.md.

    Args:
        check (str): Identifier of the check.
        level (str): "fail" or "warn".
        message (str): Human‑readable description.
        fix (str, optional): Suggested fix. Defaults to "".

    Returns:
        dict: Finding dictionary.
    """
    return {"id": check, "level": level, "message": message, "fix": fix}


def validate_bones(provided, expected):
    """Validate bone name lists.

    - Missing bones (expected but not in provided) generate a *fail* finding each.
    - Extra bones (provided but not expected) generate a single *warn* finding.
    - Missing findings are ordered according to ``expected``.
    - The extra finding lists bone names sorted alphabetically and joined by commas.
    - Returns a list of finding dicts (empty when no mismatches).
    """
    # Ensure we work with collections of strings
    provided_set = set(provided)
    expected_list = list(expected)

    # Missing bones – keep order of expected
    missing = [name for name in expected_list if name not in provided_set]

    # Extra bones – sorted alphabetically for deterministic output
    extra = sorted([name for name in provided if name not in expected_list])

    findings = []
    for name in missing:
        findings.append(
            _finding(
                "provide.bone-missing",
                "fail",
                f"{name} is not in the provided file",
                fix=f"rename or add the bone {name}",
            )
        )
    if extra:
        findings.append(
            _finding(
                "provide.bone-extra",
                "warn",
                f"{len(extra)} bones are not in the model's skeleton",
                fix="",
            )
        )
        # Attach the list of extra bones as a string value (comma‑separated)
        findings[-1]["value"] = ", ".join(extra)
    return findings


def validate_rest_pose(provided, expected, pos_tol=0.02, rot_tol=0.05):
    """Validate rest pose of common bones.

    Compares position and rotation of bones present in both ``provided`` and ``expected``.
    Position differences greater than ``pos_tol`` on any axis or rotation component greater
    than ``rot_tol`` (after sign‑flipping the provided quaternion when necessary) generate a
    warning finding with id ``provide.rest-pose``.
    The order of findings follows the order of ``expected``.
    """
    findings = []
    # Iterate over expected bones preserving order
    for name, exp_data in expected.items():
        if name not in provided:
            continue  # only common bones are checked
        prov_data = provided[name]
        # Position check
        pos_exp = exp_data.get("pos")
        pos_prov = prov_data.get("pos")
        if pos_exp and pos_prov:
            if any(abs(p_e - p_p) > pos_tol for p_e, p_p in zip(pos_exp, pos_prov)):
                findings.append(
                    _finding(
                        "provide.rest-pose",
                        "warn",
                        f"{name} rest pose differs from the model",
                        fix="apply the rest pose in Blender before export",
                    )
                )
                findings[-1]["value"] = name
                continue  # skip rotation check if position already differs
        # Rotation check
        rot_exp = exp_data.get("rot")
        rot_prov = prov_data.get("rot")
        if rot_exp and rot_prov:
            # Flip sign if dot product negative
            dot = sum(e * p for e, p in zip(rot_exp, rot_prov))
            if dot < 0:
                rot_prov = tuple(-x for x in rot_prov)
            if any(abs(r_e - r_p) > rot_tol for r_e, r_p in zip(rot_exp, rot_prov)):
                findings.append(
                    _finding(
                        "provide.rest-pose",
                        "warn",
                        f"{name} rest pose differs from the model",
                        fix="apply the rest pose in Blender before export",
                    )
                )
                findings[-1]["value"] = name
    return findings


def validate(provided_bones, provided_pose, expected_bones, expected_pose):
    """Validate bones and rest pose, returning combined findings."""
    bones_findings = validate_bones(provided_bones, expected_bones)
    pose_findings = validate_rest_pose(provided_pose, expected_pose)
    return bones_findings + pose_findings


def fail_count(findings):
    """Count fail-level findings."""
    return sum(1 for f in findings if f.get("level") == "fail")

