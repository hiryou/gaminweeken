#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


REPO_ROOT = Path(__file__).resolve().parents[1]
THEME_DIR = REPO_ROOT / "artifacts" / "themes" / "dawnkaya"
KAYA_SRC_DIR = Path.home() / "Downloads" / "kaya-set2"
BASE_GAMELIST_BG = THEME_DIR / "assets" / "kaya" / "gamelist-bg-kaya-wave-mural.png"
VARIANT_DIR = THEME_DIR / "assets" / "kaya" / "gamelist-ai-variants"
METADATA_DIR = THEME_DIR / "system" / "metadata"
METADATA_CUSTOM_DIR = THEME_DIR / "system" / "metadata-custom"

PREFERRED_FILES = [
    "PXL_20250531_201218082.jpg",
    "PXL_20250817_030803564.jpg",
    "PXL_20250913_092836900.jpg",
    "PXL_20251023_084918253.MP.jpg",
    "PXL_20251026_071859239.jpg",
    "PXL_20251026_071932676.jpg",
    "PXL_20251101_201338954~2.jpg",
    "PXL_20251216_205559556~2.jpg",
    "PXL_20260103_121342275.jpg",
    "PXL_20260221_004543049.jpg",
    "PXL_20260308_063332993.jpg",
    "PXL_20260413_092322391.jpg",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--systems-file",
        type=Path,
        required=True,
        help="Text file with one active system name per line.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260612,
        help="Seed for deterministic system-to-photo assignment.",
    )
    return parser.parse_args()


def active_systems(path: Path) -> list[str]:
    systems = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    return sorted(dict.fromkeys(systems))


def source_photos() -> list[Path]:
    photos = []
    preferred = [KAYA_SRC_DIR / name for name in PREFERRED_FILES if (KAYA_SRC_DIR / name).exists()]
    photos.extend(preferred)
    for path in sorted(KAYA_SRC_DIR.iterdir()):
        if not path.is_file():
            continue
        lower = path.name.lower()
        if "collage" in lower or "screenshot" in lower:
            continue
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        if path in photos:
            continue
        photos.append(path)
    if not photos:
        raise SystemExit(f"No source Kaya photos found under {KAYA_SRC_DIR}")
    return photos


