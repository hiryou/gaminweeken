# Neo Platforms Handoff

## Scope

This handoff covers the Neo Geo / FBNeo / Neo Geo CD issues investigated on the Droid on 2026-06-21.

## Device Context

- Device: `orangepi5`
- Android board/platform: `rk3588`
- RetroArch package: `com.retroarch.aarch64`
- ES-DE package: `org.es_de.frontend`

## 1. FBNeo "Romset is unknown"

### What happened

Some games placed under `ROMs/fbneo/` launched with:

- `FBNeo Error: Romset is unknown`

### Root cause

FBNeo does not use human-friendly game names. It identifies games by canonical internal romset shortnames.

This is not about spaces in file paths.

Examples:

- good canonical name: `mslug3.zip`
- wrong friendly names:
  - `Metal Slug 3.zip`
  - `Metal Slug 3 (NGM-2560).zip`

### Concrete findings

On device, logcat showed launches like:

- `Auto-start game "/storage/emulated/0/RetroGames/ROMs/fbneo/Metal Slug 2 Turbo.zip"`
- `Auto-start game "/storage/emulated/0/RetroGames/ROMs/fbneo/Metal Slug 3.zip"`
- `Auto-start game "/storage/emulated/0/RetroGames/ROMs/fbneo/Metal Slug 3 (NGM-2560).zip"`

Current folder state found during investigation:

- `/storage/emulated/0/RetroGames/ROMs/fbneo/dino.zip`
- `/storage/emulated/0/RetroGames/ROMs/fbneo/neogeo.zip`
- `/storage/emulated/0/RetroGames/ROMs/fbneo/Metal Slug 3 (NGM-2560).zip`

Host-side candidate also exists:

- `/Users/longn/Downloads/retrogaming/roms/neogeo/mslug3.zip`

This host file is the strongest candidate because the filename matches the expected FBNeo shortname.

### Additional finding for `dino.zip`

`dino.zip` contents were listed and looked plausible, but `qsound.zip` was not present in `ROMs/fbneo/`.

Likely issue for `dino.zip`:

- missing dependency set `qsound.zip`

### Practical rule

For FBNeo:

- use proper arcade romsets
- use canonical short filenames
- keep required BIOS/dependency zips next to them

Examples:

- Neo Geo arcade: `neogeo.zip`
- CPS2/QSound titles: may need `qsound.zip`

### Extra evidence from Reddit thread

Useful external confirmation:

- Reddit thread: https://www.reddit.com/r/RetroArch/comments/15mnvvr/fbneo_not_working_with_romset_is_unknown/

Actionable point from that thread:

- if you rename an arcade romset, FBNeo can stop recognizing it entirely
- example given there:
  - renaming `sfiii.zip` to a prettier title broke detection
  - restoring the exact shortname fixed it

This directly supports the current conclusion that the unknown-romset issue is about exact canonical romset IDs, not spaces in paths and not frontend naming.

## 2. Neo Geo vs Neo Geo AES vs FBNeo

### Clarification

- `Neo Geo` is the hardware family
- `AES` is the home console variant
- `FBNeo` is an emulator/core, not a later console

### Practical conclusion

If the goal is to run games through FBNeo, place compatible romsets under:

- `ROMs/fbneo/`

It is fine for Neo Geo MVS and compatible arcade-style Neo Geo content to live there if FBNeo is the chosen emulator.

What matters is romset compatibility, not the marketing label on the website.

## 3. Metal Slug 3 source issue

### What happened

User linked:

- `https://romsfun.com/roms/neo-geo-aes/metal-slug-3-6.html`

### Conclusion

That page is the wrong source for the current FBNeo setup.

Reason:

- FBNeo expects the arcade/MVS romset `mslug3.zip`
- the linked page is an AES/home-console source

So the current fix direction is:

- do not use that AES download for FBNeo
- use a proper FBNeo/MAME-compatible `mslug3.zip` arcade romset

## 4. Neo Geo CD black screen

### Initial mistake

I first copied the BIOS to:

- `/storage/emulated/0/Android/data/com.retroarch.aarch64/files/system/neocd.bin`

That was wrong for the NeoCD core.

### Correct BIOS path

