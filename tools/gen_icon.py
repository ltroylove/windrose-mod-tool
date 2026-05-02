"""Generate BlackFlag Mod Manager icon: red skull + crossed sword/key on a black waving flag."""
from PIL import Image, ImageDraw
import os

SIZE = 256
RED = (210, 35, 35, 255)
BLACK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def new(fill=CLEAR):
    return Image.new("RGBA", (SIZE, SIZE), fill)


def composite(*layers):
    result = new()
    for layer in layers:
        result = Image.alpha_composite(result, layer)
    return result


# ---------------------------------------------------------------------------
# flag background — black with gentle wave on right edge
# ---------------------------------------------------------------------------

def draw_flag():
    img = new()
    draw = ImageDraw.Draw(img)
    W = H = SIZE
    pts = [
        (0,          0),
        (int(W*.88), 0),
        (int(W*.95), int(H*.12)),
        (int(W*.86), int(H*.28)),
        (int(W*.93), int(H*.50)),
        (int(W*.85), int(H*.72)),
        (int(W*.92), int(H*.88)),
        (int(W*.88), H),
        (0,          H),
    ]
    draw.polygon(pts, fill=(18, 18, 18, 255))
    return img


# ---------------------------------------------------------------------------
# skull — cranium, cheeks, jaw, eye sockets, nose, teeth
# ---------------------------------------------------------------------------

def draw_skull():
    img = new()
    draw = ImageDraw.Draw(img)

    # cranium
    draw.ellipse([60, 18, 196, 142], fill=RED)

    # cheekbone widening
    draw.ellipse([44,  84, 116, 152], fill=RED)
    draw.ellipse([140, 84, 212, 152], fill=RED)

    # jaw body
    draw.rectangle([76, 130, 180, 178], fill=RED)
    # round jaw bottom corners
    draw.ellipse([76, 158, 110, 178], fill=RED)
    draw.ellipse([146, 158, 180, 178], fill=RED)
    draw.rectangle([86, 165, 170, 178], fill=RED)

    # eye sockets
    draw.ellipse([78,  54, 122, 100], fill=BLACK)
    draw.ellipse([134, 54, 178, 100], fill=BLACK)

    # nose cavity
    draw.polygon([(128, 106), (110, 132), (146, 132)], fill=BLACK)

    # teeth — rounded bumps rather than bars
    # black background across jaw bottom
    draw.rectangle([82, 145, 174, 172], fill=BLACK)
    # draw 5 red teeth (rounded rectangles) on that black strip
    for i in range(5):
        tx = 84 + i * 18
        draw.rounded_rectangle([tx, 145, tx + 14, 168], radius=4, fill=RED)

    return img


# ---------------------------------------------------------------------------
# sword — horizontal, blade right, handle left
# ---------------------------------------------------------------------------

def draw_sword_h():
    img = new()
    draw = ImageDraw.Draw(img)
    cx, cy = SIZE // 2, SIZE // 2

    BL = 200   # blade length (half each side of cx)
    BW = 9     # blade half-width
    GL = 38    # guard length (half each side)
    HL = 52    # handle length
    PR = 9     # pommel radius

    blade_x0 = cx - BL // 2 + HL + 10
    blade_x1 = cx + BL // 2

    # blade (tapers to point)
    pts = [
        (blade_x0, cy - BW),
        (blade_x1 - 14, cy - BW),
        (blade_x1, cy),
        (blade_x1 - 14, cy + BW),
        (blade_x0, cy + BW),
    ]
    draw.polygon(pts, fill=RED)

    # guard
    gx = blade_x0
    draw.rectangle([gx - 5, cy - GL, gx + 5, cy + GL], fill=RED)

    # handle
    draw.rectangle([cx - BL // 2 + PR, cy - 5, gx - 5, cy + 5], fill=RED)

    # pommel
    px = cx - BL // 2 + PR
    draw.ellipse([px - PR, cy - PR, px + PR, cy + PR], fill=RED)

    return img


# ---------------------------------------------------------------------------
# key — horizontal, bow (ring) right, bit left
# ---------------------------------------------------------------------------

def draw_key_h():
    img = new()
    draw = ImageDraw.Draw(img)
    cx, cy = SIZE // 2, SIZE // 2

    RR = 28    # ring outer radius
    RI = 15    # ring inner radius (hole)
    SL = 140   # shaft length (extends left of ring)
    SW = 10    # shaft half-width
    T1L = 20   # tooth 1 length
    T2L = 14   # tooth 2 length

    ring_cx = cx + SL // 2 - RR

    # shaft
    draw.rectangle([ring_cx - SL, cy - SW // 2, ring_cx, cy + SW // 2], fill=RED)

    # teeth on bottom of shaft near the tip
    tip = ring_cx - SL
    draw.rectangle([tip + 8,  cy + SW // 2, tip + 22, cy + SW // 2 + T1L], fill=RED)
    draw.rectangle([tip + 30, cy + SW // 2, tip + 44, cy + SW // 2 + T2L], fill=RED)

    # ring (bow)
    draw.ellipse([ring_cx - RR, cy - RR, ring_cx + RR, cy + RR], fill=RED)
    draw.ellipse([ring_cx - RI, cy - RI, ring_cx + RI, cy + RI], fill=CLEAR)

    return img


# ---------------------------------------------------------------------------
# build final icon
# ---------------------------------------------------------------------------

def build_icon():
    flag = draw_flag()
    skull = draw_skull()

    # Sword: rotated 45° (points upper-right / lower-left), shifted down
    sword_h = draw_sword_h()
    sword = sword_h.rotate(45, resample=Image.BICUBIC, expand=False)

    # Key: rotated -45° (points upper-left / lower-right), shifted down
    key_h = draw_key_h()
    key = key_h.rotate(-45, resample=Image.BICUBIC, expand=False)

    # Shift crossed items so they sit just below the skull center
    def shift_down(img, dy):
        shifted = new()
        shifted.paste(img, (0, dy))
        return shifted

    sword = shift_down(sword, 68)
    key   = shift_down(key,   68)

    return composite(flag, sword, key, skull)


# ---------------------------------------------------------------------------
# save as multi-size .ico
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    icon_256 = build_icon()
    sizes = [16, 32, 48, 64, 128, 256]
    resized = [icon_256.resize((s, s), Image.LANCZOS) for s in sizes]

    out = os.path.join(os.path.dirname(__file__), "..", "data", "icon.ico")
    resized[0].save(
        out,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=resized[1:],
    )
    # also save a PNG for preview
    png_out = os.path.join(os.path.dirname(__file__), "..", "data", "icon_preview.png")
    icon_256.save(png_out)
    print(f"Icon written to {out}")
    print(f"Preview written to {png_out}")