def cartoonize_portrait(portrait: Image.Image) -> Image.Image:
    base = ImageOps.autocontrast(portrait, cutoff=1)
    base = ImageEnhancer.color(base, 0.78)
    base = ImageEnhancer.brightness(base, 0.94)
    base = ImageEnhancer.contrast(base, 1.12)
    base = base.filter(ImageFilter.SMOOTH_MORE)
    small = base.resize((base.width // 2, base.height // 2), Image.Resampling.BILINEAR)
    painter = small.resize(base.size, Image.Resampling.BILINEAR)
    painter = ImageOps.posterize(painter, 4)
    painter = painter.filter(ImageFilter.ModeFilter(size=5))
    painter = painter.filter(ImageFilter.SMOOTH_MORE)

    edges = base.convert("L").filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.invert(edges)
    edges = ImageEnhancer.contrast(edges, 1.6)
    edges = edges.filter(ImageFilter.GaussianBlur(0.9))

    blended = Image.blend(painter, base, 0.26)
    warm_tint = Image.new("RGB", blended.size, (211, 191, 160))
    blended = Image.blend(blended, warm_tint, 0.14)

    edge_rgb = Image.merge("RGB", (edges, edges, edges))
    final = Image.blend(blended, edge_rgb, 0.14)
    return final


def largest_component(mask: np.ndarray) -> np.ndarray:
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    best_component: list[tuple[int, int]] = []
    neighbors = ((1, 0), (-1, 0), (0, 1), (0, -1))

    for y in range(height):
        for x in range(width):
            if not mask[y, x] or visited[y, x]:
                continue
            stack = [(y, x)]
            visited[y, x] = True
            component: list[tuple[int, int]] = []
            while stack:
                cy, cx = stack.pop()
                component.append((cy, cx))
                for dy, dx in neighbors:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((ny, nx))
            if len(component) > len(best_component):
                best_component = component

    output = np.zeros_like(mask, dtype=np.uint8)
    for y, x in best_component:
        output[y, x] = 255
    return output


def subject_alpha(source: Image.Image) -> Image.Image:
    arr = np.asarray(source.convert("RGB")).astype(np.float32)
    lum = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    sat = arr.max(axis=2) - arr.min(axis=2)

    dark_primary = lum < 108
    dark_soft = (lum < 145) & (sat < 72)
    mask = dark_primary | dark_soft
    component = largest_component(mask)

    alpha = Image.fromarray(component, mode="L")
    alpha = alpha.filter(ImageFilter.MaxFilter(13))
    alpha = alpha.filter(ImageFilter.MinFilter(5))
    alpha = alpha.filter(ImageFilter.GaussianBlur(4))
    alpha = ImageEnhancer.brightness(alpha, 1.08)
    return alpha


def crop_to_subject(portrait: Image.Image, alpha: Image.Image) -> tuple[Image.Image, Image.Image]:
    bbox = alpha.point(lambda value: 255 if value > 24 else 0).getbbox()
    if bbox is None:
        return portrait, alpha
    left, top, right, bottom = bbox
    pad = 28
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(alpha.width, right + pad)
    bottom = min(alpha.height, bottom + pad)
    box = (left, top, right, bottom)
    return portrait.crop(box), alpha.crop(box)


def render_variant(base_bg: Image.Image, photo_path: Path, output_path: Path, variant_index: int) -> None:
    canvas = base_bg.copy().convert("RGBA")

    portrait = Image.open(photo_path).convert("RGB")
    portrait = ImageOps.exif_transpose(portrait)
    style_mode = variant_index % 4
    portrait_size = 760
    portrait = ImageOps.fit(
        portrait,
        (portrait_size, portrait_size),
        method=Image.Resampling.LANCZOS,
        centering=[(0.5, 0.44), (0.5, 0.40), (0.48, 0.46), (0.52, 0.42)][style_mode],
    )

    alpha = subject_alpha(portrait)
    portrait = cartoonize_portrait(portrait)
    portrait, alpha = crop_to_subject(portrait, alpha)

    target_boxes = [(455, 355), (390, 335), (505, 365), (420, 345)]
    box_width, box_height = target_boxes[style_mode]
    scale = min(box_width / portrait.width, box_height / portrait.height)
    portrait = portrait.resize(
        (max(1, int(portrait.width * scale)), max(1, int(portrait.height * scale))),
        Image.Resampling.LANCZOS,
    )
    alpha = alpha.resize(portrait.size, Image.Resampling.LANCZOS)

    portrait_rgba = Image.new("RGBA", portrait.size)
    portrait_rgba.paste(portrait, (0, 0))
    portrait_rgba.putalpha(alpha)

    # Tuck Kaya slightly off-canvas so she feels embedded in the mural.
    x = [-34, 6, -62, -14][style_mode]
    y = canvas.height - portrait.height + [58, 36, 72, 48][style_mode]
    canvas.alpha_composite(portrait_rgba, (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path)


def system_release_year(system_name: str) -> int:
    metadata_path = METADATA_DIR / f"{system_name}.xml"
    if not metadata_path.exists():
        return 9999
    try:
        root = ET.fromstring(metadata_path.read_text())
    except ET.ParseError:
        return 9999

    for element in root.findall("./variables/systemReleaseYear"):
        text = (element.text or "").strip()
        if text.isdigit():
            return int(text)
    return 9999


def randomized_assignment(
    systems: list[str],
    variant_paths: list[Path],
    rng: random.Random,
) -> list[tuple[str, Path]]:
    if not variant_paths:
        raise ValueError("variant_paths must not be empty")

    ordered_systems = sorted(systems, key=lambda name: (system_release_year(name), name))
    repeats = math.ceil(len(ordered_systems) / len(variant_paths))
    pool: list[Path] = []
    previous: Path | None = None

    for _ in range(repeats):
        chunk = variant_paths[:]
        rng.shuffle(chunk)
        if previous is not None and len(chunk) > 1 and chunk[0] == previous:
            for index in range(1, len(chunk)):
                if chunk[index] != previous:
                    chunk[0], chunk[index] = chunk[index], chunk[0]
                    break
        pool.extend(chunk)
        previous = chunk[-1]

    return list(zip(ordered_systems, pool[: len(ordered_systems)]))


class ImageEnhancer:
    @staticmethod
    def color(image: Image.Image, factor: float) -> Image.Image:
        return ImageEnhance.Color(image).enhance(factor)

    @staticmethod
    def brightness(image: Image.Image, factor: float) -> Image.Image:
        return ImageEnhance.Brightness(image).enhance(factor)

    @staticmethod
    def contrast(image: Image.Image, factor: float) -> Image.Image:
        return ImageEnhance.Contrast(image).enhance(factor)

    @staticmethod
    def sharpness(image: Image.Image, factor: float) -> Image.Image:
        return ImageEnhance.Sharpness(image).enhance(factor)


from PIL import ImageEnhance


def update_metadata_override(system_name: str, relative_variant_path: str) -> None:
    path = METADATA_CUSTOM_DIR / f"{system_name}.xml"
    snippet = (
        "   <variables>\n"
        f"      <kayaGamelistBackground>{relative_variant_path}</kayaGamelistBackground>\n"
        "   </variables>\n"
    )

    if path.exists():
        content = path.read_text()
        if "<kayaGamelistBackground>" in content:
            content = re.sub(
                r"<kayaGamelistBackground>.*?</kayaGamelistBackground>",
                f"<kayaGamelistBackground>{relative_variant_path}</kayaGamelistBackground>",
                content,
                flags=re.DOTALL,
            )
        else:
            content = content.replace("</theme>", snippet + "</theme>")
    else:
        content = "<theme>\n" + snippet + "</theme>\n"

    path.write_text(content)


def write_preview(variant_paths: list[Path]) -> None:
    previews = variant_paths[:12]
    thumbs = []
    for path in previews:
        image = Image.open(path).convert("RGB")
        image.thumbnail((500, 281))
        card = Image.new("RGB", (520, 330), "white")
        card.paste(image, ((520 - image.width) // 2, 12))
        draw = ImageDraw.Draw(card)
        draw.text((12, 296), path.name, fill="black")
        thumbs.append(card)

    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 520, rows * 330), (235, 235, 235))
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % cols) * 520, (index // cols) * 330))

    sheet.save(THEME_DIR / "preview-gamelist-variants.jpg", quality=90)


def existing_variants() -> list[Path]:
    return sorted(VARIANT_DIR.glob("kaya-ai-pose-*.png"))


def main() -> None:
    args = parse_args()
    systems = active_systems(args.systems_file)
    rng = random.Random(args.seed)
    VARIANT_DIR.mkdir(parents=True, exist_ok=True)
    variant_paths = existing_variants()

    if not variant_paths:
        photos = source_photos()
        base_bg = Image.open(BASE_GAMELIST_BG).convert("RGBA")
        for index, photo in enumerate(photos, start=1):
            variant_path = VARIANT_DIR / f"kaya-ai-pose-{index:02d}.png"
            render_variant(base_bg, photo, variant_path, index)
            variant_paths.append(variant_path)

    # Assign backgrounds across release-year-sorted systems with per-cycle reshuffling.
    for system_name, variant in randomized_assignment(systems, variant_paths, rng):
        relative_path = f"./assets/kaya/gamelist-ai-variants/{variant.name}"
        update_metadata_override(system_name, relative_path)

    write_preview(variant_paths)
    print(f"Generated {len(variant_paths)} gamelist variants")
    print(f"Assigned them across {len(systems)} active systems")


if __name__ == "__main__":
    main()
