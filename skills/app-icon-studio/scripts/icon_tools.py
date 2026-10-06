"""Compose app icon prompts and check raster asset properties."""

import argparse
import json
from pathlib import Path
import re
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]


def clean_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if len(value) > 2000:
        raise ValueError(f"{name} exceeds 2000 characters")
    return " ".join(value.split())


def compose(brief):
    if not isinstance(brief, dict):
        raise ValueError("The brief must be a JSON object")
    allowed = {"subject", "material", "palette", "details", "mode", "style"}
    if set(brief) - allowed:
        raise ValueError("Unknown brief fields: " + ", ".join(sorted(set(brief) - allowed)))
    subject = clean_text(brief.get("subject"), "subject")
    material = clean_text(brief.get("material"), "material")
    palette = brief.get("palette")
    if not isinstance(palette, list) or not 1 <= len(palette) <= 5:
        raise ValueError("palette must contain 1 to 5 hex colors")
    if any(not isinstance(color, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", color)
           for color in palette):
        raise ValueError("Each palette color must use #RRGGBB")
    details = brief.get("details")
    if not isinstance(details, list) or not 2 <= len(details) <= 3:
        raise ValueError("details must contain 2 or 3 visual details")
    details = [clean_text(value, "detail") for value in details]
    mode = brief.get("mode", "artwork")
    if mode not in ("artwork", "foreground"):
        raise ValueError("mode must be artwork or foreground")
    templates = json.loads((ROOT / "assets" / "prompt-templates.json").read_text(encoding="utf-8"))
    template = templates[mode]
    style = clean_text(brief.get("style", template["default_style"]), "style")
    theme = (f"{template['subject_prefix']} {subject.rstrip('.')}. "
             f"Material: {material.rstrip('.')}. "
             f"Palette: {', '.join(palette)}. "
             f"Key details: {'; '.join(details)}. {style}")
    return "\n\n".join([template["opening"], theme, template["closing"]]) + "\n"


def check_image(path, mode):
    try:
        from PIL import Image
    except ImportError as error:
        raise ValueError("Pillow is unavailable. Use a Python environment with Pillow, or report pixel checks as pending.") from error
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.width * image.height > 4096 * 4096:
                raise ValueError("Image exceeds the inspection limit of 16 megapixels")
            image.load()
            alpha_min, alpha_max = image.convert("RGBA").getchannel("A").getextrema()
            errors = []
            if image.format != "PNG":
                errors.append("Export a PNG file")
            if image.size != (1024, 1024):
                errors.append("Use a 1024 x 1024 canvas")
            if getattr(image, "n_frames", 1) != 1:
                errors.append("Use a still image")
            if mode == "artwork" and alpha_min != 255:
                errors.append("Artwork must be fully opaque")
            if mode == "foreground" and (alpha_min != 0 or alpha_max == 0):
                errors.append("Foreground must contain transparent pixels and visible content")
            return {
                "status": "pass" if not errors else "fail",
                "file": str(path.resolve()), "mode": mode,
                "size": list(image.size), "format": image.format,
                "alpha_extrema": [alpha_min, alpha_max],
                "visual_review": "pending", "errors": errors,
            }


def main():
    if sys.version_info < (3, 10):
        print(json.dumps({"status": "error", "message": "Python 3.10 or later is required"}))
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prompt = commands.add_parser("prompt", help="Create a prompt without replacing existing files")
    prompt.add_argument("brief", type=Path)
    prompt.add_argument("--out", type=Path, required=True)
    check = commands.add_parser("check", help="Check a PNG without changing it")
    check.add_argument("image", type=Path)
    check.add_argument("--mode", choices=("artwork", "foreground"), default="artwork")
    args = parser.parse_args()
    try:
        if args.command == "prompt":
            content = compose(json.loads(args.brief.read_text(encoding="utf-8")))
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("x", encoding="utf-8") as output:
                output.write(content)
            result = {"status": "pass", "prompt": str(args.out.resolve())}
        else:
            result = check_image(args.image, args.mode)
    except Exception as error:
        result = {"status": "error", "message": str(error)}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
