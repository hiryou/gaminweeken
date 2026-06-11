#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

REMOTE_WORKDIR="/sdcard/Download/retrodroid"
REMOTE_ESDE_CUSTOM_SYSTEMS="/sdcard/ES-DE/custom_systems"
DRYRUN=0

usage() {
    echo "Usage: $0 [--dryrun] <ssh_target> [adb_serial]"
    echo "Usage: $0 --dryrun [adb_serial]"
    echo "Example: $0 u0_a77@192.168.0.99"
    echo "Example: $0 u0_a77@192.168.0.99 192.168.0.99:5555"
    echo "Example: $0 --dryrun"
    echo "Example: $0 --dryrun 192.168.0.99:5555"
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Missing required command: $1" >&2
        exit 1
    fi
}

sync_esde_custom_systems() {
    if [ ! -d artifacts/custom_systems ]; then
        return
    fi

    local xml_count
    xml_count=$(find artifacts/custom_systems -maxdepth 1 -type f -name '*.xml' | wc -l | tr -d ' ')
    if [ "$xml_count" = "0" ]; then
        return
    fi

    # artifacts/custom_systems/* was last sourced from
    # https://github.com/GlazedBelmont/es-de-android-custom-systems/releases/download/v1.50/es_find_rules.xml
    # https://github.com/GlazedBelmont/es-de-android-custom-systems/releases/download/v1.50/es_systems.xml

    echo
    echo "[*] Syncing ES-DE custom system XMLs via adb..."
    adb shell "mkdir -p '$REMOTE_ESDE_CUSTOM_SYSTEMS'"
    adb push artifacts/custom_systems/. "$REMOTE_ESDE_CUSTOM_SYSTEMS/" >/dev/null
}

build_remote_payload_args() {
    local payload=("scripts")

    if [ -d artifacts/termux ]; then
        payload+=("artifacts/termux")
    fi

    printf '%s\n' "${payload[@]}"
}

resolve_adb_serial() {
    if [ "${1:-}" != "" ]; then
        echo "$1"
        return
    fi

    devices=()
    while IFS= read -r line; do
        devices+=("$line")
    done < <(adb devices | awk 'NR>1 && $2=="device" {print $1}')

    if [ "${#devices[@]}" -eq 1 ]; then
        echo "${devices[0]}"
        return
    fi

    echo "Unable to infer adb serial. Pass it explicitly." >&2
    adb devices >&2
    exit 1
}

POSITIONAL=()
for arg in "$@"; do
    case "$arg" in
        --dryrun)
            DRYRUN=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            POSITIONAL+=("$arg")
            ;;
    esac
done

if [ ${#POSITIONAL[@]} -gt 0 ]; then
    set -- "${POSITIONAL[@]}"
else
    set --
fi

if [ "$DRYRUN" -eq 1 ]; then
    if [ $# -gt 1 ]; then
        usage
        exit 1
    fi
else
    if [ $# -lt 1 ] || [ $# -gt 2 ]; then
        usage
        exit 1
    fi
fi

require_cmd adb
require_cmd python3

if [ "$DRYRUN" -eq 0 ]; then
    require_cmd ssh
    require_cmd tar
fi

SSH_TARGET="${1:-}"
if [ "$DRYRUN" -eq 1 ]; then
    ADB_SERIAL="$(resolve_adb_serial "${1:-}")"
else
    ADB_SERIAL="$(resolve_adb_serial "${2:-}")"
fi

echo "========================================================="
echo "       RETRODROID HOST ORCHESTRATOR: SETUP PIPELINE      "
echo "========================================================="
if [ "$DRYRUN" -eq 0 ]; then
    echo "[*] SSH target: $SSH_TARGET"
else
    echo "[*] Dry run mode enabled. Remote SSH setup will be skipped."
fi
echo "[*] ADB serial: $ADB_SERIAL"

if [ "$DRYRUN" -eq 0 ]; then
    echo
    echo "[*] Streaming scripts/ to the device and running remote setup..."
    REMOTE_PAYLOAD=()
    while IFS= read -r payload_path; do
        REMOTE_PAYLOAD+=("$payload_path")
    done < <(build_remote_payload_args)
    tar czf - "${REMOTE_PAYLOAD[@]}" | ssh -p 8022 "$SSH_TARGET" \
        "mkdir -p '$REMOTE_WORKDIR' && tar xzf - -C '$REMOTE_WORKDIR' && bash '$REMOTE_WORKDIR/scripts/setup.sh'"

    sync_esde_custom_systems
elif [ -d artifacts/custom_systems ] && find artifacts/custom_systems -maxdepth 1 -type f -name '*.xml' | grep -q .; then
    echo
    echo "[*] Dry run mode enabled. ES-DE custom system XML sync will be skipped."
fi

echo
if [ "$DRYRUN" -eq 1 ]; then
    echo "[*] Dry-running host-tracked APK artifacts via adb..."
    python3 scripts/bootstrap_apks.py --serial "$ADB_SERIAL" --dryrun
else
    echo "[*] Installing host-tracked APK artifacts via adb..."
    python3 scripts/bootstrap_apks.py --serial "$ADB_SERIAL"
fi
