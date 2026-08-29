#!/usr/bin/env python3
"""Compose generated text patches while preserving source pixels elsewhere."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image


def alpha_at(px: int, py: int, box: tuple[int, int, int, int], feather: int) -> float:
    x, y, width, height = box
    x2, y2 = x + width, y + height
    dx = x - px if px < x else px - x2 + 1 if px >= x2 else 0
    dy = y - py if py < y else py - y2 + 1 if py >= y2 else 0
    distance = math.hypot(dx, dy)
    if distance <= 0:
        return 1.0
    if feather <= 0 or distance >= feather:
        return 0.0
    return 0.5 + 0.5 * math.cos(math.pi * distance / feather)


def compose(job: dict, default_feather: int) -> dict:
    source_path = Path(job["source"]).expanduser().resolve()
    generated_path = Path(job["generated"]).expanduser().resolve()
    output_path = Path(job["output"]).expanduser().resolve()
    region = job["box"]
    box = (int(region["x"]), int(region["y"]), int(region["width"]), int(region["height"]))
    feather = int(job.get("feather", default_feather))

    with Image.open(source_path) as source_image:
        source = source_image.convert("RGB")
    with Image.open(generated_path) as generated_image:
        generated = generated_image.convert("RGB").resize(source.size, Image.Resampling.LANCZOS)

    width, height = source.size
    x, y, region_width, region_height = box
    if region_width <= 0 or region_height <= 0 or x < 0 or y < 0 or x + region_width > width or y + region_height > height:
        raise ValueError(f"Invalid box for {source_path}: {box} within {source.size}")

    source_pixels = source.load()
    generated_pixels = generated.load()
    result = source.copy()
    result_pixels = result.load()

    left = max(0, x - feather)
    top = max(0, y - feather)
    right = min(width, x + region_width + feather)
    bottom = min(height, y + region_height + feather)
    for py in range(top, bottom):
        for px in range(left, right):
            alpha = alpha_at(px, py, box, feather)
            if alpha == 0:
                continue
            base = source_pixels[px, py]
            edit = generated_pixels[px, py]
            result_pixels[px, py] = tuple(round(edit[channel] * alpha + base[channel] * (1 - alpha)) for channel in range(3))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path, format="PNG", optimize=True)

    with Image.open(output_path) as verified_image:
        if verified_image.mode != "RGB":
            raise ValueError(f"Output must be opaque RGB: {output_path} is {verified_image.mode}")
        verified = verified_image.load()
        changed_outside = 0
        for py in range(height):
            for px in range(width):
                if left <= px < right and top <= py < bottom:
                    continue
                if verified[px, py] != source_pixels[px, py]:
                    changed_outside += 1
        if changed_outside:
            raise ValueError(f"{output_path}: {changed_outside} pixels changed outside the allowed region")

    return {
        "output": str(output_path),
        "width": width,
        "height": height,
        "mode": "RGB",
        "outsideRegionChangedPixels": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    default_feather = int(manifest.get("feather", 32))
    jobs = manifest.get("jobs", [])
    if not jobs:
        raise ValueError("Manifest must contain at least one job")
    results = [compose(job, default_feather) for job in jobs]
    print(json.dumps({"ok": True, "count": len(results), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
