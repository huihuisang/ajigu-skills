#!/usr/bin/env python3
"""Render exact localized copy onto a prepared screenshot master."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    return parser.parse_args()


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def render_block(draw: ImageDraw.ImageDraw, block: dict, locale: str) -> None:
    font_size = int(block["font_size"])
    min_font_size = int(block.get("min_font_size", font_size))
    max_width = int(block["max_width"])
    font_path = block["font"]
    font_index = int(block.get("font_index", 0))
    lines = block["lines"]

    while font_size >= min_font_size:
        font = ImageFont.truetype(font_path, font_size, index=font_index)
        if max(text_width(draw, line, font) for line in lines) <= max_width:
            break
        font_size -= 1
    else:
        raise ValueError(f"Copy does not fit for {locale}")

    x, y = block["origin"]
    line_gap = int(block.get("line_gap", 18))
    fill = tuple(block.get("fill", [255, 255, 255]))
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        box = draw.textbbox((x, y), line, font=font)
        y = box[3] + line_gap


def render_item(item: dict) -> None:
    source = Path(item["source"])
    output = Path(item["output"])
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image)

    blocks = item.get("blocks")
    if blocks is None:
        blocks = [item]
    for block in blocks:
        render_block(draw, block, item["locale"])

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", compress_level=6)
    print(f"{item['locale']}: {output}")


def main() -> None:
    data = json.loads(parse_args().manifest.read_text(encoding="utf-8"))
    for item in data["items"]:
        render_item(item)


if __name__ == "__main__":
    main()
