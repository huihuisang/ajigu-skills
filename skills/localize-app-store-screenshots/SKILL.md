---
name: localize-app-store-screenshots
description: Localize marketing text embedded in existing App Store screenshot PNGs while preserving the original product imagery pixel-for-pixel outside explicit text regions. Use when adapting already-designed screenshots to additional storefront languages, replacing screenshot headlines without redesigning artwork, validating Apple screenshot dimensions and alpha rules, or preparing reviewed screenshot uploads with the asc CLI.
---

# Localize App Store Screenshots

Preserve the approved artwork and localize only its marketing copy. Render final text deterministically with installed fonts, composite only inside the approved copy region, and use `asc` review/apply for remote delivery.

## Workflow

1. Inventory source PNGs, ordering, dimensions, device families, and existing remote screenshots.
2. Write market-native copy. Preserve the selling idea; do not translate literally when phrasing becomes awkward. Keep line breaks intentional.
3. Inspect every source image before editing.
4. Prepare a clean master by removing only the source marketing copy. Prefer an existing approved clean master. If cleanup is necessary, use a tight mask and preserve every pixel outside it.
5. Render exact localized copy with `scripts/render_localized_text.py`. Use an installed font with confirmed glyph coverage; never use image generation to draw final text.
6. Define a tight text-region box and verify the final bitmap differs from the approved source only inside it.
7. Review a labeled contact sheet, then inspect every CJK title at 100% scale for exact glyphs, spelling, wrapping, hierarchy, and cleanup seams.
8. Validate dimensions, RGB opacity, file count, ordering, exact manifest copy, and zero changed pixels outside each permitted region.
9. Generate ASC review artifacts, inspect them, approve them, and upload with plan/apply only when its planned groups exactly match the intended locale/display-type matrix. Never delete or replace remote screenshots without explicit authorization.
10. List remote screenshots again and verify locale, device family, count, and processing state.

## Image-generation boundary

Do not ask an image model to render final localized copy. Generative text can contain substituted glyphs, remnants, or hallucinated characters even when the prompt says verbatim.

Use image generation only when a clean background patch cannot be produced locally, and request removal rather than replacement:

```text
Use case: precise-object-edit
Asset type: clean master for a localized App Store screenshot
Input image: edit target
Primary request: Remove only the existing marketing copy and reconstruct the background.
Constraints: Preserve the background, device mockup, perspective, lighting, every product-screen pixel, colors, crop, and aspect ratio. Do not translate or redraw the product UI.
Avoid: any text, letters, symbols, watermark, redesign, device changes, UI changes, or altered product imagery.
```

Reject the result if composition or protected artwork changes. Never use the full generated bitmap; composite only a reviewed cleanup patch inside the allowed region.

## Deterministic composition

Prepare a clean master locally when the source copy is light on a textured background:

```bash
python scripts/prepare_clean_master.py \
  --source /path/to/approved.png \
  --output /path/to/clean-master.png \
  --box x,y,width,height
```

Render exact text from a JSON manifest:

```bash
python scripts/render_localized_text.py --manifest /path/to/text-manifest.json
python scripts/verify_localized_text.py --manifest /path/to/text-manifest.json
```

Create a JSON manifest using the schema in `references/manifest.md`, then run:

```bash
python scripts/compose_localized_patch.py --manifest /path/to/manifest.json
```

The script resizes the generated edit to the exact source dimensions, blends only within the allowed rectangle plus feathered edge, writes opaque RGB PNG, and verifies that decoded pixels outside the allowed region are identical to the source.

Do not widen a box to hide model drift. Tighten it around the marketing copy. Never include product UI in the permitted region.

## App Store QA

- Preserve the source dimensions unless targeting a different Apple display type.
- Require opaque RGB output; reject alpha-bearing PNGs.
- Keep one ordered set per storefront and display type.
- Use market-appropriate fonts/glyphs and visually inspect CJK output.
- Confirm every title at thumbnail scale and every subtitle at 100% scale.
- Compare visible copy character-for-character with the reviewed manifest. OCR may assist Latin-script QA but never replaces visual CJK inspection.
- Reject residual source letters, duplicate strokes, replacement glyphs, tofu boxes, unexpected punctuation, or model-generated text.
- Treat zero outside-region pixel changes as a hard invariant.

## ASC upload safety

Read the installed `asc-shots-pipeline` and `asc-cli-usage` skills before upload. Confirm current flags with `asc screenshots --help` and command-specific `--help`.

Prefer:

```bash
asc screenshots review-generate --framed-dir OUTPUT_ROOT --output-dir REVIEW_DIR
asc screenshots review-open --output-dir REVIEW_DIR
asc screenshots review-approve --all-ready --output-dir REVIEW_DIR
asc screenshots plan --app APP_ID --version VERSION --review-output-dir REVIEW_DIR --output json
asc screenshots apply --app APP_ID --version VERSION --review-output-dir REVIEW_DIR --confirm --output json
```

If plan/apply cannot express the intended locale mapping, resolve the exact version-localization ID and use `asc screenshots upload` for that locale only. List screenshots before and after. Do not assume upload replaces existing screenshots; inspect the CLI behavior and Apple limits first.

Some dimensions are accepted by multiple Apple display types. For example, `1290x2796` may validate as both `APP_IPHONE_67` and `APP_IPHONE_69`. If plan output duplicates the same files across display types, do not apply it. Run an app-scoped upload with an explicit `--device-type`, after a matching dry run:

```bash
asc screenshots upload --app APP_ID --version-id VERSION_ID --path OUTPUT_ROOT --device-type APP_IPHONE_67 --dry-run
asc screenshots upload --app APP_ID --version-id VERSION_ID --path OUTPUT_ROOT --device-type APP_IPHONE_67
```

## Resources

- `scripts/compose_localized_patch.py`: pixel-locked compositing and validation.
- `references/manifest.md`: manifest schema and example.
