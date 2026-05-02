from PIL import Image
import sys

files = [
    (r"C:\Users\Dad\.claude\image-cache\e85ad7da-1b46-4a0b-a01c-0f3ca9cc9b00\5.png", r"C:\Projects\windrose\Docs\Nexus-Deploy\screenshot-game-tuning.png"),
    (r"C:\Users\Dad\.claude\image-cache\e85ad7da-1b46-4a0b-a01c-0f3ca9cc9b00\6.png", r"C:\Projects\windrose\Docs\Nexus-Deploy\screenshot-installed-mods.png"),
    (r"C:\Users\Dad\.claude\image-cache\e85ad7da-1b46-4a0b-a01c-0f3ca9cc9b00\7.png", r"C:\Projects\windrose\Docs\Nexus-Deploy\screenshot-mod-library.png"),
    (r"C:\Users\Dad\.claude\image-cache\e85ad7da-1b46-4a0b-a01c-0f3ca9cc9b00\8.png", r"C:\Projects\windrose\Docs\Nexus-Deploy\screenshot-server.png"),
    (r"C:\Users\Dad\.claude\image-cache\e85ad7da-1b46-4a0b-a01c-0f3ca9cc9b00\9.png", r"C:\Projects\windrose\Docs\Nexus-Deploy\screenshot-settings.png"),
]

def to_1920x1080(src, out):
    img = Image.open(src).convert("RGB")
    print(f"{src.split(chr(92))[-1]} — source: {img.size}")
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
    print(f"  -> saved {out.split(chr(92))[-1]} at {img.size}")

for src, out in files:
    to_1920x1080(src, out)
