"""Fetch card artwork from Yugipedia for the Kuriboh mod's changed cards, for the HD layer (make_hd.py --sources).

    python tools/pc/kuriboh/fetch_artwork.py <out folder> [slot=Title ...]

Asks Yugipedia's MediaWiki API (https://yugipedia.com/api.php) for a card page's files and takes one named "...artwork" (English first,
then any), at its original size, saved as <slot>.png. The artwork is Konami's: it is for the user's own local use and is never committed
(the out folder is under tmp/). Slots not given on the command line use TITLES below.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://yugipedia.com/api.php"
AGENT = "kuriboh-hd-tool/0.1 (personal local use; contact: the user)"

# The mod's slot -> the real card's page on Yugipedia ("" when the mod's card has no real counterpart: 343 Kuriboh Multiplied, a swarm of Kuribohs, and 666)
TITLES = {
    338: "Multiply", 343: "", 393: "Berserk Dragon", 394: "Dragon Master Knight", 402: "Red-Eyes Black Metal Dragon",
    484: "Ryu-Ran", 499: "Five-Headed Dragon", 666: "", 674: "Barrel Dragon", 676: "Dark Sage", 677: "Toon World",
    681: "Mirror Force", 682: "Manga Ryu-Ran", 683: "Toon Summoned Skull", 684: "Blue-Eyes Toon Dragon",
    693: "Exodia Necross", 695: "Contract with Exodia", 699: "A Deal with Dark Ruler",
}


def call(**params):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=30) as response:
        return json.load(response)


def artwork_files(title):
    """Files named like the card and "artwork": by file-name prefix (Yugipedia names them CardName-SET-LANG-RARITY-artwork.png)."""
    prefix = re.sub(r"[^A-Za-z0-9]", "", title) + "-"
    data = call(action="query", list="allimages", aiprefix=prefix, ailimit="500")
    names = ["File:" + i["name"] for i in data["query"]["allimages"]]
    art = [n for n in names if re.search(r"artwork", n, re.I) and n.lower().endswith((".png", ".jpg", ".jpeg"))]
    # the video game's 512x512 artwork first (square, clean), then English ones, then the rest
    art.sort(key=lambda n: (0 if "-MADU-EN-VG-" in n else 1, 0 if "-EN-" in n else 1, n))
    return art


def original(file_title):
    data = call(action="query", titles=file_title, prop="imageinfo", iiprop="url|size")
    for page in data["query"]["pages"].values():
        info = page.get("imageinfo")
        if info:
            return info[0]["url"], info[0]["width"], info[0]["height"]
    return None


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    titles = dict(TITLES)
    for arg in sys.argv[2:]:
        slot, _, title = arg.partition("=")
        titles[int(slot)] = title
    for slot, title in sorted(titles.items()):
        if not title:
            print(f"{slot}: no real card; keeps the enlargement")
            continue
        try:
            files = artwork_files(title)
            time.sleep(0.5)
            found = original(files[0]) if files else None
            time.sleep(0.5)
            if not found:
                print(f"{slot} {title}: no artwork file on the page ({len(files)} candidates)")
                continue
            url, w, h = found
            request = urllib.request.Request(url, headers={"User-Agent": AGENT})
            data = urllib.request.urlopen(request, timeout=60).read()
            (out / f"{slot}.png").write_bytes(data)
            print(f"{slot} {title}: {files[0]} {w}x{h} ({len(data) // 1024} KB)")
        except Exception as problem:
            print(f"{slot} {title}: failed ({problem})")


main()
