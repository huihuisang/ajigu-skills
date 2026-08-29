# Manifests

## Text rendering

Use this schema with `scripts/render_localized_text.py` after preparing a clean master:

```json
{
  "items": [
    {
      "locale": "ja",
      "source": "/absolute/path/clean-master.png",
      "output": "/absolute/path/ja/0_APP_IPHONE_67_0.png",
      "lines": ["美しいAPOD"],
      "font": "/absolute/path/font.ttc",
      "font_index": 0,
      "font_size": 150,
      "min_font_size": 100,
      "max_width": 830,
      "origin": [100, 134],
      "allowed_box": [60, 100, 900, 450],
      "line_gap": 18,
      "fill": [255, 255, 255]
    }
  ]
}
```

For title/subtitle hierarchy, use `blocks`, where every block carries its own `lines`, font, size, width, origin, gap, and fill fields. The script reduces the requested font size only as needed to fit `max_width`. Put deliberate wrapping in `lines`; do not depend on automatic line breaking.

## Patch composition

Use absolute paths when running outside a project root. Coordinates refer to the source image in pixels.

```json
{
  "feather": 34,
  "jobs": [
    {
      "source": "/project/screenshots/en-US/01.png",
      "generated": "/generated/ja-01.png",
      "output": "/project/screenshots/ja/01.png",
      "box": { "x": 25, "y": 45, "width": 930, "height": 390 }
    }
  ]
}
```

Fields:

- `feather`: Optional global feather radius in pixels. Default: `32`.
- `source`: Approved original PNG.
- `generated`: Image-generation edit containing the localized text.
- `output`: Non-destructive final PNG path.
- `box`: Rectangular region allowed to change.
- `feather`: Optional per-job override.

The script rejects an invalid or empty box, writes an opaque RGB PNG, reopens it, and fails if any decoded pixel outside the box plus feather differs from the decoded source.
