#!/usr/bin/env python3
"""Reassemble a split model directory back into a single record binary.
Usage: reassemble_model.py <split_dir> <out_record.bin>
"""
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
import model_record as mr

def reassemble(split_dir, out_path):
    offsets = mr.phase_offsets()
    # Ensure we follow PHASES order
    parts = []
    for name, _ in mr.PHASES:
        filename = Path(split_dir) / f"{name.replace(' ', '_')}.bin"
        parts.append(filename.read_bytes())
    data = b"".join(parts)
    assert len(data) == mr.RECORD_BYTES, f"size {len(data)} != {mr.RECORD_BYTES}"
    Path(out_path).write_bytes(data)

if __name__ == "__main__":
    if len(sys.argv)!=3:
        print('Usage: reassemble_model.py <split_dir> <out_record.bin>')
        sys.exit(1)
    reassemble(sys.argv[1], sys.argv[2])
