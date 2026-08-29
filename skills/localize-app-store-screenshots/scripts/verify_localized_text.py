#!/usr/bin/env python3
"""Verify localized screenshots against a clean master and text manifest."""

from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    data = json.loads(parse_args().manifest.read_text(encoding="utf-8"))
    for item in data["items"]:
        source = np.asarray(Image.open(item["source"]).convert("RGB"))
        output = np.asarray(Image.open(item["output"]).convert("RGB"))
        if output.shape != source.shape:
            raise ValueError(f"Dimension mismatch for {item['locale']}")

        x, y, width, height = item["allowed_box"]
        changed = np.any(source != output, axis=2)
        allowed = np.zeros(changed.shape, dtype=bool)
        allowed[y : y + height, x : x + width] = True
        if np.any(changed & ~allowed):
            raise ValueError(f"Protected pixels changed for {item['locale']}")
        if not np.any(changed & allowed):
            raise ValueError(f"No text rendered for {item['locale']}")

        blocks = item.get("blocks", [item])
        lines = [line for block in blocks for line in block["lines"]]
        for line in lines:
            if unicodedata.normalize("NFC", line) != line:
                raise ValueError(f"Copy is not NFC normalized for {item['locale']}: {line!r}")
            if "\ufffd" in line:
                raise ValueError(f"Replacement glyph in copy for {item['locale']}")

        print(f"{item['locale']}: {output.shape[1]}x{output.shape[0]}, RGB, protected pixels unchanged")


if __name__ == "__main__":
    main()
