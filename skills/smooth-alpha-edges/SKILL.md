---
name: smooth-alpha-edges
description: Repair jagged or noisy outer silhouettes in transparent raster images while preserving the original interior pixels. Use for PNG/WebP cutouts whose alpha boundary is stair-stepped, fringed, or geometrically uneven; do not use when the subject itself should be redrawn.
---

# Smooth Alpha Edges

Repair the alpha geometry, not merely the image resolution. Upscaling a bad 1-bit outline only creates larger stair steps, and blurring it only softens the wrong contour.

## Diagnose first

Inspect the source with ImageMagick:

```bash
magick identify -verbose input.png | rg 'Geometry:|Type:|Alpha:'
```

Distinguish two cases:

- If the silhouette is already geometrically correct but has a hard binary transition, resampling plus an 8-bit alpha edge may be sufficient.
- If the boundary position visibly wobbles, contains bumps, or follows pixel stairs, rebuild the silhouette with a continuous path. Do not rely on resize, blur, erosion, or median filtering as the final fix.

## Rebuild a silhouette

1. Preserve the original file and work on a sibling output until the result is approved.
2. Trace only the outer silhouette as a closed path in the source image's pixel coordinate system. Use `M`, `L`, `C`, and `Z`; prefer a small number of cubic Bezier segments over many points.
3. Keep the path slightly inside the original opaque boundary when transparent pixels do not contain usable RGB data. This avoids dark or white fringe from previously transparent pixels.
4. Save only the path data in a text file, for example:

```text
M 20,10 C 12,10 8,18 8,30 L 8,180 C 8,192 16,200 28,200 L 92,200 C 104,200 112,192 112,180 L 112,30 C 112,18 108,10 100,10 Z
```

5. Run the bundled deterministic helper:

```bash
scripts/rebuild_vector_alpha.sh \
  --input input.png \
  --output input-smoothed.png \
  --path-file silhouette.path \
  --scale 3 \
  --preview input-smoothed-preview.png \
  --preview-width 600
```

The helper preserves the source color content, renders the path at higher resolution, adds a controlled subpixel transition, and writes a true RGBA PNG.

## Validate the result

- Inspect the composited preview at the intended display size. A transparent PNG viewed at extreme 1:1 or enlarged inspection can make normal raster pixel steps look worse than the rendered result.
- Check both light and dark contrasting backgrounds when fringe color matters.
- Confirm the output reports `TrueColorAlpha` with 8-bit alpha.
- Compare interior seams, texture, color, proportions, and placement against the source; only the outer boundary should change.
- Reject black/white halos, clipped corners, expanded transparent RGB artifacts, excessive softness, and subject redesign.

Use generative image editing only when the user permits changes to the subject. For preservation-sensitive cutouts, prefer this deterministic path-mask workflow.
