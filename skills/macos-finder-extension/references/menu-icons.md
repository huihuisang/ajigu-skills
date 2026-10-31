# Finder Menu Icons

## Choose the Rendering Intent

Finder reconstructs extension menus across a process boundary. The displaying client decides how to interpret image metadata. Runtime SF Symbols, bundled PDFs, and even system templates can keep the wrong foreground in Finder while their source `isTemplate` flag and local archive tests are correct. Do not infer a successful tint from a particular image format, flag, or neighboring native menu item.

Choose the intent before creating the image:

- **Template glyph:** use monochrome artwork with transparency and template rendering. Verify that the actual Finder adapts the glyph in every required state. For asset catalogs, declare the template rendering intent and retain vector data where appropriate. Appearance variants may fix a normal Dark menu without fixing a Light highlighted menu, so test those separately.
- **App or brand artwork:** preserve its intended color and set `isTemplate = false`. For a command that opens the containing app, its app icon is a suitable choice. Check that it remains recognizable on all menu backgrounds.

For an app-opening command, reuse the app artwork as an explicit resource of the extension target. Do not assume a sandboxed extension can inspect its parent app bundle or obtain its artwork through icon services. Load the bundled artwork without converting it into a template:

```swift
func appMenuIcon(in bundle: Bundle) -> NSImage? {
    guard let image = bundle.image(forResource: "AppMenuIcon")?.copy() as? NSImage else { return nil }
    image.size = NSSize(width: 16, height: 16)
    image.isTemplate = false
    return image
}
```

For a system template, use a public image intended for the target control. Do not use Touch Bar-only artwork in ordinary menus. A named system image can archive by name; copying or changing it can remove that identity. Name preservation still does not prove Finder's final tinting.

Do not fix a dark template by replacing it with a fixed white image. Do not choose colors from the extension process's appearance and assume they match Finder's hover state. If a template fails the real rendering matrix, prefer intentional app artwork when the command opens that app, or a text-only item when no suitable image exists. Do not silently claim the original template behavior works.

## Inspect Resources and Rendering Intent

Run the local check appropriate to the image source:

```bash
swift <skill-path>/scripts/inspect_menu_icon.swift \
  /path/to/App.app/Contents/PlugIns/FinderExtension.appex ActionTemplate
swift <skill-path>/scripts/inspect_menu_icon.swift --system-image NSAddTemplate
swift <skill-path>/scripts/inspect_menu_icon.swift \
  /path/to/FinderExtension.appex AppMenuIcon --full-color
```

The check reads the image, rendering intent, logical size, secure archive round trip, and available pixel data. It checks template masks for monochrome content and transparency, and app artwork for retained color. A source representation class is not a universal compatibility rule: compiled catalogs may use different representations from raw PDFs or bitmaps.

The check does not install, register, or modify the extension. `finderAppearanceVerified: false` is intentional. Passing resource checks cannot establish correct colors in Finder.

## Verify Real Finder Rendering

Use the exact signed, installed extension with a valid selection. Observe and capture all four states:

| Appearance | State | Required result |
| --- | --- | --- |
| Light | Not highlighted | Icon has the intended foreground or brand colors and remains recognizable |
| Light | Highlighted | Template follows selected text, or intentional full-color artwork retains its colors and contrast |
| Dark | Not highlighted | Template follows the normal foreground, or full-color artwork remains recognizable |
| Dark | Highlighted | Template follows selected text, or intentional full-color artwork retains its colors and contrast |

Move the pointer away from the item, then into it. Confirm the item is actually highlighted, using both selected-state evidence and the visible background/text change. A mouse event followed by a delay is not proof of selection. Capture enough of a neighboring native row to compare states. Allow appearance changes to propagate before opening a fresh menu; preserve and restore any setting changed for verification.

Keep captures with the build identity and stated rendering intent. Check disabled or increased-contrast states when the feature uses them. Local AppKit screenshots, archive tests, source searches, menu action success, and bundle checks do not replace this matrix. Report any unobserved required state as incomplete.

## Primary Sources

- [Apple: NSImage.isTemplate](https://developer.apple.com/documentation/appkit/nsimage/istemplate)
- [Apple: NSImage named resources](https://developer.apple.com/documentation/appkit/nsimage/init(named:))
- [Apple: Finder Sync](https://developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/Finder.html)
