from PIL import Image

src = r"c:\Projects\windrose\data\icon_source.png"
out = r"c:\Projects\windrose\data\icon.ico"

img = Image.open(src).convert("RGBA")
sizes = [16, 32, 48, 64, 128, 256]
resized = [img.resize((s, s), Image.LANCZOS) for s in sizes]
resized[0].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=resized[1:])
print("Done:", out)
