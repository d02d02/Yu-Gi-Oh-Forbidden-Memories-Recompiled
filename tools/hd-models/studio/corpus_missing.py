"""Missing model corpus utilities.

Provides build_missing(kind, path) to generate synthetic GLB files that are missing
specific data required for the Studio's audit pipeline.

According to JOB.md, three kinds are supported:
- "no-clips": skeleton and mesh present, but no animation clips.
- "no-skeleton": no skeletal data (empty bone list), mesh present.
- "no-skin": skeleton present but mesh not skinned to it.

Any other kind raises NotImplementedError.
"""

from pathlib import Path
from studio import corpus

MISSING_KINDS = ("no-clips", "no-skeleton", "no-skin")



def missing_report(path: Path) -> dict:
    """Return a report dict for a missing‑data GLB.

    The report contains:
    * ``findings`` – a list of each finding dict from ``audit.audit_all`` over all stages,
      with an added ``"stage"`` key indicating the audit stage.
    * ``offered`` – a mapping from finding id to the list returned by
      ``resolutions.offered`` for every finding whose ``level`` is ``"fail"`` or ``"warn"``.
    """
    import sys, pathlib
    # Ensure local imports work like in corpus.py
    module_dir = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(module_dir))
    import audit
    import resolutions
    path = pathlib.Path(path)
    # Run audit
    results = audit.audit_all(str(path))
    findings = []
    offered = {}
    for stage, data in results.items():
        for f in data.get('findings', []):
            # copy finding and add stage
            rec = dict(f)
            rec['stage'] = stage
            findings.append(rec)
            level = f.get('level')
            if level in ('fail', 'warn'):
                offered[f.get('id')] = resolutions.offered(f)
    return {'findings': findings, 'offered': offered}

def build_missing(kind: str, path: Path) -> None:
    """Create a GLB at *path* that is missing data according to *kind*.

    Parameters
    ----------
    kind: str
        One of the values in ``MISSING_KINDS``. Unknown values raise ``NotImplementedError``.
    path: pathlib.Path
        Destination file path for the generated GLB.
    """
    if kind not in MISSING_KINDS:
        raise NotImplementedError(f"Unknown missing kind: {kind}")

    if kind == "no-clips":
        corpus.write_glb(path, corpus.humanoid_bones(), skinned=True, clips=False, meshes=1)
    elif kind == "no-skeleton":
        corpus.write_glb(path, [], skinned=False, clips=False, meshes=1)
    elif kind == "no-skin":
        corpus.write_glb(path, corpus.humanoid_bones(), skinned=False, clips=False, meshes=1)
