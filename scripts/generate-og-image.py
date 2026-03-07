#!/usr/bin/env python3
"""Generate Open Graph image (1200x630px) with site branding.

Renders at 2x internally and downscales for sharper text on social platforms.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "store" / "assets" / "og-image.png"

WIDTH, HEIGHT = 1200, 630
SCALE = 2  # Render at 2x for sharper text

# Brand colors from styles.css
ACCENT_1 = (102, 126, 234)  # #667eea
ACCENT_2 = (118, 75, 162)   # #764ba2


def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def draw_gradient(draw, width, height, c1, c2):
    for y in range(height):
        t = y / height
        color = lerp_color(c1, c2, t)
        draw.line([(0, y), (width, y)], fill=color)


def get_font(size):
    for name in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def center_text(draw, y, text, font, fill, canvas_width):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((canvas_width - text_w) / 2, y), text, fill=fill, font=font)


def main():
    w, h = WIDTH * SCALE, HEIGHT * SCALE
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    draw_gradient(draw, w, h, ACCENT_1, ACCENT_2)

    # Decorative circles
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.ellipse([100, 200, 900, 1000], fill=(255, 255, 255, 20))
    overlay_draw.ellipse([1500, 600, 2400, 1500], fill=(255, 255, 255, 15))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    font_large = get_font(128)
    font_medium = get_font(64)
    font_small = get_font(48)

    white = (255, 255, 255)

    center_text(draw, 400, "Marcin Kamiński", font_large, white, w)
    center_text(draw, 580, "Senior Consultant & Product Manager", font_medium, white, w)

    # Divider
    line_y = 700
    line_half = 160
    draw.line([(w / 2 - line_half, line_y), (w / 2 + line_half, line_y)], fill=white, width=4)

    center_text(draw, 760, "Portfolio · Digital Store · Web Tools", font_small, white, w)
    center_text(draw, 1080, "mkhome.byst.re", font_small, (255, 255, 255, 200), w)

    # Downscale to final size with high-quality resampling
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)

    img.save(OUTPUT, "PNG", optimize=True)
    print(f"Generated {OUTPUT} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
