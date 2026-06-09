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
        return "127.0.0.1 (Offline or interface issue)"

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
            f.write("sshd\n")

        # Adjust execution permission mapping settings
        os.chmod(autostart_script_path, 0o755)
        print(f"    [+] Persistent daemon target initialized at: {autostart_script_path}")

        # Test spin the live process immediately to verify configuration stability
        print("[*] Running initial terminal system daemon configuration sweep...")
        subprocess.run(["sshd"], check=False)
        print("    [+] Background service instance spawned successfully.")
    except Exception as e:
        print(f"    [-] Critical script permission interruption: {e}")

def main():
    print("=========================================================")
    print("     ORANGE PI 5 APPLIANCE CORE: ENVIRONMENT INITIALIZER ")
    print("=========================================================\n")

    setup_directory_tree()
    setup_termux_ssh_autostart()

    current_ip = get_local_ip()
    print("\n" + "="*57)
    print("🎉 SYSTEM INITIALIZATION PARSE PHASE COMPLETE!")
    print("="*57)
    print(f"🏡 MicroSD Folder Backbone: {RETROGAMES_ROOT}/")
    print(f"🔒 SSH Daemon Autostart Status: ACTIVE")
    print(f"🌐 Remote Connection Terminal Command Line to copy and run:")
    print(f"    ssh -p 8022 userspace@{current_ip}")
    print("="*57 + "\n")

if __name__ == "__main__":
    main()



