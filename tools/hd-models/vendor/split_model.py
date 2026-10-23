#!/usr/bin/env python3
"""Split a model record into its 17 phase files.
Usage: split_model.py <record.bin> <out-dir>
"""
import sys, os
from pathlib import Path

# import helpers from model_record
sys.path.append(str(Path(__file__).parent))
import model_record as mr

def split(record_path, out_dir):
    data = Path(record_path).read_bytes()
    offsets = mr.phase_offsets()
    os.makedirs(out_dir, exist_ok=True)
    for name,_ in mr.PHASES:
        at, length = offsets[name]
        (Path(out_dir)/f"{name.replace(' ','_')}.bin").write_bytes(data[at:at+length])

if __name__ == "__main__":
    if len(sys.argv)!=3:
        print('Usage: split_model.py <record.bin> <out-dir>')
        sys.exit(1)
    split(sys.argv[1], sys.argv[2])
