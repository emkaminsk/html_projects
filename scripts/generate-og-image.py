#!/usr/bin/env python3
"""Generate Open Graph image (1200x630px) with site branding."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "store" / "assets" / "og-image.png"

WIDTH, HEIGHT = 1200, 630

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
    # Try common sans-serif fonts available on Linux
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


def main():
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    # Diagonal gradient (approximated as vertical)
    draw_gradient(draw, WIDTH, HEIGHT, ACCENT_1, ACCENT_2)

    # Semi-transparent decorative circles (simulated with lighter color blending)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.ellipse([50, 100, 450, 500], fill=(255, 255, 255, 20))
    overlay_draw.ellipse([750, 300, 1200, 750], fill=(255, 255, 255, 15))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Text
    font_large = get_font(64)
    font_medium = get_font(32)
    font_small = get_font(24)

    white = (255, 255, 255)
    white_dim = (255, 255, 255, 200)

    # Name
    name = "Marcin Kamiński"
    bbox = draw.textbbox((0, 0), name, font=font_large)
    name_w = bbox[2] - bbox[0]
    draw.text(((WIDTH - name_w) / 2, 200), name, fill=white, font=font_large)

    # Subtitle
    subtitle = "Senior Consultant & Product Manager"
    bbox = draw.textbbox((0, 0), subtitle, font=font_medium)
    sub_w = bbox[2] - bbox[0]
    draw.text(((WIDTH - sub_w) / 2, 290), subtitle, fill=white, font=font_medium)

    # Divider line
    line_y = 350
    line_half = 80
    draw.line(
        [(WIDTH / 2 - line_half, line_y), (WIDTH / 2 + line_half, line_y)],
        fill=white,
        width=2,
    )

    # Tagline
    tagline = "Portfolio · Digital Store · Web Tools"
    bbox = draw.textbbox((0, 0), tagline, font=font_small)
    tag_w = bbox[2] - bbox[0]
    draw.text(((WIDTH - tag_w) / 2, 380), tagline, fill=white, font=font_small)

    # URL at bottom
    url = "mkhome.byst.re"
    bbox = draw.textbbox((0, 0), url, font=font_small)
    url_w = bbox[2] - bbox[0]
    draw.text(((WIDTH - url_w) / 2, 540), url, fill=(255, 255, 255, 180), font=font_small)

    img.save(OUTPUT, "PNG")
    print(f"Generated {OUTPUT} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
