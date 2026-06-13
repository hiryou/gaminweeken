# Custom Theme Handoff

This file is the future-agent work context for implementing new ES-DE custom themes in this repo.

Use it when the user asks for a new theme from a provided set of static images, especially pet-photo-driven themes like `wakayave` and `dawnkaya`.

## Goal

Given:
- a base ES-DE theme to fork
- one or more user-provided image sets
- a desired visual direction

produce:
- a new theme folder
- preview assets for review
- optional Droid deployment as a separate theme

The expected workflow is:
1. concept and preview first
2. deploy only after the user approves
3. keep the custom theme separate from stock themes

## Previous Themes

Previously created themes are not currently stored live under `artifacts/themes/` in this repo.

Source-of-truth archives live here:

```text
~/Dropbox/gaming/retrogaming/retrodroid/themes/
```

Known archives:
- `wakayave.zip`
- `dawnkaya.zip`

If you need to inspect prior implementation details, unzip one of those into `tmp/` first, for example:

```bash
mkdir -p tmp/theme-inspect
unzip -q ~/Dropbox/gaming/retrogaming/retrodroid/themes/dawnkaya.zip -d tmp/theme-inspect
```

Those archives contain the actual `theme.xml`, `assets/kaya/`, `system/metadata-custom/`, and preview images from earlier work.

## Theme Structure Model

Custom themes here were implemented as forks of an existing ES-DE theme with selective overrides.

Typical layout inside a theme zip/folder:

```text
<theme-name>/
  theme.xml
  colors.xml
  capabilities.xml
  aspect-ratio-*.xml
  assets/
    kaya/
    images/
    fonts/
  system/
    metadata/
    metadata-custom/
    systemart/
```

What matters most for custom pet-photo themes:
- `theme.xml`
- `assets/kaya/*`
- `system/metadata-custom/*.xml`

## What Worked Well

Two successful directions were already built:

### `wakayave`
- brighter sticker-collage system view
- Hawaii postcard / surf / flower vibe
- strongest personality
- best for playful top-level carousel treatment

### `dawnkaya`
- darker, calmer mural direction
- console/system view and game-list view use related but distinct backgrounds
- lower-left Kaya placement worked well for game-list readability
- good fit when the user wants a premium, less cluttered look

## Default Design Rules

When making a new theme from static photos, follow these rules unless the user says otherwise:

1. Keep platform browsing readable.
- System logos / console art from the base theme must stay legible.
- Do not let the custom art overpower the central carousel.

2. Treat system view and game-list view separately.
- System view can be brighter / more decorative.
- Game-list view should be darker or softer for text readability.

3. Avoid pasted-photo look.
- If using a pet or person image inside a mural-style theme, the subject should feel integrated into the background, not just composited on top.

4. Keep deployments non-destructive.
- Always deploy as a new separate theme folder.
- Do not overwrite stock themes or existing custom themes unless the user explicitly asks.

5. Show previews before deploying.
- For new directions, provide 1–3 preview concepts first.
- Only push to the Droid after approval.

## Workflow

### Phase 1: Gather Inputs

Collect or confirm:
- base theme name
- local image set path
- desired vibe
- whether the user wants:
  - system view only first
  - or system + game-list views
- whether deployment should happen now or only after preview approval

Typical example:
- base theme: `LINEAR`
- images: `~/Downloads/<set-name>/*`
- vibe: “cartoonized pet, Hawaii, surf, flowers, beach sunrise”

### Phase 2: Build Preview Concepts

For a brand-new direction:
- generate 2–3 concept previews first
- each should show what the top-level system carousel might feel like

Preferred output:
- preview PNGs saved in the repo
- a short note describing what each concept is optimizing for

Do not start by modifying the Droid filesystem.

### Phase 3: Build the Theme Folder

Once a direction is chosen:
- create a new theme folder under `artifacts/themes/<theme-name>/` if the repo is being used as the staging area
- or unpack an older theme from Dropbox and branch from that if continuing an existing line

Recommended approach:
- fork from the exact working base theme version already known to render correctly on the Droid
- only override the parts you actually need

Be careful:
- if ES-DE theme assets are version-sensitive, forking from the exact installed base theme is safer than rebuilding from memory

### Phase 4: Implement System View

For system view:
- preserve the base theme’s console thumbnails / logos / layout
- replace or augment only the background layer(s)
- for bright collage themes, keep the center open enough for carousel readability
- for darker mural themes, match the same palette used in game-list backgrounds

### Phase 5: Implement Game-List View

