# Dawnkaya CLI Handoff

## Goal

Resume `dawnkaya` theme work for ES-DE on the Orange Pi Droid.

Current target:
- keep the approved console-view mural background
- regenerate the per-console game-list backgrounds from `~/Downloads/kaya-set3/*`
- use the same mural style as the approved background
- use the OpenAI CLI/API fallback path
- best-effort iteration: if one image fails, skip it and continue

## Current theme state

Active live theme on the Droid:
- `/sdcard/ES-DE/themes/dawnkaya`

Repo theme folder:
- [artifacts/themes/dawnkaya](./artifacts/themes/dawnkaya)

ES-DE is currently configured to use `dawnkaya`.

## What is already fixed

The console/platform-view background is now correct and uses the user-approved mural:
- source approved image:
  - `/Users/longn/.codex/generated_images/019eb0ec-3d10-7281-a61c-9159e2a2a99c/ig_01402a8c88aa2731016a2c9eb0a6a081999c5c0b48b04cb945.png`
- copied into theme as:
  - [artifacts/themes/dawnkaya/assets/kaya/system-bg-kaya-wave-mural-v4.png](./artifacts/themes/dawnkaya/assets/kaya/system-bg-kaya-wave-mural-v4.png)

`theme.xml` already points the system view at that image:
- [artifacts/themes/dawnkaya/theme.xml](./artifacts/themes/dawnkaya/theme.xml)

Do not replace that console-view background unless explicitly requested.

## What is still wrong

The per-console game-list mural pool generated from `kaya-set3` is still wrong.

The user explicitly wants:
- Kaya silhouette extracted out of each source image
- Kaya restyled/cartoonized into the same mural language as the approved background
- same general dawn Hawaii palette/vibe
- not photo-cutout looking
- not sad-looking
- include companion-dog photos too
- use all images from `kaya-set3`

## Source image set

Use all files under:
- `/Users/longn/Downloads/kaya-set3`

The user explicitly said not to filter the set.

## Relevant scripts and files

### Added for CLI fallback

Main batch driver:
- [scripts/generate_dawnkaya_set3_cli.py](./scripts/generate_dawnkaya_set3_cli.py)

This script:
- iterates over all `kaya-set3` images
- uses the approved mural as the style reference
- sends one independent `image_gen.py edit` request per source image
- writes outputs to:
  - `artifacts/themes/dawnkaya/assets/kaya/gamelist-ai-variants-set3-cli/`
- logs success/failure to:
  - [tmp/dawnkaya-set3-cli-report.json](./tmp/dawnkaya-set3-cli-report.json)

### Existing theme assignment script

- [scripts/build_dawnkaya_variants.py](./scripts/build_dawnkaya_variants.py)

This handles assignment of mural files across active systems after a good pool exists.

### Active systems file

- [tmp/dawnkaya-active-systems.txt](./tmp/dawnkaya-active-systems.txt)

## Python env created for this work

Dedicated env:
- `.venv-imagegen/`

Installed:
- `openai`
- `pillow`

Use this interpreter for the CLI pass:

```bash
.venv-imagegen/bin/python scripts/generate_dawnkaya_set3_cli.py
```

## OpenAI CLI/image generation path

The repo uses the bundled skill CLI:
- `/Users/longn/.codex/skills/.system/imagegen/scripts/image_gen.py`

The batch driver uses the `edit` subcommand with:
- Image 1 = a `kaya-set3` source photo
- Image 2 = the approved mural style reference

The prompt is embedded in:
- [scripts/generate_dawnkaya_set3_cli.py](./scripts/generate_dawnkaya_set3_cli.py)

## Current blocker

Actual image generation is currently blocked by OpenAI API billing for the API key in `OPENAI_API_KEY`.

Observed error:

```text
openai.BadRequestError: Error code: 400 - {
  'error': {
    'message': 'Billing hard limit has been reached.',
    'type': 'billing_limit_user_error',
    'code': 'billing_hard_limit_reached'
  }
}
```

Important:
- this is from the official OpenAI API
- not from a third-party tool
- not from ChatGPT web/app credits
- ChatGPT subscription/credits and API billing are separate

## Verified retry status

Retried after setup:
- `IMG-20230131-WA0000.jpg` -> failed with `billing_hard_limit_reached`
- `IMG-20230204-WA0000.jpg` -> failed with `billing_hard_limit_reached`

Current report file:
- [tmp/dawnkaya-set3-cli-report.json](./tmp/dawnkaya-set3-cli-report.json)

## Exact commands used

Create env and deps:

```bash
python3 -m venv .venv-imagegen
.venv-imagegen/bin/pip install openai pillow
```

Single-image probe:

```bash
.venv-imagegen/bin/python scripts/generate_dawnkaya_set3_cli.py --limit 1
```

Two-image probe:

```bash
.venv-imagegen/bin/python scripts/generate_dawnkaya_set3_cli.py --limit 2
```

Full intended run after billing is fixed:

```bash
.venv-imagegen/bin/python scripts/generate_dawnkaya_set3_cli.py
```

## Recommended next steps after API billing is fixed

1. Re-run the full CLI pass:

```bash
.venv-imagegen/bin/python scripts/generate_dawnkaya_set3_cli.py
```

2. Review outputs in:

- `artifacts/themes/dawnkaya/assets/kaya/gamelist-ai-variants-set3-cli/`

3. Keep only the good mural images and rename/copy them into the active pool:

- `artifacts/themes/dawnkaya/assets/kaya/gamelist-ai-variants/`

4. Rebuild assignments:

```bash
python3 scripts/build_dawnkaya_variants.py --systems-file tmp/dawnkaya-active-systems.txt
```

5. Redeploy theme to Droid:

```bash
adb -s 192.168.0.99:5555 push artifacts/themes/dawnkaya/. /sdcard/ES-DE/themes/dawnkaya/
```

6. Restart ES-DE:

```bash
adb -s 192.168.0.99:5555 shell am force-stop org.es_de.frontend
adb -s 192.168.0.99:5555 shell monkey -p org.es_de.frontend -c android.intent.category.LAUNCHER 1
```

## Access details known-good

SSH:

```bash
ssh -p 8022 u0_a77@192.168.0.99
```

ADB:

```bash
adb devices
# expected:
# 192.168.0.99:5555    device
```

## Constraint to preserve

Do not regress the current console/platform-view background.

Only the game-list mural pool should be regenerated next unless the user asks otherwise.
