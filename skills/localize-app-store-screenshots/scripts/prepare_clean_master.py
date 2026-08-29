#!/usr/bin/env python3
"""Remove bright source copy inside a tightly scoped region."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--box", required=True, help="x,y,width,height")
    args = parser.parse_args()

    x, y, width, height = (int(value) for value in args.box.split(","))
    image = np.asarray(Image.open(args.source).convert("RGB")).copy()
    roi = image[y : y + height, x : x + width]
    maximum = roi.max(axis=2)
    minimum = roi.min(axis=2)
    candidate = ((minimum > 115) & ((maximum - minimum) < 45)).astype(np.uint8) * 255
    count, labels, stats, _ = cv2.connectedComponentsWithStats(candidate, 8)
    bright_seed = minimum > 220
    mask = np.zeros(candidate.shape, dtype=np.uint8)
    for index in range(1, count):
        component = labels == index
        if stats[index, cv2.CC_STAT_AREA] > 3 and bright_seed[component].any():
            mask[component] = 255
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=1)
    cleaned = cv2.inpaint(cv2.cvtColor(roi, cv2.COLOR_RGB2BGR), mask, 7, cv2.INPAINT_TELEA)
    image[y : y + height, x : x + width] = cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image).save(args.output, format="PNG", compress_level=6)
    print(f"Prepared {args.output}; changed only {args.box}")


if __name__ == "__main__":
    main()
