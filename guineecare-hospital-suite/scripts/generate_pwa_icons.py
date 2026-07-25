"""Generate simple PWA icons for GuinéeCare — v1.3.0.

Creates 192×192 and 512×512 PNG icons with the brand color (#0f766e teal)
and a stylized "GC" monogram. No external assets required.
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "/home/z/my-project/guineecare-hospital-suite/frontend/public/icons"
BRAND_COLOR = (15, 118, 110)  # #0f766e teal-700
WHITE = (255, 255, 255)


def find_font(size: int) -> ImageFont.FreeTypeFont:
    """Try to load a bold sans-serif font, fall back to default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def make_icon(size: int, output_path: str) -> None:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded square background
    margin = size // 16
    radius = size // 8
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=BRAND_COLOR,
    )

    # Monogram "GC" — centered, white
    font_size = int(size * 0.45)
    font = find_font(font_size)
    text = "GC"
    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2 - bbox[0]
    y = (size - text_h) // 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=WHITE)

    img.save(output_path, "PNG", optimize=True)
    print(f"  ✓ {output_path} ({size}×{size})")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating PWA icons in {OUTPUT_DIR}")
    make_icon(192, os.path.join(OUTPUT_DIR, "icon-192.png"))
    make_icon(512, os.path.join(OUTPUT_DIR, "icon-512.png"))
    # Also generate a favicon
    make_icon(32, os.path.join(OUTPUT_DIR, "favicon-32.png"))
    print("✅ Done")


if __name__ == "__main__":
    main()
