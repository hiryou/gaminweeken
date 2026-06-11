# ES-DE Frontend Mapping Reference

This document is the exact ES-DE routing plan for this repo's Android/Droid setup on Orange Pi 5.

The goal is simple:
- use `RetroArch` for older systems where a libretro core is fine
- use standalone emulators for heavier systems where Android-native apps perform better

## The Decision Layers

There are two separate routing layers, and mixing them up is what makes this feel confusing.

1. `ES-DE`
   Chooses which emulator application should launch for a system or a specific game.
2. `RetroArch`
   If ES-DE launches RetroArch, RetroArch then needs a matching libretro core installed.

So:
- `ES-DE` does not install cores
- `RetroArch` does not decide your ES-DE system routing
- if `nes` is mapped to a RetroArch option in ES-DE, then RetroArch still needs an NES core installed

## Install and First Launch

1. Obtain the paid Android `ES-DE` APK from the official distribution channel you use.
2. Place that APK directly under:
   ```text
   artifacts/apks/
   ```
3. Install it onto the Droid with the normal host pipeline:
   ```bash
   ./setup_droid.sh <ssh_target> [adb_serial]
   ```
   ES-DE will be detected and installed after the emulator APKs.
4. Launch ES-DE once so it can create its working folders.
5. When prompted, point ES-DE at the ROM root:
   `/storage/emulated/0/RetroGames/roms/`
6. After the first scan completes, open:
   `Start -> Alternative Emulators`

## Global Mapping Table

Use these default mappings in ES-DE.

| ES-DE system | ROM folder | Default emulator | Notes |
| --- | --- | --- | --- |
| `nes` | `/storage/emulated/0/RetroGames/roms/nes/` | `RetroArch` | Use the ES-DE default RetroArch path. |
| `snes` | `/storage/emulated/0/RetroGames/roms/snes/` | `RetroArch` | Use the ES-DE default RetroArch path. |
| `genesis` | `/storage/emulated/0/RetroGames/roms/genesis/` | `RetroArch` | Use the ES-DE default RetroArch path. |
| `dreamcast` | `/storage/emulated/0/RetroGames/roms/dreamcast/` | `RetroArch` | Use the ES-DE default RetroArch path. |
| `ps1` | `/storage/emulated/0/RetroGames/roms/ps1/` | `RetroArch` | Use the ES-DE default RetroArch path. |
| `n64` | `/storage/emulated/0/RetroGames/roms/n64/` | `Mupen64Plus AE (Standalone)` | Preferred over a RetroArch N64 core. |
| `gc` | `/storage/emulated/0/RetroGames/roms/gc/` | `Dolphin (Standalone)` | Preferred for GameCube. |
| `wii` | `/storage/emulated/0/RetroGames/roms/wii/` | `Dolphin (Standalone)` | Create this folder manually if you want Wii titles. |
| `3ds` | `/storage/emulated/0/RetroGames/roms/3ds/` | `Azahar Plus (Standalone)` | If ES-DE exposes `Citra` instead and that is what you installed, use that. |
| `ps2` | `/storage/emulated/0/RetroGames/roms/ps2/` | `AetherSX2 (Standalone)` | Use the standalone PS2 app. |
| `switch` | `/storage/emulated/0/RetroGames/roms/switch/` | `Citron (Standalone)` | Recommended default if both Citron and Sudachi are installed. |

## RetroArch Systems

For systems you keep on RetroArch, there are two things to configure:

1. ES-DE must route the system to a RetroArch-backed emulator choice.
2. RetroArch must already have the matching core installed.

Current recommended starting point:

| System | ES-DE target | RetroArch requirement |
| --- | --- | --- |
| `nes` | `RetroArch::FCEUmm` | `fceumm_libretro_android.so` must be installed |
| `snes` | `RetroArch::Snes9x` | `snes9x_libretro_android.so` must be installed |
| `genesis` | `RetroArch::Genesis Plus GX` | `genesis_plus_gx_libretro_android.so` must be installed |
| `ps1` | `RetroArch::SwanStation` | `swanstation_libretro_android.so` must be installed |
| `dreamcast` | `RetroArch::Flycast` | `flycast_libretro_android.so` must be installed |

