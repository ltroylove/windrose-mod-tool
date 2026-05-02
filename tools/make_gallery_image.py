from PIL import Image
import sys

src = sys.argv[1]
out = sys.argv[2]

img = Image.open(src).convert("RGB")
print(f"Source size: {img.size}")

target = (1920, 1080)

if img.size == target:
    img.save(out, format="PNG")
elif img.width / img.height > 1920 / 1080:
    # wider than target ratio — scale to width, crop height
    scale = 1920 / img.width
    new_h = int(img.height * scale)
    img = img.resize((1920, new_h), Image.LANCZOS)
    top = (new_h - 1080) // 2
    img = img.crop((0, top, 1920, top + 1080))
else:
    # taller than target ratio — scale to height, pad width with bg color
    scale = 1080 / img.height
    new_w = int(img.width * scale)
    img = img.resize((new_w, 1080), Image.LANCZOS)
    bg = Image.new("RGB", (1920, 1080), (15, 23, 42))  # dark navy matches app
    x = (1920 - new_w) // 2
    bg.paste(img, (x, 0))
    img = bg

img.save(out, format="PNG")
print(f"Saved {out} at {img.size}")
