#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONFIG_FILE="$SCRIPT_DIR/config/droid-config.sh"
[ -f "$CONFIG_FILE" ] || {
    echo "Missing config file: $CONFIG_FILE" >&2
    exit 1
}

# shellcheck disable=SC1090
. "$CONFIG_FILE"

REMOTE_WORKDIR="${REMOTE_WORKDIR:-/sdcard/Download/retrodroid}"
ESDE_ROOT="${ESDE_ROOT:-/sdcard/ES-DE}"
REMOTE_ESDE_CUSTOM_SYSTEMS="${ESDE_ROOT}/custom_systems"
SSH_PORT="${SSH_PORT:-8022}"
DEFAULT_DROID_ADDRESS="${DROID_ADDRESS:-}"
DEFAULT_SSH_USER="${SSH_USER:-}"
DEFAULT_ADB_PORT="${ADB_PORT:-5555}"
DEFAULT_SSH_TARGET="${DROID_SSH_TARGET:-}"
DEFAULT_ADB_SERIAL="${DROID_ADB_SERIAL:-}"
DRYRUN=0

if [ -z "$DEFAULT_SSH_TARGET" ] && [ -n "$DEFAULT_SSH_USER" ] && [ -n "$DEFAULT_DROID_ADDRESS" ]; then
    DEFAULT_SSH_TARGET="${DEFAULT_SSH_USER}@${DEFAULT_DROID_ADDRESS}"
fi

if [ -z "$DEFAULT_ADB_SERIAL" ] && [ -n "$DEFAULT_DROID_ADDRESS" ]; then
    DEFAULT_ADB_SERIAL="${DEFAULT_DROID_ADDRESS}:${DEFAULT_ADB_PORT}"
fi

usage() {
    echo "Usage: $0 [<ssh_target> [adb_serial]]"
    echo "Usage: $0 --dryrun [adb_serial]"
    if [ -n "$DEFAULT_SSH_TARGET" ]; then
        echo "Example: $0"
        echo "Example: $0 ${DEFAULT_SSH_TARGET}"
    fi
    if [ -n "$DEFAULT_SSH_TARGET" ] && [ -n "$DEFAULT_ADB_SERIAL" ]; then
        echo "Example: $0 ${DEFAULT_SSH_TARGET} ${DEFAULT_ADB_SERIAL}"
    fi
    echo "Example: $0 --dryrun"
    if [ -n "$DEFAULT_ADB_SERIAL" ]; then
        echo "Example: $0 --dryrun ${DEFAULT_ADB_SERIAL}"
    fi
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Missing required command: $1" >&2
        exit 1
    fi
}

find_local_esde_apk() {
    local apk_dir="artifacts/apks"
    if [ ! -d "$apk_dir" ]; then
        return 1
    fi

    local candidate
    while IFS= read -r candidate; do
        case "$(basename "$candidate")" in
            ES-DE*.apk|ES_DE*.apk|es-de*.apk|es_de*.apk|EmulationStation*.apk)
                echo "$candidate"
                return 0
                ;;
        esac
    done < <(find "$apk_dir" -maxdepth 1 -type f -name '*.apk' | sort)

    return 1
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
    local payload=("scripts" "config/droid-config.sh")

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
    if [ $# -gt 2 ]; then
        usage
        exit 1
    fi
    if [ $# -eq 0 ] && [ -z "$DEFAULT_SSH_TARGET" ]; then
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

if [ "$DRYRUN" -eq 1 ]; then
    ADB_SERIAL="$(resolve_adb_serial "${1:-$DEFAULT_ADB_SERIAL}")"
else
    SSH_TARGET="${1:-$DEFAULT_SSH_TARGET}"
    ADB_SERIAL="$(resolve_adb_serial "${2:-$DEFAULT_ADB_SERIAL}")"
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
    tar czf - "${REMOTE_PAYLOAD[@]}" | ssh -p "$SSH_PORT" "$SSH_TARGET" \
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

echo
if ! ESDE_APK_PATH="$(find_local_esde_apk)"; then
    echo "[-] Required ES-DE APK is missing under artifacts/apks/" >&2
    echo "    Buy ES-DE once from https://es-de.org/ and place the APK in artifacts/apks/ before rerunning setup_droid.sh." >&2
    exit 1
fi
echo "[+] ES-DE APK found: $ESDE_APK_PATH"
