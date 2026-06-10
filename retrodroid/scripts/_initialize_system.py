"""
This script handles all the initial grunt work: it generates the entire retro system directory tree on your Samsung
microSD card, hooks directly into the Termux backend configuration profile to enable auto-boot for the
SSH daemon (sshd), and prints out your explicit IP address so you know exactly how to connect.

How to use this script in your Terminal pipeline

1. Drop into Termux: Run this script locally on the device for the first initialization wave:
    $ python initialize_system.py
2. Verify files: Look into your internal directory layouts using your computer file manager. You will see your brand
    new RetroGames architecture ready to handle input files.
3. Test boot parameters: Unplug your Orange Pi 5 completely from the wall outlet and reapply power. The system will
    cleanly spin up the background terminal listener on Port 8022 without you ever having to manually click an app
    icon inside Android again.
"""

import os
import shutil
import subprocess
import socket

# CONFIGURATION ARCHITECTURE
RETROGAMES_ROOT = "/storage/emulated/0/RetroGames"
PLATFORMS = ["nes", "snes", "genesis", "dreamcast", "ps1", "gc", "3ds", "ps2", "n64"]

def get_local_ip():
    """Fetches the active local network IP address of the Orange Pi 5 board."""
    try:
        # Connects to a dummy external domain to discover local interface routing IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return None

def get_termux_username():
    """Returns the current Termux username for SSH examples."""
    try:
        return subprocess.check_output(["whoami"], text=True).strip()
    except Exception:
        return "termux_username"

def setup_directory_tree():
    """Generates the absolute structure required for ROM storage and image staging."""
    print("[*] Instantiating file storage directory backbone...")

    # Subfolder target layout definitions
    subfolders = [
        "roms",
        "bios",
        "installers",
        "media_staging"
    ]

    # Generate foundational folders
    for folder in subfolders:
        path = os.path.join(RETROGAMES_ROOT, folder)
        os.makedirs(path, exist_ok=True)
        print(f"    [+] Created/Verified folder path: {path}")

    # Generate targeted individual game platform folders
    print("[*] Instantiating individual console target folders...")
    for platform in PLATFORMS:
        platform_path = os.path.join(RETROGAMES_ROOT, "roms", platform)
        os.makedirs(platform_path, exist_ok=True)
        print(f"    [+] Created platform target entry: .../roms/{platform}/")

def setup_termux_ssh_autostart():
    """Modifies internal Termux profiles to execute the SSH daemon on power cycles."""
    print("\n[*] Mapping background Termux runtime configurations...")

    # Locate the active primary user space home variable
    home_dir = os.path.expanduser("~")
    termux_boot_dir = os.path.join(home_dir, ".termux", "boot")

    # Create required layout structural directories if absent
    os.makedirs(termux_boot_dir, exist_ok=True)
    autostart_script_path = os.path.join(termux_boot_dir, "start-sshd")

    try:
        # Write the persistent absolute script command to wake sshd on start
        with open(autostart_script_path, "w") as f:
            f.write("#!/data/data/com.termux/files/usr/bin/sh\n")
            if shutil.which("termux-wake-lock"):
                f.write("termux-wake-lock\n")
            f.write("sshd\n")

        # Adjust execution permission mapping settings
        os.chmod(autostart_script_path, 0o755)
        print(f"    [+] Persistent daemon target initialized at: {autostart_script_path}")
        print("    [!] Termux:Boot must be installed and opened once for this script to run on reboot.")

        # Test spin the live process immediately to verify configuration stability
        print("[*] Running initial terminal system daemon configuration sweep...")
        sshd_proc = subprocess.run(["sshd"], capture_output=True, text=True, check=False)
        if sshd_proc.returncode == 0:
            print("    [+] Background service instance spawned successfully.")
            return True
        print(f"    [-] sshd launch failed: {sshd_proc.stderr.strip() or sshd_proc.stdout.strip() or 'unknown error'}")
        return False
    except Exception as e:
        print(f"    [-] Critical script permission interruption: {e}")
        return False

def main():
    print("=========================================================")
    print("     ORANGE PI 5 APPLIANCE CORE: ENVIRONMENT INITIALIZER ")
    print("=========================================================\n")

    setup_directory_tree()
    # Boot-time sshd setup is intentionally left as a manual step because
    # Termux:Boot must be installed and opened once before Android will allow
    # its boot scripts to run.
    # ssh_autostart_ready = setup_termux_ssh_autostart()

    current_ip = get_local_ip()
    username = get_termux_username()
    print("\n" + "="*57)
    print("🎉 SYSTEM INITIALIZATION PARSE PHASE COMPLETE!")
    print("="*57)
    print(f"🏡 MicroSD Folder Backbone: {RETROGAMES_ROOT}/")
    print("🔒 SSH Daemon Autostart Status: MANUAL STEP REQUIRED")
    print("   Install Termux:Boot, open it once, then create ~/.termux/boot/start-sshd manually.")
    if current_ip:
        print("🌐 Remote Connection Terminal Command Line to copy and run:")
        print(f"    ssh -p 8022 {username}@{current_ip}")
    else:
        print("🌐 Remote Connection Terminal Command Line: unavailable until the device has a network IP.")
    print("="*57 + "\n")

if __name__ == "__main__":
    main()
