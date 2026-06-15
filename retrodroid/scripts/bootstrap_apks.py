"""
Install locally tracked APK artifacts onto a connected Droid device via adb.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MANIFEST_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "apks"
DEFAULT_DOWNLOAD_DIR = DEFAULT_MANIFEST_DIR
OPTIONAL_LOCAL_APK_RULES = [
    {
        "match_prefixes": ("ES-DE", "ES_DE", "es-de", "es_de", "EmulationStation"),
        "emulator": "esde",
    },
]
APK_INSTALL_RULES = [
    {
        "match_prefixes": ("RetroArch",),
        "emulator": "retroarch",
        "grep_tokens": ("retroarch",),
    },
    {
        "match_prefixes": ("Mupen64PlusAE",),
        "emulator": "mupen64plusae",
        "grep_tokens": ("mupen",),
    },
    {
        "match_prefixes": ("app-mainline-release",),
        "emulator": "citron",
        "grep_tokens": ("citron",),
    },
    {
        "match_prefixes": ("azaharplus-",),
        "emulator": "azaharplus",
        "grep_tokens": ("azahar",),
    },
    {
        "match_prefixes": ("citra",),
        "emulator": "citra",
        "grep_tokens": ("citra",),
    },
    {
        "match_prefixes": ("lime3ds",),
        "emulator": "lime3ds",
        "grep_tokens": ("lime3ds",),
    },
    {
        "match_prefixes": ("Sudachi", "sudachi"),
        "emulator": "sudachi",
        "grep_tokens": ("sudachi",),
    },
    {
        "match_prefixes": ("yuzu", "Yuzu"),
        "emulator": "yuzu",
        "grep_tokens": ("yuzu",),
    },
    {
        "match_prefixes": ("AetherSX2", "NetherSX2"),
        "emulator": "aethersx2_family",
        "grep_tokens": ("aether", "nethersx2"),
    },
    {
        "match_prefixes": ("PCSX2", "pcsx2"),
        "emulator": "pcsx2",
        "grep_tokens": ("pcsx2",),
    },
    {
        "match_prefixes": ("Dolphin",),
        "emulator": "dolphin",
        "grep_tokens": ("dolphin",),
    },
    {
        "match_prefixes": ("ppsspp",),
        "emulator": "ppsspp",
        "grep_tokens": ("ppsspp",),
    },
    {
        "match_prefixes": ("aPS3e-", "aps3e-"),
        "emulator": "aps3e",
        "grep_tokens": ("aps3e",),
    },
    {
        "match_prefixes": ("rpcsx-release", "RPCSX", "rpcsx"),
        "emulator": "rpcsx",
        "grep_tokens": ("rpcsx",),
    },
    {
        "match_prefixes": ("duckstation", "DuckStation"),
        "emulator": "duckstation",
        "grep_tokens": ("duckstation",),
    },
    {
        "match_prefixes": ("ES-DE", "ES_DE", "es-de", "es_de", "EmulationStation"),
        "emulator": "esde",
        "grep_tokens": ("emulationstation", "es_de", "es-de"),
    },
]


@dataclass(frozen=True)
class ApkManifest:
    manifest_path: Path
    emulator: str
    filename: str
    source_url: str
    sha256: str
    size: int
    optional: bool = False

    @property
    def download_path(self) -> Path:
        return DEFAULT_DOWNLOAD_DIR / self.filename


@dataclass(frozen=True)
class OptionalLocalApk:
    emulator: str
    apk_path: Path


def require_adb() -> None:
    result = subprocess.run(["adb", "version"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError("`adb` is not available in PATH")


def list_adb_devices() -> list[str]:
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to query adb devices")

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


def list_installed_packages(serial: str) -> list[str]:
    result = subprocess.run(
        ["adb", "-s", serial, "shell", "pm", "list", "packages"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to query installed packages from the device")

    packages: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            packages.append(line.removeprefix("package:"))
    return packages


def resolve_install_rule(apk_name: str) -> dict[str, object] | None:
    normalized_name = apk_name.lower()
    for rule in APK_INSTALL_RULES:
        prefixes = rule["match_prefixes"]
        if any(normalized_name.startswith(prefix.lower()) for prefix in prefixes):
            return rule
    return None


def resolve_install_rule_for_emulator(emulator: str) -> dict[str, object] | None:
    normalized_emulator = emulator.lower()
    for rule in APK_INSTALL_RULES:
        if str(rule["emulator"]).lower() == normalized_emulator:
            return rule
    return None


def find_existing_emulator_packages(manifest: ApkManifest, installed_packages: list[str]) -> tuple[str | None, list[str]]:
    rule = resolve_install_rule_for_emulator(manifest.emulator)
    if rule is None:
        rule = resolve_install_rule(manifest.filename)
    if rule is None:
        return None, []

    grep_tokens = rule["grep_tokens"]
    matches = [
        package
        for package in installed_packages
        if any(token in package.lower() for token in grep_tokens)
    ]
    return str(rule["emulator"]), matches


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as apk_file:
        for chunk in iter(lambda: apk_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(manifest_path: Path) -> ApkManifest:
    data = json.loads(manifest_path.read_text())
    required_fields = ("emulator", "filename", "source_url", "sha256", "size")
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise RuntimeError(f"{manifest_path.name} is missing required fields: {', '.join(missing)}")
    return ApkManifest(
        manifest_path=manifest_path,
        emulator=str(data["emulator"]),
        filename=str(data["filename"]),
        source_url=str(data["source_url"]),
        sha256=str(data["sha256"]),
        size=int(data["size"]),
        optional=bool(data.get("optional", False)),
    )


def resolve_manifests(manifest_dir: Path) -> list[ApkManifest]:
    manifest_paths = sorted(manifest_dir.glob("*.json"))
    return [load_manifest(path) for path in manifest_paths]


def verify_downloaded_apk(manifest: ApkManifest, download_dir: Path) -> tuple[bool, str]:
    apk_path = download_dir / manifest.filename
    if not apk_path.exists():
        return False, f"downloaded APK not found: {apk_path}"
    actual_size = apk_path.stat().st_size
    if actual_size != manifest.size:
        return False, f"size mismatch for {apk_path.name}: expected {manifest.size}, got {actual_size}"
    actual_sha256 = sha256_file(apk_path)
    if actual_sha256 != manifest.sha256:
        return False, (
            f"sha256 mismatch for {apk_path.name}: expected {manifest.sha256}, got {actual_sha256}"
        )
    return True, str(apk_path)


def list_device_abis(serial: str) -> list[str]:
    result = subprocess.run(
        ["adb", "-s", serial, "shell", "getprop", "ro.product.cpu.abilist"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        abis = [abi.strip() for abi in result.stdout.strip().split(",") if abi.strip()]
        if abis:
            return abis

    fallback = subprocess.run(
        ["adb", "-s", serial, "shell", "getprop", "ro.product.cpu.abi"],
        capture_output=True,
        text=True,
        check=False,
    )
    if fallback.returncode != 0:
        raise RuntimeError(fallback.stderr.strip() or "Failed to query device ABI")
    abi = fallback.stdout.strip()
    return [abi] if abi else []


def verify_local_apk(apk_path: Path) -> tuple[bool, str]:
    if not apk_path.exists():
        return False, f"APK not found: {apk_path}"
    if not apk_path.is_file():
        return False, f"APK path is not a file: {apk_path}"
    with apk_path.open("rb") as apk_file:
        header = apk_file.read(4)
    if header != b"PK\x03\x04":
        return False, f"{apk_path.name} is not a valid APK/ZIP payload"
    return True, str(apk_path)


def install_apkm(serial: str, apkm_path: Path) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="retrodroid_apkm_") as temp_dir:
        temp_root = Path(temp_dir)
        with zipfile.ZipFile(apkm_path) as archive:
            archive.extractall(temp_root)

        base_apk = temp_root / "base.apk"
        if not base_apk.exists():
            return False, f"{apkm_path.name} is missing base.apk"

        chosen_split: Path | None = None
        device_abis = list_device_abis(serial)
        for abi in device_abis:
            candidate = temp_root / f"split_config.{abi.replace('-', '_')}.apk"
            if candidate.exists():
                chosen_split = candidate
                break

        if chosen_split is None:
            return False, (
                f"no matching ABI split found in {apkm_path.name} for device ABIs: "
                f"{', '.join(device_abis) or 'unknown'}"
            )

        result = subprocess.run(
            ["adb", "-s", serial, "install-multiple", "-r", str(base_apk), str(chosen_split)],
            capture_output=True,
            text=True,
            check=False,
        )
        details = "\n".join(
            part.strip() for part in (result.stdout, result.stderr) if part and part.strip()
        ).strip()
        if result.returncode == 0 and "Success" in details:
            return True, details
        if not details:
            details = f"`adb install-multiple` exited with status {result.returncode}"
        return False, details


def resolve_optional_local_apks(download_dir: Path, manifests: list[ApkManifest]) -> list[OptionalLocalApk]:
    manifest_filenames = {manifest.filename for manifest in manifests}
    optional_apks: list[OptionalLocalApk] = []

    for apk_path in sorted(download_dir.glob("*.apk")):
        if apk_path.name in manifest_filenames:
            continue
        normalized_name = apk_path.name.lower()
        for rule in OPTIONAL_LOCAL_APK_RULES:
            prefixes = rule["match_prefixes"]
            if any(normalized_name.startswith(prefix.lower()) for prefix in prefixes):
                optional_apks.append(
                    OptionalLocalApk(
                        emulator=str(rule["emulator"]),
                        apk_path=apk_path,
                    )
                )
                break

    return optional_apks


def find_existing_packages_for_emulator(emulator: str, apk_name: str, installed_packages: list[str]) -> tuple[str | None, list[str]]:
    rule = resolve_install_rule_for_emulator(emulator)
    if rule is None:
        rule = resolve_install_rule(apk_name)
    if rule is None:
        return None, []

    grep_tokens = rule["grep_tokens"]
    matches = [
        package
        for package in installed_packages
        if any(token in package.lower() for token in grep_tokens)
    ]
    return str(rule["emulator"]), matches


def install_apk(serial: str, apk_path: Path) -> tuple[bool, str]:
    if apk_path.suffix.lower() == ".apkm":
        return install_apkm(serial, apk_path)

    result = subprocess.run(
        ["adb", "-s", serial, "install", "-r", str(apk_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    details = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part and part.strip()
    ).strip()
    if result.returncode == 0 and "Success" in details:
        return True, details
    if not details:
        details = f"`adb install` exited with status {result.returncode}"
    return False, details


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install local APK artifacts onto a connected Droid device.")
    parser.add_argument(
        "--apk-dir",
        default=str(DEFAULT_MANIFEST_DIR),
        help=f"Directory containing local APK manifest files to install (default: {DEFAULT_MANIFEST_DIR})",
    )
    parser.add_argument(
        "--download-dir",
        default=str(DEFAULT_DOWNLOAD_DIR),
        help=f"Directory containing downloaded APK payloads (default: {DEFAULT_DOWNLOAD_DIR})",
    )
    parser.add_argument(
        "--serial",
        help="adb device serial. If omitted, bootstrap_apks.py will use the only connected device.",
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Evaluate idempotency checks and print what would happen without installing any APKs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_adb()

    manifest_dir = Path(args.apk_dir)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    download_dir = Path(args.download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)
    manifests = resolve_manifests(manifest_dir)
    if not manifests:
        print(f"[-] No APK manifest files found under {manifest_dir}")
        return 1

    serial = resolve_serial(args.serial)
    installed_packages = list_installed_packages(serial)
    optional_local_apks = resolve_optional_local_apks(download_dir, manifests)

    print("=========================================================")
    print("      RETRODROID HOST INSTALLER: APK BOOTSTRAP PIPELINE  ")
    print("=========================================================\n")
    print(f"[*] adb serial: {serial}")
    print(f"[*] local manifest directory: {manifest_dir}")
    print(f"[*] local APK payload directory: {download_dir}\n")
    if optional_local_apks:
        print("[*] Optional local APKs detected for install-after-emulators:")
        for apk in optional_local_apks:
            print(f"    - {apk.apk_path.name}")
        print()
    if args.dryrun:
        print("[*] Dry run mode enabled. No APK installs will be executed.\n")

    installed: list[str] = []
    skipped: list[tuple[str, str]] = []
    planned: list[str] = []
    failed: list[tuple[str, str]] = []

    for manifest in manifests:
        ok, verification = verify_downloaded_apk(manifest, download_dir)
        if not ok:
            if manifest.optional and verification.startswith("downloaded APK not found:"):
                details = f"optional local payload missing: {manifest.filename}"
                skipped.append((manifest.filename, details))
                print(f"[*] Skipping {manifest.filename}...")
                print(f"    [!] {details}")
                continue
            failed.append((manifest.filename, verification))
            print(f"[*] Cannot use {manifest.filename}...")
            print(f"    [-] {verification}")
            continue

        apk_path = Path(verification)
        emulator, existing_packages = find_existing_emulator_packages(manifest, installed_packages)
        if existing_packages:
            details = (
                f"emulator `{emulator}` already has installed package(s): "
                f"{', '.join(existing_packages)}. Uninstall the old emulator manually before installing {manifest.filename}."
            )
            skipped.append((manifest.filename, details))
            print(f"[*] Skipping {manifest.filename}...")
            print(f"    [!] {details}")
            continue

        if args.dryrun:
            planned.append(manifest.filename)
            print(f"[+] Would install {manifest.filename}...")
            continue

        print(f"[*] Installing {manifest.filename}...")
        ok, details = install_apk(serial, apk_path)
        if ok:
            installed.append(manifest.filename)
            print(f"    [+] Installed: {manifest.filename}")
        else:
            failed.append((manifest.filename, details))
            print(f"    [-] Install failed: {manifest.filename}")
            print(f"        {details}")

    for optional_apk in optional_local_apks:
        ok, verification = verify_local_apk(optional_apk.apk_path)
        if not ok:
            failed.append((optional_apk.apk_path.name, verification))
            print(f"[*] Cannot use {optional_apk.apk_path.name}...")
            print(f"    [-] {verification}")
            continue

        emulator, existing_packages = find_existing_packages_for_emulator(
            optional_apk.emulator,
            optional_apk.apk_path.name,
            installed_packages,
        )
        if existing_packages:
            details = (
                f"emulator `{emulator}` already has installed package(s): "
                f"{', '.join(existing_packages)}. Uninstall the old emulator manually before installing {optional_apk.apk_path.name}."
            )
            skipped.append((optional_apk.apk_path.name, details))
            print(f"[*] Skipping {optional_apk.apk_path.name}...")
            print(f"    [!] {details}")
            continue

        if args.dryrun:
            planned.append(optional_apk.apk_path.name)
            print(f"[+] Would install {optional_apk.apk_path.name}...")
            continue

        print(f"[*] Installing {optional_apk.apk_path.name}...")
        ok, details = install_apk(serial, optional_apk.apk_path)
        if ok:
            installed.append(optional_apk.apk_path.name)
            print(f"    [+] Installed: {optional_apk.apk_path.name}")
        else:
            failed.append((optional_apk.apk_path.name, details))
            print(f"    [-] Install failed: {optional_apk.apk_path.name}")
            print(f"        {details}")

    print("\n============================= SUMMARY =============================")
    print(f"[+] Local APK manifests discovered: {len(manifests)}")
    if planned:
        print(f"[+] APK installs planned: {len(planned)}")
        for apk_name in planned:
            print(f"    - {apk_name}")
    print(f"[+] APK installs succeeded: {len(installed)}")
    for apk_name in installed:
        print(f"    - {apk_name}")

    if skipped:
        print(f"\n[!] APK installs skipped: {len(skipped)}")
        for apk_name, details in skipped:
            print(f"    - {apk_name}: {details}")

    if failed:
        print(f"\n[-] APK installs failed: {len(failed)}")
        for apk_name, details in failed:
            print(f"    - {apk_name}: {details}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
