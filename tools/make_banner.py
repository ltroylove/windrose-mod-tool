from PIL import Image

src = r"c:\Projects\windrose\Docs\Nexus-Deploy\BlackFlag mod manager interface design.png"
out = r"c:\Projects\windrose\Docs\Nexus-Deploy\banner-1300x372.png"

img = Image.open(src).convert("RGB")
print(f"Source size: {img.size}")

target_w, target_h = 1300, 372

# Scale to fit entirely within banner (no cropping), pad sides with dark bg
scale = min(target_w / img.width, target_h / img.height)
new_w = int(img.width * scale)
new_h = int(img.height * scale)
img = img.resize((new_w, new_h), Image.LANCZOS)
bg = Image.new("RGB", (target_w, target_h), (10, 20, 30))
bg.paste(img, ((target_w - new_w) // 2, (target_h - new_h) // 2))
img = bg

img.save(out, format="PNG")
print(f"Saved {out} at {img.size}")