The NeoCD libretro core expects BIOS files under:

- `/storage/emulated/0/Android/data/com.retroarch.aarch64/files/system/neocd/`

Current correct file on device:

- `/storage/emulated/0/Android/data/com.retroarch.aarch64/files/system/neocd/neocd.bin`

Current verified hash:

- `f39572af7584cb5b3f70ae8cc848aba2`

The wrong flat copy under `system/` was removed.

### Extra evidence from Reddit thread

Useful external confirmation:

- Reddit thread: https://www.reddit.com/r/retroid/comments/1e61j8o/help_with_neogeo_cd_retroarch/

Actionable points from that thread:

- for the `NeoCD` RetroArch core, BIOS belongs in:
  - `RetroArch/system/neocd/`
- games for that core can be `bin/cue` or `chd`
- RetroArch can confirm whether firmware is seen at:
  - `Settings -> Core -> Manage Core -> Select Core -> Firmware`

This thread also distinguishes the two RetroArch approaches:

- `NeoCD` core:
  - BIOS under `system/neocd/`
- `FBNeo` running Neo Geo CD:
  - BIOS under `system/fbneo/` as `neocdz.zip`
  - games in a `neocd/` folder
  - thread specifically mentions `bin/cue` for the FBNeo Neo Geo CD path

That distinction matters because the current testing mixed general Neo Geo BIOS assumptions with Neo Geo CD-specific requirements.

### Automation fix already made

Repo file updated:

- `scripts/bootstrap_retroarch_cores.py`

It now seeds:

- host source: `~/Downloads/retrogaming/_emulator-files/neogeocd/neocd.bin`
- device target: `.../files/system/neocd/neocd.bin`

No `adb root` was needed.

### Current remaining Neo Geo CD issue

Even after fixing BIOS path, Neo Geo CD still black-screened.

Logcat showed:

- `Libretro path: "/data/user/0/com.retroarch.aarch64/cores/neocd_libretro_android.so"`
- `Auto-start game "/storage/emulated/0/RetroGames/ROMs/neogeocd/Metal Slug (Japan) (EnJa).chd"`

Current `ROMs/neogeocd/` contents on device:

- `systeminfo.txt`
- `neogeo.zip`
- `Metal Slug (Japan) (EnJa).chd`

### Conclusion

The next problem is content layout, not BIOS.

Current set is missing a proper launcher/companion file, most likely:

- `.cue`

So right now the game is being launched as a lone `.chd`, which is likely not enough for this core/setup.

One more thing worth checking in RetroArch before deeper debugging:

- `Settings -> Core -> Manage Core -> NeoCD -> Firmware`

That should confirm whether RetroArch now sees the NeoCD BIOS after the path fix.

## 5. Process actions already done

- RetroArch was force-stopped multiple times during investigation
- ES-DE was restarted when requested
- NeoCD BIOS was copied into the correct `system/neocd/` path
- RetroArch setup automation was patched to keep doing this in future

## 6. Recommended next steps

### FBNeo

1. Replace friendly-named Neo Geo zips with proper FBNeo shortname romsets.
2. Test host-side `mslug3.zip` from:
   - `/Users/longn/Downloads/retrogaming/roms/neogeo/mslug3.zip`
3. Add `qsound.zip` if testing `dino.zip`.

### Neo Geo CD

1. Replace lone `.chd` content with a proper Neo Geo CD set.
2. Look for the expected `.cue` companion file or proper NeoCD package layout for the game.
3. Re-test after the content layout is corrected.

## 7. Key paths

Host:

- `/Users/longn/Downloads/retrogaming/roms/fbneo`
- `/Users/longn/Downloads/retrogaming/roms/neogeo`
- `/Users/longn/Downloads/retrogaming/roms/neogeocd`
- `/Users/longn/Downloads/retrogaming/_emulator-files/neogeocd/neocd.bin`

Device:

- `/storage/emulated/0/RetroGames/ROMs/fbneo`
- `/storage/emulated/0/RetroGames/ROMs/neogeo`
- `/storage/emulated/0/RetroGames/ROMs/neogeocd`
- `/storage/emulated/0/Android/data/com.retroarch.aarch64/files/system/neocd/neocd.bin`
