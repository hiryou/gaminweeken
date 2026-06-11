#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SET3_DIR = Path("/Users/longn/Downloads/kaya-set3")
DEFAULT_STYLE_REF = Path(
    "/Users/longn/.codex/generated_images/019eb0ec-3d10-7281-a61c-9159e2a2a99c/ig_01402a8c88aa2731016a2c9eb0a6a081999c5c0b48b04cb945.png"
)
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts/themes/dawnkaya/assets/kaya/gamelist-ai-variants-set3-cli"
DEFAULT_REPORT = REPO_ROOT / "tmp/dawnkaya-set3-cli-report.json"


PROMPT = """Use Image 1 as the identity-and-pose reference for Kaya.
Use Image 2 only as the style, palette, rendering, and composition reference.

Create a 16:9 mural-style Hawaii dawn background for an ES-DE game-list screen.
The result should match the same moody tropical sunrise mural look as Image 2:
dark blue and amber dawn palette, ocean wave, beach sand, distant mountains,
surf boards, flowers, palm foliage silhouettes, painterly textured mural finish,
soft contrast, calm early-morning atmosphere.

Keep Kaya in the lower-left quarter only, occupying about 20 to 25 percent of the canvas.
Retain Kaya's real face, expression, and overall pose from Image 1, including goofy,
happy, funny, silly, or companion-dog energy when present. Do not make Kaya sad,
solemn, blank, or generic. If a companion dog is present in Image 1, keep that companion
in the mural naturally as well.

Important:
- Kaya and any companion must be naturally integrated into the mural, not pasted photo cutouts.
- Stylize them into the same painterly mural language as Image 2.
- Leave the center and right side open and darker for readable game-list text overlays.
- No text, no logos, no UI, no watermark.
"""


@dataclass
class AttemptResult:
    source: str
    output: str
    ok: bool
    returncode: int
    stderr: str
    stdout: str
    command: List[str]


def iter_images(directory: Path) -> List[Path]:
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    return sorted(
        p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in exts and not p.name.startswith(".")
    )


def build_command(image_gen: Path, source: Path, style_ref: Path, output: Path, quality: str, size: str) -> List[str]:
    return [
        sys.executable,
        str(image_gen),
        "edit",
        "--image",
        str(source),
        "--image",
        str(style_ref),
        "--prompt",
        PROMPT,
        "--use-case",
        "stylized-concept",
        "--scene",
        "Hawaii dawn beach mural with ocean wave, surf boards, flowers, palms, and mountains",
        "--subject",
        "Kaya as a painterly mural character integrated into the beach scene",
        "--style",
        "textured hand-painted tropical mural, matching the exact mood and finish of Image 2",
        "--composition",
        "16:9 wide mural, Kaya in lower-left only, center and right open for overlay text",
        "--lighting",
        "moody sunrise glow, dark readable center-right, soft painterly contrast",
        "--constraints",
        "preserve Kaya's real expression and pose from Image 1; keep goofy happy silly energy; no sad expression; no pasted photo look; no text; no watermark",
        "--quality",
        quality,
        "--size",
        size,
        "--out",
        str(output),
        "--force",
    ]


def run_attempt(cmd: List[str], source: Path, output: Path) -> AttemptResult:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return AttemptResult(
        source=str(source),
        output=str(output),
        ok=proc.returncode == 0,
        returncode=proc.returncode,
        stderr=proc.stderr,
        stdout=proc.stdout,
        command=cmd,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate dawnkaya set3 mural variants via image_gen.py CLI")
    parser.add_argument("--set3-dir", type=Path, default=DEFAULT_SET3_DIR)
    parser.add_argument("--style-ref", type=Path, default=DEFAULT_STYLE_REF)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--quality", default="high")
    parser.add_argument("--size", default="2048x1152")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    image_gen_env = os.environ.get("IMAGE_GEN")
    image_gen = Path(image_gen_env).expanduser() if image_gen_env else None
    if image_gen is None:
        codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
        image_gen = codex_home / "skills/.system/imagegen/scripts/image_gen.py"

    if not image_gen.exists():
        raise SystemExit(f"image_gen.py not found: {image_gen}")
    if not args.set3_dir.exists():
        raise SystemExit(f"set3 dir not found: {args.set3_dir}")
    if not args.style_ref.exists():
        raise SystemExit(f"style ref not found: {args.style_ref}")

    images = iter_images(args.set3_dir)
    if args.limit is not None:
        images = images[: args.limit]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    results: List[AttemptResult] = []

    for idx, source in enumerate(images, start=1):
        output = args.out_dir / f"kaya-set3-cli-{idx:02d}.png"
        cmd = build_command(image_gen, source, args.style_ref, output, args.quality, args.size)
        print(f"[{idx}/{len(images)}] {source.name}", flush=True)
        result = run_attempt(cmd, source, output)
        results.append(result)
        if result.ok:
            print(f"  ok -> {output.name}", flush=True)
        else:
            print(f"  failed ({result.returncode})", flush=True)

    payload = {
        "style_ref": str(args.style_ref),
        "set3_dir": str(args.set3_dir),
        "out_dir": str(args.out_dir),
        "results": [
            {
                "source": r.source,
                "output": r.output,
                "ok": r.ok,
                "returncode": r.returncode,
                "stderr": r.stderr,
                "stdout": r.stdout,
                "command": " ".join(shlex.quote(part) for part in r.command),
            }
            for r in results
        ],
    }
    args.report.write_text(json.dumps(payload, indent=2))

    ok_count = sum(1 for r in results if r.ok)
    fail_count = len(results) - ok_count
    print(f"Completed: {ok_count} succeeded, {fail_count} failed. Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
