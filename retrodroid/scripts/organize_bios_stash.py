#!/usr/bin/env python3

"""
Recursively sort a host BIOS/firmware stash into per-system folders using
Batocera BIOS hash definitions. Unmatched files are moved into `_review/`
and a JSON report is written under `tmp/`.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import tempfile
import urllib.request
from collections import defaultdict
from importlib.machinery import SourceFileLoader
from pathlib import Path


BATOCERA_RAW_URL = (
    "https://raw.githubusercontent.com/batocera-linux/batocera.linux/refs/heads/master/"
    "package/batocera/core/batocera-scripts/scripts/batocera-systems"
)


PLATFORM_ALIAS = {
    "psx": "ps1",
    "dreamcast": "dreamcast",
    "3do": "3do",
    "saturn": "saturn",
    "nds": "nds",
    "gba": "gba",
    "pcengine": "pcengine",
    "supergrafx": "pcengine",
    "neogeo": "neogeo",
}


FILENAME_PRIORITY = {
    "psxonpsp660.bin": "ps1",
    "scph101.bin": "ps1",
    "scph1001.bin": "ps1",
    "scph5500.bin": "ps1",
    "scph5501.bin": "ps1",
    "scph5502.bin": "ps1",
    "scph7001.bin": "ps1",
    "dc_boot.bin": "dreamcast",
    "dc_flash.bin": "dreamcast",
    "panafz1.bin": "3do",
    "panafz10.bin": "3do",
    "goldstar.bin": "3do",
    "saturn_bios.bin": "saturn",
    "bios7.bin": "nds",
    "bios9.bin": "nds",
    "dsi_bios7.bin": "nds",
    "dsi_bios9.bin": "nds",
    "firmware.bin": "nds",
    "dsi_firmware.bin": "nds",
    "dsi_nand.bin": "nds",
    "gba_bios.bin": "gba",
    "gb_bios.bin": "gba",
    "gbc_bios.bin": "gba",
    "sgb_bios.bin": "gba",
    "syscard3.pce": "pcengine",
    "neogeo.zip": "neogeo",
}


def md5sum(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_batocera_systems() -> dict:
    with tempfile.NamedTemporaryFile(prefix="batocera-systems-", delete=False) as fh:
        tmp_path = Path(fh.name)
    urllib.request.urlretrieve(BATOCERA_RAW_URL, tmp_path)
    loader = SourceFileLoader("batocera_systems", str(tmp_path))
    spec = importlib.util.spec_from_loader("batocera_systems", loader)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    tmp_path.unlink(missing_ok=True)
    return module.systems


def build_md5_index(systems: dict) -> dict[str, list[tuple[str, str]]]:
    index: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for platform, meta in systems.items():
        for entry in meta.get("biosFiles", []):
            md5 = (entry.get("md5") or "").strip().lower()
            file_path = entry.get("file", "")
            if not md5:
                continue
            index[md5].append((platform, file_path))
    return index


def platform_from_match(path: Path, md5: str, md5_index: dict[str, list[tuple[str, str]]]) -> str | None:
    name = path.name

    if name == ".DS_Store":
        return None

    if "switch" in path.parts:
        return "switch"
    if "GC" in path.parts or name == "IPL.bin" or name.startswith("gc-"):
        return "gamecube"

    if name in FILENAME_PRIORITY:
        return FILENAME_PRIORITY[name]

    matches = md5_index.get(md5, [])
    if not matches:
        return None

    if len(matches) == 1:
        return PLATFORM_ALIAS.get(matches[0][0], matches[0][0])

    for _, file_path in matches:
        candidate = Path(file_path).name
        if candidate == name:
            for platform, path_match in matches:
                if Path(path_match).name == name:
                    return PLATFORM_ALIAS.get(platform, platform)

    for preferred in ("psx", "dreamcast", "saturn", "nds", "gba", "pcengine", "neogeo", "3do"):
        for platform, _ in matches:
            if platform == preferred:
                return PLATFORM_ALIAS.get(platform, platform)

    return PLATFORM_ALIAS.get(matches[0][0], matches[0][0])


def relative_review_path(root: Path, path: Path) -> Path:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = Path(path.name)
    return Path("_review") / rel


def destination_for(path: Path, platform: str, root: Path) -> Path:
    if platform == "switch":
        try:
            rel = path.relative_to(root / "switch")
            return root / "switch" / rel
        except ValueError:
            return root / "switch" / path.name

    if platform == "gamecube":
        if path.name == "IPL.bin":
            region = path.parent.name
            if region in {"USA", "EUR", "JAP"}:
                return root / "gamecube" / region / "IPL.bin"
        return root / "gamecube" / path.name

    if platform == "dreamcast" and path.name.startswith("dc_"):
        return root / "dreamcast" / path.name

    return root / platform / path.name


def unique_destination(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    counter = 2
    while True:
        candidate = dest.with_name(f"{stem}__dup{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def move_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dest.resolve():
        return
    if dest.exists():
        if md5sum(src) == md5sum(dest):
            src.unlink()
            return
        dest = unique_destination(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recursively organize a BIOS stash by platform using Batocera hash definitions."
        )
    )
    parser.add_argument("root", type=Path, nargs="?", default=Path.home() / "Downloads/retrogaming/bios")
    parser.add_argument("--report", type=Path, default=Path("tmp/bios_organize_report.json"))
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    systems = load_batocera_systems()
    md5_index = build_md5_index(systems)

    files = [p for p in root.rglob("*") if p.is_file()]
    files.sort()

    report = {"moved": [], "review": [], "unchanged": []}

    for path in files:
        if path.name == ".DS_Store":
            dest = root / "_review" / path.name
            move_file(path, unique_destination(dest))
            report["review"].append({"source": str(path), "dest": str(dest), "reason": "macos-metadata"})
            continue

        if "_review" in path.parts:
            report["unchanged"].append({"source": str(path), "reason": "already-review"})
            continue

        digest = md5sum(path)
        platform = platform_from_match(path, digest, md5_index)
        if platform is None:
            dest = root / relative_review_path(root, path)
            move_file(path, unique_destination(dest))
            report["review"].append({"source": str(path), "dest": str(dest), "reason": "unmatched"})
            continue

        dest = destination_for(path, platform, root)
        move_file(path, dest)
        report["moved"].append({"source": str(path), "dest": str(dest), "platform": platform, "md5": digest})

    # Remove empty directories except root.
    for directory in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        if directory == root:
            continue
        try:
            directory.rmdir()
        except OSError:
            pass

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2))

    moved = len(report["moved"])
    review = len(report["review"])
    print(f"Moved {moved} files into platform folders.")
    print(f"Moved {review} files into _review.")
    print(f"Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
