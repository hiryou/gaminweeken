"""
This modular initialization script connects to official endpoints, parses their JSON APIs to find the latest valid
public architectures, and downloads the binary Android application installers directly into a localized folder.
"""

import os
import requests

# CONFIGURATION ARCHITECTURE
DOWNLOAD_DIR = "/storage/emulated/0/RetroGames/installers/"
EMULATOR_REGISTRY = {
    "retroarch": {
        "name": "RetroArch 64-bit Core",
        "source_type": "direct_url",
        "url": "https://libretro.com"
    },
    # --------------------------------------------------------------------------
    # NETHER_SX2 EMULATOR CONFIGURATION PROFILE (COMMENTED OUT)
    # --------------------------------------------------------------------------
    # "ps2_nethersx2": {
    #     "name": "NetherSX2 (PS2 Engine)",
    #     "source_type": "github_latest",
    #     "repo": "Trixer619/NetherSX2-patch"
    # },
    # --------------------------------------------------------------------------
    "ps2_aethersx2": {
        "name": "AetherSX2 v1.5-3668 (Peak Performance / Ad-Free Build)",
        "source_type": "direct_url",
        "url": "https://githubusercontent.com"
    },
    # --------------------------------------------------------------------------
    # LEGACY 3DS ENGINE REFERENCE BLOCK (PRESERVED)
    # --------------------------------------------------------------------------
    # "3ds_citra_legacy": {
    #     "name": "Citra 3DS Custom Fork (Legacy Build)",
    #     "source_type": "github_latest",
    #     "repo": "PabloMK7/citra"
    # },
    # --------------------------------------------------------------------------
    "3ds_azahar_plus": {
        "name": "Azahar Plus (Premium 3DS Engine - Citra Successor)",
        "source_type": "github_latest",
        "repo": "AzaharPlus/AzaharPlus"
    },
    # --------------------------------------------------------------------------
    # DUAL NINTENDO SWITCH ENGINE LAYOUT
    # --------------------------------------------------------------------------
    "switch_sudachi": {
        "name": "Sudachi Switch Emulator (High Compatibility & Stability Base)",
        "source_type": "github_latest",
        "repo": "sudachi-emu/sudachi"
    },
    "switch_citron_neo": {
        "name": "Citron Neo Switch Emulator (Vulkan & Thread Speed Performance Engine)",
        "source_type": "github_latest",
        "repo": "citron-neo/emulator"
    },
    # --------------------------------------------------------------------------
    # GAMECUBE & WII ENGINE ARCHITECTURE (OFFICIAL DEV ENDPOINT)
    # --------------------------------------------------------------------------
    "gamecube_dolphin": {
        "name": "Dolphin GameCube/Wii Development Branch (Official)",
        "source_type": "direct_url",
        "url": "https://dolphin-emu.org"  # Dynamically pulls latest master compilation
    },
    # --------------------------------------------------------------------------
    # NINTENDO 64 ENGINE ARCHITECTURE
    # --------------------------------------------------------------------------
    "n64_m64plus_fz": {
        "name": "M64Plus FZ Emulator (N64 Standalone Powerhouse)",
        "source_type": "github_latest",
        "repo": "fzurita/mupen64plus-ae"
    }
}

def resolve_github_asset(repo_path):
    """Queries the Github API to safely track down the latest working standalone APK payload."""
    api_url = f"https://github.com{repo_path}/releases/latest"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for asset in data.get("assets", []):
                if asset["name"].endswith(".apk"):
                    return asset["browser_download_url"], asset["name"]
    except Exception as e:
        print(f"[-] API Handshake Interrupted for {repo_path}: {e}")
    return None, None

def download_binary(url, filename):
    """Executes a streamlined chunk-based binary file download to target filesystem destination."""
    dest_path = os.path.join(DOWNLOAD_DIR, filename)
    print(f"[*] Stream Initialization: {filename}...")
    try:
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"[+] Operational Success: Saved to {dest_path}")
    except Exception as e:
        print(f"[-] Download Execution Aborted for {filename}: {e}")

def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print("=========================================================")
    print("    ORANGE PI 5 CONSOLE APPLIANCE: INITIAL BOOTSTRAP     ")
    print("=========================================================\n")

    for emu_id, config in EMULATOR_REGISTRY.items():
        print(f"[#] Processing Entry: {config['name']}")

        if config["source_type"] == "direct_url":
            filename = f"{emu_id}_latest.apk"
            download_binary(config["url"], filename)

        elif config["source_type"] == "github_latest":
            dl_url, asset_name = resolve_github_asset(config["repo"])
            if dl_url:
                download_binary(dl_url, asset_name)
            else:
                print(f"[-] Critical Error: No matching standalone APK file found in github.com/{config['repo']}")
        print("-" * 50)

if __name__ == "__main__":
    main()






