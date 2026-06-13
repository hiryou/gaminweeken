"""
Validate expected RetroArch BIOS / firmware files on the connected Android device.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Literal

from droid_config import load_droid_config


CONFIG = load_droid_config()
RETROARCH_ROOT = str(CONFIG.retroarch_dir)
RETROARCH_SYSTEM_DIR = str(CONFIG.retroarch_system_dir)
ROMS_ROOT = str(CONFIG.roms_root)
BATOCERA_REMOTE_URL = (
    "https://raw.githubusercontent.com/batocera-linux/batocera.linux/master/"
    "package/batocera/core/batocera-scripts/scripts/batocera-systems"
)


@dataclass
class FirmwareSpec:
    path: str
    required: bool
    description: str
    alternates: tuple[str, ...] = ()
    expected_md5: tuple[str, ...] = ()


@dataclass(frozen=True)
class SystemRule:
    kind: Literal["check", "no_firmware_needed", "manual", "unknown"]
    description: str
    firmware_group: str | None = None


FIRMWARE_GROUPS = {
    "ps1_swanstation": {
        "display_name": "Sony PlayStation - SwanStation",
        "esde_system": "ps1",
        "esde_mapping": "RetroArch::SwanStation",
        "hash_source": (
            "Batocera batocera-systems PSX biosFiles MD5 list "
            "(package/batocera/core/batocera-scripts/scripts/batocera-systems)."
        ),
        "firmware": [
            FirmwareSpec("scph5501.bin", True, "PS1 US BIOS", expected_md5=("490f666e1afb15b7362b406ed1cea246",)),
            FirmwareSpec("scph5500.bin", False, "PS1 JP BIOS", expected_md5=("8dd7d5296a650fac7319bce665a6a53c",)),
            FirmwareSpec("scph5502.bin", False, "PS1 EU BIOS", expected_md5=("32736f17079d0b2b7024407c39bd3050",)),
            FirmwareSpec(
                "PSXONPSP660.bin",
                False,
                "Region-free PSP PS1 BIOS alternative",
                alternates=("psxonpsp660.bin",),
                expected_md5=("c53ca5908936d412331790f4426c6c33",),
            ),
            FirmwareSpec("scph101.bin", False, "PS1 NA BIOS alternative", expected_md5=("6e3735ff4c7dc899ee98981385f6f3d0",)),
            FirmwareSpec("scph1001.bin", False, "PS1 NA BIOS alternative", expected_md5=("dc2b9bf8da62ec93e868cfd29f0d067d",)),
            FirmwareSpec("scph7001.bin", False, "PS1 US BIOS alternative", expected_md5=("1e68c231d0896b7eadcad1d7d8e76129",)),
            FirmwareSpec("ps1_rom.bin", False, "Region-free PS3 PS1 BIOS alternative"),
            FirmwareSpec("openbios.bin", False, "Open-source BIOS alternative"),
        ],
        "notes": (
            "SwanStation generally needs a PS1 BIOS for broad compatibility. "
            "At minimum, add scph5501.bin for US-region titles. "
            "Known-good MD5s are checked against Batocera's PSX BIOS table where available."
        ),
    },
    "dreamcast_flycast": {
        "display_name": "Sega Dreamcast - Flycast",
        "esde_system": "dreamcast",
        "esde_mapping": "RetroArch::Flycast",
        "hash_source": (
            "Batocera batocera-systems Dreamcast biosFiles MD5 list for dc_boot.bin; "
            "dc_flash.bin remains presence-only because Batocera does not define an MD5 for it there."
        ),
        "firmware": [
            FirmwareSpec(
                "dc_boot.bin",
                True,
                "Dreamcast BIOS",
                expected_md5=("e10c53c2f8b90bab96ead2d368858623",),
            ),
            FirmwareSpec(
                "dc_flash.bin",
                True,
                "Dreamcast flash / clock / language data",
                alternates=("dc/dc_flash.bin",),
            ),
        ],
        "notes": "Flycast typically expects both dc_boot.bin and dc_flash.bin in the RetroArch system directory.",
    },
}


BATOCERA_SOURCE_LABEL = "built-in fallback MD5 set"


SYSTEM_RULES: dict[str, SystemRule] = {
    "dreamcast": SystemRule(
        kind="check",
        firmware_group="dreamcast_flycast",
        description="RetroArch::Flycast firmware can be validated automatically.",
    ),
    "ps1": SystemRule(
        kind="check",
        firmware_group="ps1_swanstation",
        description="RetroArch::SwanStation firmware can be validated automatically.",
    ),
    "psx": SystemRule(
        kind="check",
        firmware_group="ps1_swanstation",
        description="RetroArch::SwanStation firmware can be validated automatically.",
    ),
    "nes": SystemRule(kind="no_firmware_needed", description="RetroArch NES cores do not need a BIOS."),
    "famicom": SystemRule(kind="no_firmware_needed", description="RetroArch NES/Famicom cores do not need a BIOS."),
    "snes": SystemRule(kind="no_firmware_needed", description="RetroArch Snes9x does not need a BIOS."),
    "sfc": SystemRule(kind="no_firmware_needed", description="RetroArch Snes9x does not need a BIOS."),
    "genesis": SystemRule(kind="no_firmware_needed", description="RetroArch Genesis Plus GX does not need a BIOS."),
    "megadrive": SystemRule(kind="no_firmware_needed", description="RetroArch Genesis Plus GX does not need a BIOS."),
    "megadrivejp": SystemRule(kind="no_firmware_needed", description="RetroArch Genesis Plus GX does not need a BIOS."),
    "gamegear": SystemRule(kind="no_firmware_needed", description="RetroArch Genesis Plus GX does not need a BIOS."),
    "mastersystem": SystemRule(kind="no_firmware_needed", description="RetroArch Genesis Plus GX does not need a BIOS."),
    "mark3": SystemRule(kind="no_firmware_needed", description="RetroArch Genesis Plus GX does not need a BIOS."),
    "gb": SystemRule(kind="no_firmware_needed", description="Game Boy emulators do not normally need a BIOS."),
    "gbc": SystemRule(kind="no_firmware_needed", description="Game Boy Color emulators do not normally need a BIOS."),
    "gba": SystemRule(kind="no_firmware_needed", description="Game Boy Advance emulators do not normally need a BIOS."),
    "n64": SystemRule(kind="no_firmware_needed", description="Mupen64Plus AE does not normally need a BIOS."),
    "gc": SystemRule(kind="no_firmware_needed", description="Dolphin generally does not require a GameCube BIOS."),
    "wii": SystemRule(kind="no_firmware_needed", description="Dolphin generally does not require a Wii BIOS."),
    "3ds": SystemRule(
        kind="manual",
        description="Azahar/Citra system files are handled in-app and are not validated by this script.",
    ),
    "n3ds": SystemRule(
        kind="manual",
        description="Azahar/Citra system files are handled in-app and are not validated by this script.",
    ),
    "ps2": SystemRule(
        kind="manual",
        description="AetherSX2 BIOS is configured inside the app and is not validated by this script.",
    ),
    "switch": SystemRule(
        kind="manual",
        description="Citron/Sudachi prod.keys and firmware are configured inside each emulator app.",
    ),
}


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


def remote_file_exists(serial: str, remote_path: str) -> bool:
    result = run_command(
        ["adb", "-s", serial, "shell", "test", "-f", remote_path],
        check=False,
    )
    return result.returncode == 0


def load_batocera_systems_from_path(source_path: Path) -> dict:
    loader = SourceFileLoader("batocera_systems_ref", str(source_path))
    spec = importlib.util.spec_from_loader("batocera_systems_ref", loader)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load Batocera systems reference from {source_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.systems


def load_batocera_systems() -> tuple[dict | None, str]:
    try:
        with tempfile.NamedTemporaryFile(prefix="batocera-systems-", delete=False) as fh:
            tmp_path = Path(fh.name)
        try:
            urllib.request.urlretrieve(BATOCERA_REMOTE_URL, tmp_path)
            return load_batocera_systems_from_path(tmp_path), "live Batocera upstream"
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception:
        return None, "built-in fallback MD5 set"


def lookup_batocera_md5s(systems: dict, platform: str, *filenames: str) -> tuple[str, ...]:
    meta = systems.get(platform, {})
    bios_files = meta.get("biosFiles", [])
    names = {name.lower() for name in filenames}
    matches: list[str] = []
    for item in bios_files:
        file_path = item.get("file", "")
        md5 = (item.get("md5") or "").strip().lower()
        if not md5:
            continue
        if Path(file_path).name.lower() in names:
            matches.append(md5)
    deduped: list[str] = []
    for md5 in matches:
        if md5 not in deduped:
            deduped.append(md5)
    return tuple(deduped)


def apply_batocera_md5_reference() -> None:
    global BATOCERA_SOURCE_LABEL

    systems, source_label = load_batocera_systems()
    BATOCERA_SOURCE_LABEL = source_label
    if systems is None:
        return

    ps1 = FIRMWARE_GROUPS["ps1_swanstation"]
    dreamcast = FIRMWARE_GROUPS["dreamcast_flycast"]

    for item in ps1["firmware"]:
        filenames = [item.path, *item.alternates]
        md5s = lookup_batocera_md5s(systems, "psx", *filenames)
        if md5s:
            item.expected_md5 = md5s

    for item in dreamcast["firmware"]:
        filenames = [item.path, *item.alternates]
        md5s = lookup_batocera_md5s(systems, "dreamcast", *filenames)
        if md5s:
            item.expected_md5 = md5s

    ps1["hash_source"] = f"{source_label} Batocera PSX biosFiles MD5 list."
    dreamcast["hash_source"] = (
        f"{source_label} Batocera Dreamcast biosFiles MD5 list for dc_boot.bin; "
        "dc_flash.bin remains presence-only because Batocera does not define an MD5 for it there."
    )


def remote_file_md5(serial: str, remote_path: str) -> str:
    result = subprocess.run(
        ["adb", "-s", serial, "exec-out", "cat", remote_path],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="ignore").strip()
        raise RuntimeError(stderr or f"Failed to read remote file for MD5: {remote_path}")
    return hashlib.md5(result.stdout).hexdigest()


def firmware_paths(item: FirmwareSpec) -> list[str]:
    paths = [item.path]
    paths.extend(item.alternates)

    # Flycast firmware is commonly placed either directly in system/ or under system/dc/.
    if "/" not in item.path:
        paths.append(f"dc/{item.path}")

    deduped: list[str] = []
    for path in paths:
        if path not in deduped:
            deduped.append(path)
    return deduped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check expected RetroArch BIOS / firmware files on the connected Droid device."
    )
    parser.add_argument(
        "--serial",
        help="adb device serial. If omitted, the only connected device will be used.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=sorted(FIRMWARE_GROUPS),
        default=sorted(FIRMWARE_GROUPS),
        help="Limit checks to one or more firmware groups.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the full list of populated systems that do not have a rule in this script yet.",
    )
    return parser.parse_args()


def list_populated_rom_systems(serial: str) -> list[str]:
    shell_script = (
        f'for d in "{ROMS_ROOT}"/*; do '
        '[ -d "$d" ] || continue; '
        'if find "$d" -type f | grep -q .; then basename "$d"; fi; '
        "done | sort -u"
    )
    result = run_command(["adb", "-s", serial, "shell", shell_script])
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    args = parse_args()
    apply_batocera_md5_reference()
    require_adb()
    serial = resolve_serial(args.serial)

    print("=========================================================")
    print("   RETRODROID HOST ORCHESTRATOR: RETROARCH BIOS CHECK    ")
    print("=========================================================\n")
    print(f"[*] adb serial: {serial}")
    print(f"[*] ROM root: {ROMS_ROOT}")
    print(f"[*] RetroArch system directory: {RETROARCH_SYSTEM_DIR}\n")
    print(f"[*] Batocera BIOS hash source: {BATOCERA_SOURCE_LABEL}\n")

    populated_systems = list_populated_rom_systems(serial)
    if not populated_systems:
        print("[!] No populated ROM system folders were found.")
        return 0

    print(f"[*] Populated ROM systems detected: {len(populated_systems)}")
    print(f"    {', '.join(populated_systems)}\n")

    selected_groups = set(args.only)
    groups_to_check: list[str] = []
    no_firmware_needed: list[str] = []
    manual_systems: list[tuple[str, str]] = []
    unknown_systems: list[str] = []

    for system_name in populated_systems:
        rule = SYSTEM_RULES.get(system_name)
        if rule is None:
            unknown_systems.append(system_name)
            continue

        if rule.kind == "check":
            assert rule.firmware_group is not None
            if rule.firmware_group in selected_groups and rule.firmware_group not in groups_to_check:
                groups_to_check.append(rule.firmware_group)
        elif rule.kind == "no_firmware_needed":
            no_firmware_needed.append(system_name)
        elif rule.kind == "manual":
            manual_systems.append((system_name, rule.description))

    missing_required: list[tuple[str, str]] = []
    missing_optional: list[tuple[str, str]] = []
    present: list[tuple[str, str]] = []
    mismatched_required: list[tuple[str, str, str]] = []
    mismatched_optional: list[tuple[str, str, str]] = []

    if not groups_to_check:
        print("[*] No populated ROM systems matched the currently selected automated firmware checks.\n")

    for key in groups_to_check:
        group = FIRMWARE_GROUPS[key]
        print(f"[*] Checking {group['display_name']}...")
        print(f"    ES-DE system mapping: {group['esde_system']} -> {group['esde_mapping']}")
        print(f"    Note: {group['notes']}")
        if group.get("hash_source"):
            print(f"    Hash reference: {group['hash_source']}")

        for item in group["firmware"]:
            matching_path = None
            for candidate in firmware_paths(item):
                remote_path = f"{RETROARCH_SYSTEM_DIR}/{candidate}"
                if remote_file_exists(serial, remote_path):
                    matching_path = candidate
                    break

            if matching_path is not None:
                if item.expected_md5:
                    remote_path = f"{RETROARCH_SYSTEM_DIR}/{matching_path}"
                    actual_md5 = remote_file_md5(serial, remote_path)
                    if actual_md5 in item.expected_md5:
                        present.append((group["display_name"], item.path))
                        print(
                            f"    [+] Present + hash match: {matching_path} ({item.description}) "
                            f"[md5={actual_md5}]"
                        )
                    else:
                        if item.required:
                            mismatched_required.append((group["display_name"], item.path, actual_md5))
                            print(
                                f"    [-] Present but hash mismatch: {matching_path} ({item.description}) "
                                f"[md5={actual_md5}]"
                            )
                        else:
                            mismatched_optional.append((group["display_name"], item.path, actual_md5))
                            print(
                                f"    [!] Present but hash mismatch: {matching_path} ({item.description}) "
                                f"[md5={actual_md5}]"
                            )
                else:
                    present.append((group["display_name"], item.path))
                    print(f"    [+] Present: {matching_path} ({item.description})")
            else:
                if item.required:
                    missing_required.append((group["display_name"], item.path))
                    print(f"    [-] Missing required: {item.path} ({item.description})")
                else:
                    missing_optional.append((group["display_name"], item.path))
                    print(f"    [!] Missing optional: {item.path} ({item.description})")
        print()

    print("============================= SUMMARY =============================")
    print(f"[+] Populated ROM systems scanned: {len(populated_systems)}")
    print(f"[+] Firmware files present: {len(present)}")
    print(f"[!] Firmware files present but hash-mismatched: {len(mismatched_required) + len(mismatched_optional)}")
    print(f"[!] Optional firmware files missing: {len(missing_optional)}")
    print(f"[-] Required firmware files missing: {len(missing_required)}")

    if no_firmware_needed:
        print(f"\n[+] Systems with games that do not normally need BIOS / firmware: {', '.join(no_firmware_needed)}")

    if manual_systems:
        print("\n[*] Systems with games that still need manual in-app firmware handling:")
        for system_name, description in manual_systems:
            print(f"    - {system_name}: {description}")

    if unknown_systems:
        print(f"\n[!] Populated systems with no rule in this script yet: {len(unknown_systems)}")
        if args.verbose:
            print(f"    {', '.join(unknown_systems)}")
        else:
            print("    Re-run with --verbose to print the full list.")

    if missing_required:
        print("\n[-] REQUIRED ACTION")
        print(f"    Add the missing files under {RETROARCH_SYSTEM_DIR}")
        for system_name, filename in missing_required:
            print(f"    - {system_name}: {filename}")
        return 1

    if mismatched_required or mismatched_optional:
        print("\n[!] HASH MISMATCHES")
        print("    These files exist but do not match the known-good BIOS MD5s used by this script.")
        for system_name, filename, actual_md5 in mismatched_required:
            print(f"    - REQUIRED {system_name}: {filename} [md5={actual_md5}]")
        for system_name, filename, actual_md5 in mismatched_optional:
            print(f"    - OPTIONAL {system_name}: {filename} [md5={actual_md5}]")
        if mismatched_required:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
