import os
from PIL import Image, ImageDraw, ImageFont


def _load_font(size):
    """Try a few common bundled font paths; fall back to PIL's default if none exist."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def make_banner_thumbnail(source_path, title, artist, out_path=None):
    """
    Overlay a dark gradient band at the bottom of the thumbnail with the song
    title and artist, similar to a polished banner-style anime post.
    """
    out_path = out_path or source_path.replace(".jpg", "_banner.jpg")

    img = Image.open(source_path).convert("RGB")
    w, h = img.size

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    band_height = int(h * 0.32)
    for i in range(band_height):
        alpha = int(200 * (i / band_height))
        y = h - band_height + i
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

    title_font = _load_font(max(22, w // 22))
    artist_font = _load_font(max(16, w // 32))

    padding = int(w * 0.04)
    title_y = h - band_height + int(band_height * 0.30)
    artist_y = h - band_height + int(band_height * 0.68)

    draw.text((padding, title_y), title, font=title_font, fill=(255, 255, 255, 255))
    draw.text((padding, artist_y), artist, font=artist_font, fill=(230, 230, 230, 255))

    combined = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    combined.save(out_path, quality=90)
    return out_path
