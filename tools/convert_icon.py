import os
from PIL import Image

# Runtime + PyInstaller load the icon from assets/icon.ico (see app_window.py
# and the --icon flag in release.yml), so write the converted .ico there.
HERE = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(HERE, "..", "data", "icon_source.png")
assets_dir = os.path.join(HERE, "..", "assets")
os.makedirs(assets_dir, exist_ok=True)
out = os.path.join(assets_dir, "icon.ico")

img = Image.open(src).convert("RGBA")
sizes = [16, 32, 48, 64, 128, 256]
resized = [img.resize((s, s), Image.LANCZOS) for s in sizes]
resized[0].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=resized[1:])
print("Done:", out)
