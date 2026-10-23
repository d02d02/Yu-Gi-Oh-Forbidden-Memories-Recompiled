#!/usr/bin/env python3
"""CLI to run audit on a glb file. Prints JSON to stdout, exit 0 on success, exit 2 on missing glb."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from studio import audit
import recipe


def main():
    if len(sys.argv) < 2:
        print("usage: run_audit.py GLB [RECIPE] [--stage S1]", file=sys.stderr)
        return 2

    glb_path = Path(sys.argv[1])
    if not glb_path.exists():
        print(f"glb not found: {glb_path}", file=sys.stderr)
        return 2

    recipe_path = None
    stage = None
    args = sys.argv[2:]
    if args and args[0] == "--stage":
        if len(args) < 2:
            print("--stage requires a stage id", file=sys.stderr)
            return 2
        stage = args[1]
        args = args[2:]
    if args:
        recipe_path = Path(args[0])

    rec = None
    if recipe_path and recipe_path.exists():
        rec = recipe.load(recipe_path)

    try:
        if stage:
            model = audit.load_model(glb_path)
            result = audit.audit_stage(stage, model, rec)
        else:
            result = audit.audit_all(glb_path, rec)
    except audit.AuditError as e:
        if stage:
            result = {"findings": [audit.finding("S0.load", "fail", str(e), "")], "data": {}}
        else:
            result = {"S0": {"findings": [audit.finding("S0.load", "fail", str(e), "")], "data": {}}}

    json.dump(result, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())