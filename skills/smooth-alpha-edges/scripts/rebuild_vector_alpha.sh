#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Rebuild a transparent raster silhouette from a closed vector path.

Usage:
  rebuild_vector_alpha.sh \
    --input INPUT.png \
    --output OUTPUT.png \
    --path-file SILHOUETTE.path \
    [--scale 3] \
    [--edge-blur 0.55] \
    [--preview PREVIEW.png] \
    [--preview-width 600] \
    [--preview-color '#111111']

The path file must contain one closed ImageMagick-compatible path in source
pixel coordinates, such as: M 10,10 C 5,20 5,80 10,90 ... Z
EOF
}

input=""
output=""
path_file=""
scale="3"
edge_blur="0.55"
preview=""
preview_width="600"
preview_color="#111111"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input) input="${2:-}"; shift 2 ;;
    --output) output="${2:-}"; shift 2 ;;
    --path-file) path_file="${2:-}"; shift 2 ;;
    --scale) scale="${2:-}"; shift 2 ;;
    --edge-blur) edge_blur="${2:-}"; shift 2 ;;
    --preview) preview="${2:-}"; shift 2 ;;
    --preview-width) preview_width="${2:-}"; shift 2 ;;
    --preview-color) preview_color="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$input" || -z "$output" || -z "$path_file" ]]; then
  usage >&2
  exit 2
fi

command -v magick >/dev/null 2>&1 || {
  echo "ImageMagick 'magick' is required." >&2
  exit 1
}

[[ -f "$input" ]] || { echo "Input not found: $input" >&2; exit 1; }
[[ -f "$path_file" ]] || { echo "Path file not found: $path_file" >&2; exit 1; }
[[ "$input" != "$output" ]] || {
  echo "Refusing to overwrite the input. Choose a sibling output path." >&2
  exit 1
}
[[ "$scale" =~ ^[1-9][0-9]*$ ]] || { echo "--scale must be a positive integer." >&2; exit 2; }
[[ "$preview_width" =~ ^[1-9][0-9]*$ ]] || { echo "--preview-width must be a positive integer." >&2; exit 2; }

read -r source_width source_height < <(magick identify -format '%w %h\n' "$input")
output_width=$((source_width * scale))
output_height=$((source_height * scale))

path_data=$(tr '\n\r' '  ' < "$path_file")
[[ "$path_data" == *M* && "$path_data" == *Z* ]] || {
  echo "Path must contain a move command (M) and be closed (Z)." >&2
  exit 1
}
[[ "$path_data" != *"'"* ]] || {
  echo "Path data must not contain single quotes." >&2
  exit 1
}

task_temp_dir=$(mktemp -d)
trap 'rm -rf "$task_temp_dir"' EXIT
mask_path="$task_temp_dir/mask.png"

# Draw in source coordinates on the enlarged canvas so Bezier geometry remains
# continuous instead of inheriting the source bitmap's stair-stepped outline.
magick \
  -size "${output_width}x${output_height}" xc:black \
  -fill white \
  -stroke none \
  -draw "scale ${scale},${scale} path '${path_data}'" \
  -blur "0x${edge_blur}" \
  "$mask_path"

# Mitchell avoids the ringing artifacts that Lanczos can introduce around
# transparent high-contrast edges. CopyOpacity replaces only the alpha channel.
magick \
  "$input" \
  -alpha on \
  -filter Mitchell \
  -resize "${output_width}x${output_height}!" \
  "$mask_path" \
  -alpha off \
  -compose CopyOpacity \
  -composite \
  -define png:color-type=6 \
  "$output"

if [[ -n "$preview" ]]; then
  preview_height=$((output_height * preview_width / output_width))
  magick \
    -size "${preview_width}x${preview_height}" "xc:${preview_color}" \
    \( "$output" -filter Lanczos -resize "${preview_width}x${preview_height}!" \) \
    -gravity center \
    -composite \
    "$preview"
fi

magick identify -format 'output=%f geometry=%wx%h type=%[type] channels=%[channels]\n' "$output"
