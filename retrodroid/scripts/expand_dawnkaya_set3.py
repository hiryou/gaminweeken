#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import subprocess
from io import BytesIO

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
from rembg import remove


REPO_ROOT = Path(__file__).resolve().parents[1]
THEME_DIR = REPO_ROOT / "artifacts" / "themes" / "dawnkaya"
KAYA_SET3_DIR = Path.home() / "Downloads" / "kaya-set3"
BASE_GAMELIST_BG = THEME_DIR / "assets" / "kaya" / "gamelist-bg-kaya-wave-mural.png"
VARIANT_DIR = THEME_DIR / "assets" / "kaya" / "gamelist-ai-variants"
SYSTEM_BG_OUT = THEME_DIR / "assets" / "kaya" / "system-bg-kaya-wave-mural-v3.png"
PREVIEW_OUT = THEME_DIR / "preview-gamelist-variants-set3.jpg"
SYSTEMS_FILE = REPO_ROOT / "tmp" / "dawnkaya-active-systems.txt"
SYSTEM_BG_SOURCE = KAYA_SET3_DIR / "PXL_20230907_135529744.jpg"


def source_photos() -> list[Path]:
    photos = [
        path
        for path in sorted(KAYA_SET3_DIR.iterdir())
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]
    if not photos:
        raise SystemExit(f"No Kaya set3 images found under {KAYA_SET3_DIR}")
    return photos


def rembg_cutout(source: Image.Image) -> Image.Image:
    buffer = BytesIO()
    source.save(buffer, format="PNG")
    cutout = Image.open(BytesIO(remove(buffer.getvalue()))).convert("RGBA")
    alpha = cutout.getchannel("A")
    alpha = ImageOps.autocontrast(alpha, cutoff=2)
    alpha = ImageEnhance.Contrast(alpha).enhance(1.9)
    alpha = alpha.filter(ImageFilter.GaussianBlur(1.6))
    alpha = ImageEnhance.Brightness(alpha).enhance(1.45)
    cutout.putalpha(alpha)
    return cutout


def crop_to_subject(cutout: Image.Image) -> Image.Image:
    alpha = cutout.getchannel("A")
    bbox = alpha.point(lambda value: 255 if value > 24 else 0).getbbox()
    if bbox is None:
        return cutout
    left, top, right, bottom = bbox
    pad = 28
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(alpha.width, right + pad)
    bottom = min(alpha.height, bottom + pad)
    box = (left, top, right, bottom)
    return cutout.crop(box)


def cartoonize_cutout(cutout: Image.Image) -> Image.Image:
    rgb = cutout.convert("RGB")
    rgb = ImageOps.autocontrast(rgb, cutoff=1)
    rgb = ImageEnhance.Color(rgb).enhance(0.95)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.98)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.06)
    softened = rgb.filter(ImageFilter.SMOOTH_MORE)
    poster = ImageOps.posterize(softened, 5).filter(ImageFilter.ModeFilter(size=3))
    rgb = Image.blend(rgb, poster, 0.26)
    warm_tint = Image.new("RGB", rgb.size, (186, 160, 132))
    rgb = Image.blend(rgb, warm_tint, 0.05)
    rgba = rgb.convert("RGBA")
    alpha = cutout.getchannel("A")
    alpha = alpha.filter(ImageFilter.GaussianBlur(1.2))
    rgba.putalpha(alpha)
    return rgba


def compose_subject(
    base_bg: Image.Image,
    source_path: Path,
    target_boxes: list[tuple[int, int]],
    offsets: list[tuple[int, int]],
    variant_index: int,
) -> Image.Image:
    canvas = base_bg.copy().convert("RGBA")

    portrait = Image.open(source_path).convert("RGB")
    portrait = ImageOps.exif_transpose(portrait)
    style_mode = variant_index % len(target_boxes)
    cutout = rembg_cutout(portrait)
    cutout = crop_to_subject(cutout)
    portrait_rgba = cartoonize_cutout(cutout)

    box_width, box_height = target_boxes[style_mode]
    scale = min(box_width / portrait_rgba.width, box_height / portrait_rgba.height)
    portrait_rgba = portrait_rgba.resize(
        (max(1, int(portrait_rgba.width * scale)), max(1, int(portrait_rgba.height * scale))),
        Image.Resampling.LANCZOS,
    )

    # Slight warm veil keeps the cutout inside the mural palette.
    warm = Image.new("RGBA", portrait_rgba.size, (186, 150, 117, 14))
    portrait_rgba = Image.alpha_composite(portrait_rgba, warm)

    x_offset, y_offset = offsets[style_mode]
    x = x_offset
    y = canvas.height - portrait_rgba.height + y_offset
    canvas.alpha_composite(portrait_rgba, (x, y))
    return canvas.convert("RGB")


def render_gamelist_variant(base_bg: Image.Image, source: Path, output_path: Path, variant_index: int) -> None:
    image = compose_subject(
        base_bg,
        source,
        target_boxes=[(430, 355), (390, 330), (520, 390), (455, 360), (480, 350)],
        offsets=[(-42, 60), (10, 42), (-76, 72), (-18, 56), (18, 48)],
        variant_index=variant_index,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def render_system_background(base_bg: Image.Image, source: Path, output_path: Path) -> None:
    base = base_bg.copy().convert("RGB")
    base = ImageEnhance.Brightness(base).enhance(1.04)
    base = ImageEnhance.Contrast(base).enhance(1.04)
    image = compose_subject(
        base,
        source,
        target_boxes=[(760, 700), (760, 700), (760, 700), (760, 700), (760, 700)],
        offsets=[(-56, 28), (-56, 28), (-56, 28), (-56, 28), (-56, 28)],
        variant_index=0,
    )
    image.save(output_path, quality=95)


def write_preview(paths: list[Path]) -> None:
    thumbs = []
    for path in paths[:15]:
        image = Image.open(path).convert("RGB")
        image.thumbnail((460, 259))
        card = Image.new("RGB", (480, 300), "white")
        card.paste(image, ((480 - image.width) // 2, 10))
        draw = ImageDraw.Draw(card)
        draw.text((12, 270), path.name, fill="black")
        thumbs.append(card)

    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 480, rows * 300), (236, 236, 236))
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % cols) * 480, (index // cols) * 300))
    sheet.save(PREVIEW_OUT, quality=92)


def rebuild_assignment() -> None:
    subprocess.run(
        [
            "python3",
            str(REPO_ROOT / "scripts" / "build_dawnkaya_variants.py"),
            "--systems-file",
            str(SYSTEMS_FILE),
        ],
        check=True,
    )


def main() -> None:
    base_bg = Image.open(BASE_GAMELIST_BG).convert("RGBA")
    photos = source_photos()
    VARIANT_DIR.mkdir(parents=True, exist_ok=True)

    start_index = 30
    written: list[Path] = []
    for index, source in enumerate(photos, start=start_index):
        output_path = VARIANT_DIR / f"kaya-ai-pose-{index:02d}.png"
        render_gamelist_variant(base_bg, source, output_path, index)
        written.append(output_path)

    render_system_background(base_bg, SYSTEM_BG_SOURCE, SYSTEM_BG_OUT)
    write_preview(written)
    rebuild_assignment()
    print(f"Wrote {len(written)} new dawnkaya set3 murals")
    print(f"Updated system mural: {SYSTEM_BG_OUT}")


if __name__ == "__main__":
    main()
