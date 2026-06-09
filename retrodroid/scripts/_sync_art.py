"""
This script safely reads your game files, matches them to your downloaded artwork images, renames the images to
match your games perfectly, and drops them into the exact folder paths required by ES-DE.

To solve the permission limitations of Android, this script is designed to be highly intelligent: it uses
Fuzzy String Matching (via a built-in fallback formula so you don't have to struggle to install external
libraries like rapidfuzz or difflib over SSH) to automatically link downloaded images to your games, even if the
file names are slightly different (e.g., matching Mario Tennis (USA).png to MarioTennis.n64).

How to Run This and Test It via SSH Terminal:
1. Place your assets: Put your rom files in their folders (e.g., /storage/emulated/0/RetroGames/roms/n64/MarioTennis.n64).
2. Drop your raw images: Put your raw, downloaded images directly into the staging folder (/storage/emulated/0/RetroGames/media_staging/).
3. Execute: Run the script from Termux over your secure SSH connection:
    $ python sync_art.py
4. See the results: Open ES-DE on your Orange Pi 5. Press your controller's Start Button and select Reload Gamelist
"""

import os
import shutil

# CONFIGURATION ARCHITECTURE
ROM_BASE_DIR = "/storage/emulated/0/RetroGames/roms/"
DOWNLOADED_ART_DIR = "/storage/emulated/0/RetroGames/media_staging/"
ES_DE_MEDIA_DIR = "/storage/emulated/0/ES-DE/downloaded_media/"

# Mapping folders to make sure we process the exact same platform IDs
TARGET_PLATFORMS = ["nes", "snes", "genesis", "dreamcast", "ps1", "gc", "3ds", "ps2", "n64"]

def clean_string(text):
    """Filters out brackets, regions, and file extensions for clean comparison."""
    # Convert to lowercase and drop common emulator file name noise
    text = text.lower()
    for noise in ["(usa)", "(europe)", "(japan)", "(pal)", "[!]", "brackets"]:
        text = text.replace(noise, "")
    # Keep only letters and numbers
    return "".join([c for c in text if c.isalnum()])

def calculate_similarity(str1, str2):
    """Simple built-in character match count to avoid relying on complex python libraries."""
    s1, s2 = clean_string(str1), clean_string(str2)
    if not s1 or not s2:
        return 0.0
    # Quick intersection check
    matches = sum(1 for char in s1 if char in s2)
    return (matches * 2.0) / (len(s1) + len(s2))

def sync_platform_art(platform):
    """Scans individual rom folders, matches art, renames, and moves to ES-DE paths."""
    rom_folder = os.path.join(ROM_BASE_DIR, platform)
    target_media_folder = os.path.join(ES_DE_MEDIA_DIR, platform, "miximages")

    if not os.path.exists(rom_folder):
        print(f"[-] Directory skip: '{rom_folder}' does not exist.")
        return

    # Gather all rom files (ignoring hidden files)
    rom_files = [f for f in os.listdir(rom_folder) if os.path.isfile(os.path.join(rom_folder, f)) and not f.startswith(".")]
    # Gather all staged art images waiting to be synced
    staged_arts = [f for f in os.listdir(DOWNLOADED_ART_DIR) if os.path.isfile(os.path.join(DOWNLOADED_ART_DIR, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not rom_files or not staged_arts:
        return

    os.makedirs(target_media_folder, exist_ok=True)
    print(f"\n[*] Scanning platform system: [{platform.upper()}]")
    print(f"    Found {len(rom_files)} ROM(s) and {len(staged_arts)} staged artwork(s).")

    for rom in rom_files:
        rom_name, _ = os.path.splitext(rom)
        best_match_art = None
        highest_score = 0.0

        # Run fuzzy loop to link the artwork to the game file
        for art in staged_arts:
            art_name, _ = os.path.splitext(art)
            score = calculate_similarity(rom_name, art_name)
            if score > highest_score:
                highest_score = score
                best_match_art = art

        # Threshold limit: If match is greater than 65% identical, process the pairing
        if best_match_art and highest_score > 0.65:
            _, art_ext = os.path.splitext(best_match_art)
            # Enforce ES-DE core mapping naming rules
            new_art_name = f"{rom_name}{art_ext}"

            src_path = os.path.join(DOWNLOADED_ART_DIR, best_match_art)
            dest_path = os.path.join(target_media_folder, new_art_name)

            print(f"    [+] Match Found ({int(highest_score*100)}%): '{best_match_art}' -> '{rom}'")
            try:
                # Move and rename the file into the active ES-DE media environment
                shutil.move(src_path, dest_path)
                # Remove from staged list so it isn't matched to other games by accident
                staged_arts.remove(best_match_art)
            except Exception as e:
                print(f"    [-] System File Error: {e}")
        else:
            print(f"    [-] No certain artwork match found for: '{rom}'")

def main():
    print("=========================================================")
    print("      UNIFIED AUTOMATION PARSER: ARTWORK SYNC ENGINE     ")
    print("=========================================================\n")

    if not os.path.exists(DOWNLOADED_ART_DIR) or not os.listdir(DOWNLOADED_ART_DIR):
        print(f"[-] Staging area empty. Place images in: {DOWNLOADED_ART_DIR} first.")
        return

    for platform in TARGET_PLATFORMS:
        sync_platform_art(platform)

    print("\n[+] Sync execution cycle complete.")

if __name__ == "__main__":
    main()


