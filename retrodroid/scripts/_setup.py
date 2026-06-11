"""
One-shot device-side setup for RetroDroid directory initialization.
"""

from __future__ import annotations

import sys
from pathlib import Path

import _initialize_system


WORKDIR = Path("/sdcard/Download/retrodroid")
TERMUX_ARTIFACTS_DIR = WORKDIR / "artifacts" / "termux"


def main() -> int:
    WORKDIR.mkdir(parents=True, exist_ok=True)

    print("[*] Initializing RetroDroid folder structure...")
    _initialize_system.setup_directory_tree()
    _initialize_system.install_termux_shell_helpers(TERMUX_ARTIFACTS_DIR)

    print("\n============================= SUMMARY =============================")
    print("[+] Device-side setup complete.")
    print(f"[+] Working directory ensured: {WORKDIR}")
    print("[+] Termux bash helper installed: watch_cpu")
    print("[*] APK download and installation are now host-side tasks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
