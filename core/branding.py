from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageDraw

from .qr import render_qr

TEAL_TOP = (20, 184, 166)
TEAL_BOTTOM = (13, 116, 108)
ORANGE = (249, 115, 22)
WHITE = (255, 255, 255)

CLOUD_CIRCLES = [(33, 56, 16), (53, 46, 20), (69, 60, 13)]
CLOUD_RECT = (17, 54, 83, 74, 10)
PAW_PAD = (50, 62, 8.5, 6.5)
PAW_TOES = [(39.5, 52.5, 3.3), (45.5, 46.5, 3.5), (54.5, 46.5, 3.5), (60.5, 52.5, 3.3)]


@lru_cache(maxsize=8)
def logo_image(size=512):
    s = 4 * size / 100
    big = int(100 * s)

    grad = Image.new("RGB", (1, big))
    for y in range(big):
        t = y / (big - 1)
        grad.putpixel((0, y), tuple(int(a + (b - a) * t) for a, b in zip(TEAL_TOP, TEAL_BOTTOM)))
    grad = grad.resize((big, big))
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, big - 1, big - 1], radius=int(24 * s), fill=255)
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(img)
    for cx, cy, r in CLOUD_CIRCLES:
        d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=WHITE)
    x0, y0, x1, y1, r = CLOUD_RECT
    d.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=r * s, fill=WHITE)
    cx, cy, rx, ry = PAW_PAD
    d.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=ORANGE)
    for cx, cy, r in PAW_TOES:
        d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=ORANGE)
    return img.resize((size, size), Image.LANCZOS)


def shop_qr_png(shop, scale=16):
    img = render_qr(shop.public_url, scale=scale, logo=logo_image(512))
    buf = BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()
