---
name: mobbin-search
description: Search Mobbin's REST API for real iOS or web UI screenshots and visually analyze the downloaded results. Use for UI/UX references, pattern comparisons, design inspiration, or questions about how existing products implement a screen or flow.
---

# Mobbin Search

Ground design advice in screenshots returned by Mobbin rather than assumptions.

## Search

1. Choose a focused natural-language query describing one screen or intent. Do not include the platform in the query.
2. Infer `ios` for SwiftUI, React Native, or mobile work and `web` for browser products. Ask only when the platform is genuinely unclear.
3. Default to 5 results, `deep` mode, and optimized images. Use up to 15 results when the user explicitly wants variety or comparison.
4. Briefly announce the query and result count, then run:

   ```text
   <skill-directory>/scripts/run-search --platform <ios|web> --limit <count> "<query>"
   ```

5. Read the JSON result and inspect every successful `local_path` with the local image viewer. Never describe a screen from metadata alone.

The launcher accepts a direct `MOBBIN_API_KEY` environment variable. Otherwise it resolves the secret through 1Password using `mobbin.env`. If configuration is missing, explain the one-time setup from the launcher's error without asking the user to paste a secret into chat.

## Respond

Ground observations in visible details such as hierarchy, copy, controls, spacing, color, and element count. Link each cited example using its `mobbin_url`.

- Give a direct answer when 1–3 screens and a short explanation resolve the question.
- For broad comparisons or inspiration sets, first offer a side-by-side HTML evidence board, a user-defined layout, or a text summary. Build the board only after the user chooses.
- Save any evidence board under `.mobbin/`, keep it self-contained, and link every screen back to Mobbin.

Downloaded images and `results.json` are temporary research artifacts under `.mobbin/`; do not commit them.

## Security

- Never print, persist, interpolate into command arguments, or include `MOBBIN_API_KEY` in generated artifacts.
- Keep the API key in 1Password. The committed example contains only a secret reference.
- Treat signed image URLs as temporary credentials: use them for immediate inspection and do not publish them.
- On HTTP 401 or 403, report that the key or Mobbin plan needs attention; do not retry repeatedly.