For game-list view:
- background must not reduce text readability
- use darker / blurred / subdued backdrop treatment
- put the subject in a corner, usually lower-left worked best
- if using multiple variants, ensure adjacent systems do not feel repetitive

### Phase 6: Per-System Variation

If the user wants different subject images per platform:
- assign one variant per system
- avoid adjacent repeats in release-year-sorted systems if possible
- deterministic randomization is better than obvious round-robin repetition

Relevant prior script:
- [scripts/build_dawnkaya_variants.py](./scripts/build_dawnkaya_variants.py)

Use it as a pattern reference, not as a universal theme builder.
It is specific to the earlier `dawnkaya` implementation.

### Phase 7: Deploy

Only after user approval.

Recommended live deploy target:

```text
/sdcard/ES-DE/themes/<theme-name>
```

Typical deploy commands:

```bash
. config/droid-config.sh
adb -s "$DROID_ADB_SERIAL" push artifacts/themes/<theme-name>/. /sdcard/ES-DE/themes/<theme-name>/
adb -s "$DROID_ADB_SERIAL" shell am force-stop org.es_de.frontend
adb -s "$DROID_ADB_SERIAL" shell monkey -p org.es_de.frontend -c android.intent.category.LAUNCHER 1
```

If the user wants zero risk, stop before deployment and ask.

## Image Generation Guidance

### Skill Reference

The local reference copy of the image-generation skill is here:

- [agents/skills/imagegen/SKILL.md](./agents/skills/imagegen/SKILL.md)

Future agents should read that file before doing image-generation-heavy theme work.

### Preferred Path

Use the built-in image generation path first for:
- concept previews
- mural-style background generation
- stylistic reinterpretation of provided photos

Do not jump to CLI/API mode by default.

### When CLI Fallback Was Used

Earlier work also added a CLI fallback path for bulk image generation:
- [scripts/generate_dawnkaya_set3_cli.py](./scripts/generate_dawnkaya_set3_cli.py)

That script was built specifically for `dawnkaya` and `kaya-set3`.

Use it only as a reference for:
- how a batch image-gen pass was attempted
- how outputs and failures were logged

Do not assume it is the default path for future themes.

### Important Limitation

Earlier CLI attempts failed because the OpenAI API key hit:
- `billing_hard_limit_reached`

That was an API billing problem, not a theme logic problem.

So:
- built-in image generation remains the preferred default
- CLI fallback should only be used if explicitly needed and actually working

## Static Photo Sets

When the user provides a local image set:
- do not over-filter unless the user asks
- if they say “use all images”, use all images
- if some images include a companion dog or secondary subject and the user wants them kept, preserve that

If the user later says a pose/expression direction is wrong:
- treat that as a prompt/style correction, not just a random variation request
- explicitly preserve the desired emotional read:
  - goofy
  - happy
  - silly
  - relaxed
  - mildly blue only if still cute

## Common Failure Modes

### 1. Theme renders broken in ES-DE

Cause:
- theme fork does not match the exact base theme version

Fix:
- fork from the exact working theme source used by the installed ES-DE build

### 2. Subject looks like a pasted photo

Cause:
- raw compositing without enough style integration

Fix:
- regenerate with stronger style transfer / mural prompt
- or use a background-generation path that integrates the subject natively

### 3. Subject looks sad / generic

Cause:
- image generation drift

Fix:
- swap to a better source image set
- make prompt explicitly preserve goofy / happy / silly expression

### 4. Repetition across systems feels obvious

Cause:
- simple round-robin assignment

Fix:
- use deterministic randomized assignment with adjacency checks

## Recommended Future Procedure

If asked to make a new theme from static pics, do this:

1. Read this file.
2. Read the copied imagegen skill:
   - [agents/skills/imagegen/SKILL.md](./agents/skills/imagegen/SKILL.md)
3. Inspect prior theme archives under:
   - `~/Dropbox/gaming/retrogaming/retrodroid/themes/`
4. Generate 2–3 concept previews first.
5. Get approval.
6. Build the theme as a separate folder.
7. Deploy only after confirming with the user that pushing to the Droid will not break anything they care about.

## Current Repo Pointers

Useful files:
- [config/droid-config.sh](./config/droid-config.sh)
- [scripts/build_dawnkaya_variants.py](./scripts/build_dawnkaya_variants.py)
- [scripts/generate_dawnkaya_set3_cli.py](./scripts/generate_dawnkaya_set3_cli.py)
- [README.md](./README.md)

Useful external source of truth:
- `~/Dropbox/gaming/retrogaming/retrodroid/themes/`