This repo now includes a host script to install that baseline RetroArch core set:

```bash
./setup_retroarch.sh
```
This installs the core `.so` and `.info` files into RetroArch's shared writable storage.
After running it, open RetroArch once and use `Load Core` for each system you plan to launch
from ES-DE.

And a separate host script to check for BIOS / firmware files still needed by the
RetroArch-backed systems that commonly require them:

```bash
./check_retroarch_bios.sh
```

If you have multiple adb devices connected:

```bash
./setup_retroarch.sh --serial 192.168.0.99:5555
```

## Alternate Emulator Cases

These systems may reasonably have more than one installed emulator.

| System | Preferred default | Alternate choice | When to switch |
| --- | --- | --- | --- |
| `switch` | `Citron (Standalone)` | `Sudachi (Standalone)` | Try Sudachi for a specific title if Citron has compatibility problems. |
| `3ds` | `Azahar Plus (Standalone)` | `Citra (Standalone)` | Only if you installed Citra separately and prefer it for a specific game. |
| `ps2` | `AetherSX2 (Standalone)` | `NetherSX2 (Standalone)` | Only if you choose to install NetherSX2 later. |

## Exact Menu Sequence in ES-DE

Repeat this for each heavy system:

1. Open `ES-DE`.
2. Press `Start`.
3. Open `Alternative Emulators`.
4. Select the target system:
   `n64`, `gc`, `wii`, `3ds`, `ps2`, or `switch`
5. Change the selected emulator from the RetroArch default to the standalone app listed above.

For `nes`, the important point is different:

1. Open `ES-DE`
2. Press `Start`
3. Open `Alternative Emulators`
4. Select `nes`
5. Choose the RetroArch entry that corresponds to the installed NES core
   For this repo's current bootstrap script, that is `RetroArch::FCEUmm`

For the other RetroArch-routed systems, use these ES-DE targets:

- `snes` -> `RetroArch::Snes9x`
- `genesis` -> `RetroArch::Genesis Plus GX`
- `ps1` -> `RetroArch::SwanStation`
- `dreamcast` -> `RetroArch::Flycast`

## BIOS / Firmware Notes

For the current RetroArch core set:

- `nes` / `snes` / `genesis` do not need BIOS files for the chosen cores
- `ps1` with `SwanStation` should have a PS1 BIOS under `/sdcard/RetroArch/system/`
- `dreamcast` with `Flycast` should have `dc_boot.bin` and `dc_flash.bin` under `/sdcard/RetroArch/system/`

Use the host-side checker to validate what is missing:

```bash
./check_retroarch_bios.sh
```

## Per-Game Overrides

If one game needs a different emulator than the global default:

1. Highlight the game in ES-DE.
2. Hold the confirm/select button for about 2 seconds.
3. Open `Advanced Game Options`.
4. Change `Alternative Emulator` for that game only.

This is the intended place to switch:
- a single Switch game from `Citron` to `Sudachi`
- a single N64 title to a different profile path
- a single 3DS title to a different installed emulator

## ROM Folder Notes

The current setup scripts create these ROM folders automatically:

- `nes`
- `snes`
- `genesis`
- `dreamcast`
- `ps1`
- `gc`
- `3ds`
- `ps2`
- `n64`

If you want ES-DE entries for `switch` or `wii`, create those folders manually:

```bash
mkdir -p /storage/emulated/0/RetroGames/roms/switch
mkdir -p /storage/emulated/0/RetroGames/roms/wii
```

## Artwork Paths

ES-DE artwork lands under:

```text
/storage/emulated/0/ES-DE/downloaded_media/
```

This repo's art-management helpers are built around that path. See:
- [README.md](./README.md)
- [emulators-docs.md](./emulators-docs.md)
