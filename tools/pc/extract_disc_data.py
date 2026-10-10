#!/usr/bin/env python3
"""Copy the retail disc's DATA files (WA_MRG.MRG, SU.MRG, MODEL.MRG ...) out of a .bin image,
for the tools that read a `--data game/DATA` folder (extract_images.py, hd_screen_pack.py).

    python tools/pc/extract_disc_data.py <disc.bin> <out folder> [name ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fm_editor.disc import DiscImage  # noqa: E402

DEFAULT = ("WA_MRG.MRG", "SU.MRG", "MODEL.MRG")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    with DiscImage(sys.argv[1]) as disc:
        for name in sys.argv[3:] or DEFAULT:
            found = disc.find("DATA/" + name)
            if not found:
                sys.exit(f"DATA/{name} is not on the disc")
            (out / name).write_bytes(disc.read(*found))
            print(name, found[1])


if __name__ == "__main__":
    main()
