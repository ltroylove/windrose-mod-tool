"""
Resize a batch of images to 1920x1080 (center-crop or letterbox).

Usage:
    python batch_gallery.py src1.png dst1.png src2.png dst2.png ...
"""
import sys
from PIL import Image


def to_1920x1080(src: str, out: str) -> None:
    img = Image.open(src).convert("RGB")
    target_w, target_h = 1920, 1080
    if img.width / img.height > target_w / target_h:
        scale = target_w / img.width
        new_h = int(img.height * scale)
        img = img.resize((target_w, new_h), Image.LANCZOS)
        top = (new_h - target_h) // 2
        img = img.crop((0, top, target_w, top + target_h))
    else:
        scale = target_h / img.height
        new_w = int(img.width * scale)
        img = img.resize((new_w, target_h), Image.LANCZOS)
        bg = Image.new("RGB", (target_w, target_h), (15, 23, 42))
        bg.paste(img, ((target_w - new_w) // 2, 0))
        img = bg
    img.save(out, format="PNG")
    print(f"{src} -> {out}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or len(args) % 2 != 0:
        print("Usage: batch_gallery.py src1 dst1 [src2 dst2 ...]")
        sys.exit(1)
    for i in range(0, len(args), 2):
        to_1920x1080(args[i], args[i + 1])
