"""
Install a small curated RetroArch core set onto the connected Android device.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from droid_config import load_droid_config


RETROARCH_PACKAGE = "com.retroarch.aarch64"
CONFIG = load_droid_config()
RETROARCH_ROOT = str(CONFIG.retroarch_dir)
RETROARCH_CORES_DIR = str(CONFIG.retroarch_cores_dir)
RETROARCH_INFO_DIR = str(CONFIG.retroarch_info_dir)
RETROARCH_ANDROID_CORE_BASE = "https://buildbot.libretro.com/nightly/android/latest/arm64-v8a"
RETROARCH_INFO_ZIP_URL = "https://buildbot.libretro.com/assets/frontend/info.zip"


@dataclass(frozen=True)
class CoreSpec:
    key: str
    display_name: str
    esde_system: str
    esde_mapping: str
    archive_name: str
    library_name: str
    info_name: str


CORE_REGISTRY = {
    "nes_fceumm": CoreSpec(
        key="nes_fceumm",
        display_name="Nintendo Entertainment System - FCEUmm",
        esde_system="nes",
        esde_mapping="RetroArch::FCEUmm",
        archive_name="fceumm_libretro_android.so.zip",
        library_name="fceumm_libretro_android.so",
        info_name="fceumm_libretro.info",
    ),
    "snes_snes9x": CoreSpec(
        key="snes_snes9x",
        display_name="Super Nintendo Entertainment System - Snes9x",
        esde_system="snes",
        esde_mapping="RetroArch::Snes9x",
        archive_name="snes9x_libretro_android.so.zip",
        library_name="snes9x_libretro_android.so",
        info_name="snes9x_libretro.info",
    ),
    "genesis_genesis_plus_gx": CoreSpec(
        key="genesis_genesis_plus_gx",
        display_name="Sega Mega Drive / Genesis - Genesis Plus GX",
        esde_system="genesis",
        esde_mapping="RetroArch::Genesis Plus GX",
        archive_name="genesis_plus_gx_libretro_android.so.zip",
        library_name="genesis_plus_gx_libretro_android.so",
        info_name="genesis_plus_gx_libretro.info",
    ),
    "dreamcast_flycast": CoreSpec(
        key="dreamcast_flycast",
        display_name="Sega Dreamcast - Flycast",
        esde_system="dreamcast",
        esde_mapping="RetroArch::Flycast",
        archive_name="flycast_libretro_android.so.zip",
        library_name="flycast_libretro_android.so",
        info_name="flycast_libretro.info",
    ),
}

DEFAULT_CORE_KEYS = [
    "nes_fceumm",
    "snes_snes9x",
    "genesis_genesis_plus_gx",
    "dreamcast_flycast",
]


def run_command(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        details = stderr or stdout or f"command failed: {' '.join(cmd)}"
        raise RuntimeError(details)
    return result


def require_adb() -> None:
    run_command(["adb", "version"])


def list_adb_devices() -> list[str]:
    result = run_command(["adb", "devices"])
    devices: list[str] = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def resolve_serial(explicit_serial: str | None) -> str:
    if explicit_serial:
        return explicit_serial

    devices = list_adb_devices()
    if len(devices) == 1:
        return devices[0]
    if not devices:
        raise RuntimeError("No adb devices are connected")
    raise RuntimeError("Multiple adb devices detected; pass --serial explicitly")


def ensure_retroarch_installed(serial: str) -> None:
    result = run_command(
        ["adb", "-s", serial, "shell", "pm", "list", "packages", RETROARCH_PACKAGE]
    )
    if RETROARCH_PACKAGE not in result.stdout:
        raise RuntimeError(
            f"RetroArch package `{RETROARCH_PACKAGE}` is not installed on device {serial}"
        )


def remote_file_exists(serial: str, remote_path: str) -> bool:
    result = run_command(
        ["adb", "-s", serial, "shell", "test", "-f", remote_path],
        check=False,
    )
    return result.returncode == 0


def ensure_remote_directories(serial: str) -> None:
    run_command(
        [
            "adb",
            "-s",
            serial,
            "shell",
            "mkdir",
            "-p",
            RETROARCH_ROOT,
            RETROARCH_CORES_DIR,
            RETROARCH_INFO_DIR,
        ]
    )


def download_file(url: str, dest_path: Path) -> None:
    with urllib.request.urlopen(url) as response, dest_path.open("wb") as output_file:
        shutil.copyfileobj(response, output_file)


def extract_zip_member(zip_path: Path, member_name: str, dest_path: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(member_name) as source, dest_path.open("wb") as output_file:
            shutil.copyfileobj(source, output_file)


def push_file(serial: str, local_path: Path, remote_path: str) -> None:
    run_command(["adb", "-s", serial, "push", str(local_path), remote_path])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install a curated RetroArch core set onto the connected Droid device."
    )
    parser.add_argument(
        "--serial",
        help="adb device serial. If omitted, the only connected device will be used.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=sorted(CORE_REGISTRY),
        default=DEFAULT_CORE_KEYS,
        help="Limit installation to one or more curated RetroArch cores.",
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Resolve and print planned core installs without pushing files to the device.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_adb()
    serial = resolve_serial(args.serial)
    ensure_retroarch_installed(serial)

    print("=========================================================")
    print("   RETRODROID HOST ORCHESTRATOR: RETROARCH CORE SETUP    ")
    print("=========================================================\n")
    print(f"[*] adb serial: {serial}")
    print(f"[*] RetroArch root: {RETROARCH_ROOT}")
    if args.dryrun:
        print("[*] Dry run mode enabled. No files will be pushed.\n")
    else:
        print()

    selected_specs = [CORE_REGISTRY[key] for key in args.only]

    installed: list[str] = []
    skipped: list[str] = []
    failed: list[tuple[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="retrodroid-retroarch-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        info_zip_path = temp_dir / "info.zip"
        info_zip_ready = False

        if not args.dryrun:
            ensure_remote_directories(serial)

        for spec in selected_specs:
            remote_core_path = f"{RETROARCH_CORES_DIR}/{spec.library_name}"
            remote_info_path = f"{RETROARCH_INFO_DIR}/{spec.info_name}"
            core_exists = remote_file_exists(serial, remote_core_path)
            info_exists = remote_file_exists(serial, remote_info_path)

            core_url = f"{RETROARCH_ANDROID_CORE_BASE}/{spec.archive_name}"
            print(f"[*] Processing {spec.display_name}...")
            print(f"    Source core archive: {core_url}")
            print(f"    ES-DE system mapping: {spec.esde_system} -> {spec.esde_mapping}")

            if args.dryrun:
                installed.append(spec.display_name)
                continue

            try:
                if core_exists and info_exists:
                    skipped.append(spec.display_name)
                    print(
                        f"    [!] Core files already present, skipping file copy."
                    )
                else:
                    core_zip_path = temp_dir / spec.archive_name
                    core_library_path = temp_dir / spec.library_name
                    core_info_path = temp_dir / spec.info_name

                    download_file(core_url, core_zip_path)
                    extract_zip_member(core_zip_path, spec.library_name, core_library_path)

                    if not info_zip_ready:
                        download_file(RETROARCH_INFO_ZIP_URL, info_zip_path)
                        info_zip_ready = True
                    extract_zip_member(info_zip_path, spec.info_name, core_info_path)

                    push_file(serial, core_library_path, remote_core_path)
                    push_file(serial, core_info_path, remote_info_path)
                    print(f"    [+] Installed core: {remote_core_path}")
                    print(f"    [+] Installed info: {remote_info_path}")
                installed.append(spec.display_name)
            except Exception as exc:
                failed.append((spec.display_name, str(exc)))
                print(f"    [-] Failed: {exc}")

    print("\n============================= SUMMARY =============================")
    print(f"[+] RetroArch core targets processed: {len(selected_specs)}")
    print(f"[+] RetroArch core installs completed: {len(installed)}")
    for item in installed:
        print(f"    - {item}")

    if skipped:
        print(f"\n[!] RetroArch core installs skipped: {len(skipped)}")
        for item in skipped:
            print(f"    - {item}")

    if failed:
        print(f"\n[-] RetroArch core installs failed: {len(failed)}")
        for name, reason in failed:
            print(f"    - {name}: {reason}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
