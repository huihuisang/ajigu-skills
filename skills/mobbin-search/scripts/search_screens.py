#!/usr/bin/python3
"""Search Mobbin's REST API and download screenshots for visual inspection."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


API_URL = "https://api.mobbin.com/v1/screens/search"
MAX_IMAGE_BYTES = 30 * 1024 * 1024


def bounded_limit(value: str) -> int:
    limit = int(value)
    if not 1 <= limit <= 100:
        raise argparse.ArgumentTypeError("limit must be between 1 and 100")
    return limit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search Mobbin and download matching screenshots."
    )
    parser.add_argument("query", help="A natural-language description of one screen")
    parser.add_argument("--platform", required=True, choices=("ios", "web"))
    parser.add_argument("--limit", type=bounded_limit, default=5)
    parser.add_argument("--mode", choices=("deep", "standard"), default="deep")
    parser.add_argument(
        "--image-quality",
        choices=("optimized", "high"),
        default="optimized",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for screenshots and results.json (defaults to .mobbin/)",
    )
    return parser.parse_args()


def api_error_message(status: int, body: bytes) -> str:
    try:
        payload = json.loads(body.decode("utf-8"))
        error = payload.get("error", {})
        detail = error.get("message") or error.get("code")
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        detail = None
    suffix = f": {detail}" if detail else ""
    return f"Mobbin API request failed (HTTP {status}){suffix}"


def search_screens(api_key: str, args: argparse.Namespace) -> list[dict[str, Any]]:
    payload = {
        "query": args.query,
        "platform": args.platform,
        "mode": args.mode,
        "limit": args.limit,
        "image_quality": args.image_quality,
        "exclude_screen_ids": [],
    }
    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "snore-tracker-mobbin-search/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            body = response.read()
    except HTTPError as error:
        raise RuntimeError(api_error_message(error.code, error.read())) from error
    except URLError as error:
        raise RuntimeError(f"Mobbin API connection failed: {error.reason}") from error

    try:
        decoded = json.loads(body.decode("utf-8"))
        screens = decoded["screens"]
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise RuntimeError("Mobbin API returned an unexpected response") from error
    if not isinstance(screens, list):
        raise RuntimeError("Mobbin API returned an invalid screens collection")
    return screens


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48].rstrip("-") or "mobbin-search"


def output_directory(args: argparse.Namespace) -> Path:
    if args.output_dir:
        return args.output_dir.expanduser().resolve()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return (Path.cwd() / ".mobbin" / f"{slugify(args.query)}-{timestamp}").resolve()


def safe_filename_part(value: str) -> str:
    part = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return part[:36] or "screen"


def image_url(screen: dict[str, Any]) -> str | None:
    image = screen.get("image")
    if isinstance(image, dict) and isinstance(image.get("url"), str):
        return image["url"]
    value = screen.get("image_url")
    return value if isinstance(value, str) else None


def image_extension(content_type: str | None) -> str:
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/avif": ".avif",
    }.get(normalized, ".img")


def download_image(url: str, destination_stem: Path) -> Path:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("image URL is not a valid HTTPS URL")

    request = Request(url, headers={"User-Agent": "snore-tracker-mobbin-search/1.0"})
    temporary: Path | None = None
    try:
        with urlopen(request, timeout=60) as response:
            destination = destination_stem.with_suffix(
                image_extension(response.headers.get("Content-Type"))
            )
            temporary = destination.with_suffix(destination.suffix + ".download")
            total = 0
            with temporary.open("wb") as output:
                while chunk := response.read(64 * 1024):
                    total += len(chunk)
                    if total > MAX_IMAGE_BYTES:
                        raise RuntimeError("image exceeds the 30 MB safety limit")
                    output.write(chunk)
            temporary.replace(destination)
            return destination
    except (HTTPError, URLError, OSError) as error:
        raise RuntimeError(f"image download failed: {error}") from error
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def enrich_and_download(
    screens: list[dict[str, Any]], directory: Path
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for index, raw_screen in enumerate(screens, start=1):
        screen = (
            dict(raw_screen) if isinstance(raw_screen, dict) else {"raw": raw_screen}
        )
        url = image_url(screen)
        if not url:
            screen["download_error"] = "Mobbin did not return an image URL"
            enriched.append(screen)
            continue

        app_name = str(screen.get("app_name") or "screen")
        screen_id = str(screen.get("id") or index)[:12]
        stem = directory / f"{index:02d}-{safe_filename_part(app_name)}-{screen_id}"
        try:
            screen["local_path"] = str(download_image(url, stem))
        except RuntimeError as error:
            screen["download_error"] = str(error)
        enriched.append(screen)
    return enriched


def main() -> int:
    args = parse_args()
    api_key = os.environ.get("MOBBIN_API_KEY", "").strip()
    if not api_key or api_key.startswith("op://"):
        print(
            "MOBBIN_API_KEY is unavailable. Run this command through scripts/run-search.",
            file=sys.stderr,
        )
        return 2

    try:
        screens = search_screens(api_key, args)
        directory = output_directory(args)
        directory.mkdir(parents=True, exist_ok=False)
        enriched = enrich_and_download(screens, directory)
        result = {
            "query": args.query,
            "platform": args.platform,
            "output_dir": str(directory),
            "screens": enriched,
        }
        results_path = directory / "results.json"
        results_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
