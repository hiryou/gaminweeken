# Source this file before running host-side setup commands:
#   . config/droid-config.sh
#
# Then you can use:
#   "$DROID_SSH_TARGET"
#   "$DROID_ADB_SERIAL"

# termux / transport
export DROID_ADDRESS=192.168.0.99
export ADB_PORT=5555
export SSH_PORT=8022
export SSH_USER=u0_a77

export TERMUX_SHELL_HELPER_ROOT=~/.config/retrodroid/shell

export REMOTE_WORKDIR=/sdcard/Download/retrodroid

export ESDE_ROOT=/sdcard/ES-DE
export RETROARCH_DIR=/sdcard/RetroArch
export RETRO_GAMES_DIR=/sdcard/RetroGames

export RETROARCH_SUBDIR_SYSTEM=system
export RETROARCH_SUBDIR_CORES=cores
export RETROARCH_SUBDIR_INFO=info

# convenient derived shell values for user-facing commands
export DROID_SSH_TARGET="${SSH_USER}@${DROID_ADDRESS}"
export DROID_ADB_SERIAL="${DROID_ADDRESS}:${ADB_PORT}"
export ESDE_CUSTOM_SYSTEMS_DIR="${ESDE_ROOT}/custom_systems"

# these are expected subpaths by software - here for ref, not as configured
#termux_boot_dir=~/.termux/boot
#esde_custom_systems_dir=/sdcard/ES-DE/custom_systems
# leave out for now
#vita3k_root=/sdcard/Android/data/org.vita3k.emulator/files

# for later games convenient sync
export LOCAL_RETROGAMING_DIR="/Users/longn/Downloads/retrogaming"

if ! adb devices | awk '$2 == "device" {print $1}' | grep -qx "$DROID_ADB_SERIAL"; then
    adb connect "$DROID_ADB_SERIAL"
fi
adb devices
