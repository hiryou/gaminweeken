"""
Download Android emulator APKs into the host-side artifact cache.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import requests


DEFAULT_DOWNLOAD_DIR = Path(
    os.environ.get(
        "RETRODROID_DOWNLOAD_DIR",
        Path(__file__).resolve().parents[1] / "artifacts" / "apks",
    )
)
HTTP_HEADERS = {
    "Accept": "application/vnd.github+json, text/html, application/xhtml+xml, */*",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    ),
}


@dataclass(frozen=True)
class DownloadSpec:
    url: str
    filename: str
    archive_member: str | None = None


EMULATOR_REGISTRY = {
    "retroarch": {
        "name": "RetroArch 64-bit Core",
        "source_type": "resolver",
        "resolver": "resolve_retroarch",
        "emulator": "retroarch",
        "manifest_name": "retroarch.json",
    },
    "ps2_aethersx2": {
        "name": "AetherSX2 v1.5-3668",
        "source_type": "resolver",
        "resolver": "resolve_aethersx2",
        "emulator": "aethersx2_family",
        "manifest_name": "aethersx2.json",
    },
    "3ds_azahar_plus": {
        "name": "Azahar Plus (Premium 3DS Engine - Citra Successor)",
        "source_type": "resolver",
        "resolver": "resolve_azahar_plus",
        "emulator": "azaharplus",
        "manifest_name": "azaharplus.json",
    },
    "switch_sudachi": {
        "name": "Sudachi Switch Emulator (Pinned Stable URL)",
        "source_type": "resolver",
        "resolver": "resolve_sudachi",
        "emulator": "sudachi",
        "manifest_name": "sudachi.json",
    },
    "switch_citron_neo": {
        "name": "Citron Neo Switch Emulator (Vulkan & Thread Speed Performance Engine)",
        "source_type": "resolver",
        "resolver": "resolve_citron",
        "emulator": "citron",
        "manifest_name": "citron.json",
    },
    "gamecube_dolphin": {
        "name": "Dolphin GameCube/Wii Stable Release",
        "source_type": "resolver",
        "resolver": "resolve_dolphin",
        "emulator": "dolphin",
        "manifest_name": "dolphin.json",
    },
    "n64_mupen64plus_ae": {
        "name": "Mupen64Plus AE (official nightly bundle)",
        "source_type": "resolver",
        "resolver": "resolve_mupen64plus_ae",
        "emulator": "mupen64plusae",
        "manifest_name": "mupen64plusae.json",
    },
}


SESSION = requests.Session()
SESSION.headers.update(HTTP_HEADERS)


def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def get_json(url: str) -> dict | list:
    response = SESSION.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def get_text(url: str) -> str:
    response = SESSION.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def resolve_github_release_asset(
    repo_path: str,
    asset_patterns: Iterable[str],
    *,
    include_prereleases: bool = False,
) -> DownloadSpec:
    releases = get_json(f"https://api.github.com/repos/{repo_path}/releases")

    for release in releases:
        if release.get("draft"):
            continue
        if release.get("prerelease") and not include_prereleases:
            continue

        assets = release.get("assets", [])
        for pattern in asset_patterns:
            regex = re.compile(pattern)
            for asset in assets:
                asset_name = asset.get("name", "")
                if regex.search(asset_name):
                    return DownloadSpec(
                        url=asset["browser_download_url"],
                        filename=asset_name,
                    )

    raise RuntimeError(f"No matching asset found for github.com/{repo_path}")


def resolve_retroarch() -> DownloadSpec:
    stable_index = get_text("https://buildbot.libretro.com/stable/")
    versions = sorted(
        {
            match.group(1)
            for match in re.finditer(r"/stable/([0-9]+(?:\.[0-9]+)+)/", stable_index)
        },
        key=version_key,
    )
    if not versions:
        raise RuntimeError("Unable to resolve a RetroArch stable version from buildbot")

    latest_version = versions[-1]
    android_index = get_text(f"https://buildbot.libretro.com/stable/{latest_version}/android/")
    match = re.search(r'href="([^"]*RetroArch_aarch64\.apk)"', android_index)
    if not match:
        raise RuntimeError(f"No RetroArch_aarch64.apk found for stable {latest_version}")

    apk_path = match.group(1)
    if apk_path.startswith("/"):
        url = f"https://buildbot.libretro.com{apk_path}"
    else:
        url = f"https://buildbot.libretro.com/stable/{latest_version}/android/{apk_path}"

    return DownloadSpec(url=url, filename=os.path.basename(url))


def resolve_azahar_plus() -> DownloadSpec:
    return resolve_github_release_asset(
        "AzaharPlus/AzaharPlus",
        [
            r"android_coexists_with_azahar\.apk$",
            r"android_replaces_azahar\.apk$",
            r"\.apk$",
        ],
    )


# Docs ref for pinned fallback build source:
# https://www.reddit.com/r/EmulationOnAndroid/comments/1977t8g/aethersx2_or_nethersx2/
# https://github.com/AetherSX2-backup/AetherSX2-builds/tree/master/alpha-3191-3668
def resolve_aethersx2() -> DownloadSpec:
    return DownloadSpec(
        url=(
            "https://raw.githubusercontent.com/AetherSX2-backup/AetherSX2-builds/master/"
            "alpha-3191-3668/13930-v1.5-3668.apk"
        ),
        filename="AetherSX2-v1.5-3668.apk",
    )


def resolve_citron() -> DownloadSpec:
    return resolve_github_release_asset(
        "citron-neo/emulator",
        [
            r"app-mainline-release\.apk$",
            r"Android.*\.apk$",
            r"\.apk$",
        ],
        include_prereleases=True,
    )


# Docs ref for pinned stable Android build:
# https://sudachiemu.org/download
def resolve_sudachi() -> DownloadSpec:
    return DownloadSpec(
        url="https://download.sudachiemu.org/sudachiemu.org-apk.zip",
        filename="Sudachi-stable.apk",
        archive_member="sudachiemu.org-apk.apk",
    )


# Docs ref for pinned stable Android release:
# https://dolphin-emu.org/download/
def resolve_dolphin() -> DownloadSpec:
    return DownloadSpec(
        url="https://dl.dolphin-emu.org/releases/2603a/dolphin-2603a.apk",
        filename="Dolphin-2603a.apk",
    )


def resolve_mupen64plus_ae() -> DownloadSpec:
    return DownloadSpec(
        url=(
            "https://github.com/mupen64plus-ae/mupen64plus-ae/releases/download/"
            "Pre-release/mupen64plus-ae-master.zip"
        ),
        filename="Mupen64PlusAE-release.apk",
        archive_member="Mupen64PlusAE-release.apk",
    )


def ensure_apk_file(path: Path) -> None:
    with path.open("rb") as apk_file:
        header = apk_file.read(4)
    if header != b"PK\x03\x04":
        raise RuntimeError(f"{path.name} is not a valid APK/ZIP payload")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as apk_file:
        for chunk in iter(lambda: apk_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(download_dir: Path, config: dict, spec: DownloadSpec) -> None:
    payload_path = download_dir / spec.filename
    manifest_path = download_dir / config["manifest_name"]
    manifest = {
        "emulator": config["emulator"],
        "filename": spec.filename,
        "source_url": spec.url,
        "sha256": sha256_file(payload_path),
        "size": payload_path.stat().st_size,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"[+] Manifest Updated: {manifest_path}")


def download_file(url: str, dest_path: Path) -> None:
    with SESSION.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type.lower():
            raise RuntimeError(f"Expected a binary payload but received {content_type}")
        with dest_path.open("wb") as output_file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output_file.write(chunk)


def download_binary(spec: DownloadSpec, download_dir: Path) -> None:
    dest_path = download_dir / spec.filename
    print(f"[*] Stream Initialization: {spec.filename}...")

    if spec.archive_member is None:
        download_file(spec.url, dest_path)
        ensure_apk_file(dest_path)
        print(f"[+] Operational Success: Saved to {dest_path}")
        return

    fd, temp_path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    temp_zip_path = Path(temp_path)
    try:
        download_file(spec.url, temp_zip_path)
        with zipfile.ZipFile(temp_zip_path) as archive:
            member_name = next(
                (name for name in archive.namelist() if name.endswith(spec.archive_member)),
                None,
            )
            if member_name is None:
                raise RuntimeError(f"{spec.archive_member} was not present in the downloaded archive")
            with archive.open(member_name) as source, dest_path.open("wb") as output_file:
                output_file.write(source.read())
        ensure_apk_file(dest_path)
        print(f"[+] Operational Success: Saved to {dest_path}")
    finally:
        if temp_zip_path.exists():
            temp_zip_path.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download emulator APKs into the local artifact cache.")
    parser.add_argument(
        "--download-dir",
        default=str(DEFAULT_DOWNLOAD_DIR),
        help=f"Destination directory for downloaded APKs (default: {DEFAULT_DOWNLOAD_DIR})",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=sorted(EMULATOR_REGISTRY),
        help="Limit execution to one or more emulator registry keys.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve each source and print what would be downloaded without writing files.",
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Alias for --dry-run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    download_dir = Path(args.download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[str] = []
    manual_warnings: list[tuple[str, str]] = []
    failures: list[tuple[str, str]] = []

    print("=========================================================")
    print("      RETRODROID HOST CACHE: APK DOWNLOAD PIPELINE       ")
    print("=========================================================\n")

    selected_ids = args.only or list(EMULATOR_REGISTRY.keys())

    for emu_id in selected_ids:
        config = EMULATOR_REGISTRY[emu_id]
        print(f"[#] Processing Entry: {config['name']}")

        if config["source_type"] == "manual":
            reason = config["reason"]
            manual_warnings.append((config["name"], reason))
            print(f"[!] Manual Step Required: {reason}")
            print("-" * 50)
            continue

        resolver = globals()[config["resolver"]]
        try:
            spec = resolver()
            if args.dry_run or args.dryrun:
                print(f"[+] Resolved Download: {spec.filename}")
                print(f"    Source URL: {spec.url}")
                if spec.archive_member:
                    print(f"    Archive Member: {spec.archive_member}")
            else:
                download_binary(spec, download_dir)
                write_manifest(download_dir, config, spec)
                downloaded.append(spec.filename)
        except Exception as exc:
            failures.append((config["name"], str(exc)))
            print(f"[-] Download Execution Aborted for {emu_id}: {exc}")

        print("-" * 50)

    print("\n============================= SUMMARY =============================")
    print(f"[+] Downloaded APKs: {len(downloaded)}")
    for filename in downloaded:
        print(f"    - {filename}")

    if manual_warnings:
        print("\n[!] NOTICEABLE WARNINGS")
        print("    The following emulators were skipped because their sources are not")
        print("    currently machine-downloadable by this script:")
        for name, reason in manual_warnings:
            print(f"    - {name}: {reason}")

    if failures:
        print("\n[-] DOWNLOAD FAILURES")
        for name, reason in failures:
            print(f"    - {name}: {reason}")


if __name__ == "__main__":
    main()
