"""Before | After | Difference of one region of two same-size screenshots, enlarged (nearest neighbour).
   crop_compare.py before.png after.png out.png x0 y0 x1 y1 [zoom=3] [label_before] [label_after]
Coordinates are in the images' own pixels. The difference panel is white where the pictures differ."""
import sys
from PIL import Image, ImageChops, ImageDraw
b, a, out = sys.argv[1:4]
x0, y0, x1, y1 = (int(v) for v in sys.argv[4:8])
zoom = int(sys.argv[8]) if len(sys.argv) > 8 else 3
lb = sys.argv[9] if len(sys.argv) > 9 else "before"
la = sys.argv[10] if len(sys.argv) > 10 else "after"
B = Image.open(b).convert("RGB").crop((x0, y0, x1, y1))
A = Image.open(a).convert("RGB").crop((x0, y0, x1, y1))
D = ImageChops.difference(B, A).convert("L").point(lambda v: 255 if v > 24 else 0).convert("RGB")
w, h = B.size
sheet = Image.new("RGB", (w * zoom * 3 + 40, h * zoom + 24), (30, 30, 30))
for i, (img, label) in enumerate(((B, lb), (A, la), (D, "difference"))):
    sheet.paste(img.resize((w * zoom, h * zoom), Image.NEAREST), (i * (w * zoom + 20), 24))
    ImageDraw.Draw(sheet).text((i * (w * zoom + 20) + 4, 6), label, fill=(255, 255, 255))
sheet.save(out)
print(out, sheet.size)
