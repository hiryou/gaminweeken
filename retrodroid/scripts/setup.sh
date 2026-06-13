#!/data/data/com.termux/files/usr/bin/sh

set -eu

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKDIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
PREFIX_BIN="${PREFIX:-/data/data/com.termux/files/usr}/bin"

echo "========================================================="
echo "    ORANGE PI 5 APPLIANCE: CENTRAL CONTROLLER INTERFACE  "
echo "========================================================="

mkdir -p "$WORKDIR"

if [ -d "$PREFIX_BIN" ]; then
    ln -sf "$SCRIPTS_DIR/setup.sh" "$PREFIX_BIN/setup.sh"
fi

cd "$SCRIPTS_DIR"

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPTS_DIR/_setup.py" "$@"
fi

exec python "$SCRIPTS_DIR/_setup.py" "$@"
