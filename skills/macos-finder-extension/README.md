# macOS Finder Extension

Build and diagnose Finder Sync menus, badges, and toolbar actions while keeping application state, file authorization, and durable work in the containing app. Includes local checks for bundle structure, signatures, entitlements, registration, and menu image rendering intent. The icon workflow verifies template or app artwork colors in the real Finder.

## Install

Ask your Agent: "Install macos-finder-extension from https://github.com/huihuisang/ajigu-skills."

```bash
npx skills add huihuisang/ajigu-skills -g -y --skill macos-finder-extension
```

Or copy the full directory into your host's skill directory. Node.js is required only for command installation.

## Configuration and requirements

No extra configuration or API key is needed for inspection. Requires macOS, Bash, PlistBuddy, codesign, plutil, and pluginkit. Building also requires the project's Xcode toolchain and signing setup. Check that Finder Sync fits the product: Apple positions it for synchronization-related Finder UI, not general Finder customization. File Provider and Quick Actions serve different needs.

## Usage and output

Request: "Diagnose why this Finder Sync extension does not show its context menu."

```bash
bash scripts/inspect_finder_extension.sh "/path/to/App.app"   Contents/PlugIns/FinderExtension.appex com.example.App.FinderExtension
```

Run this command from the installed skill directory. The script prints structure, signatures, team identifiers, entitlements, and registration details. A pass covers these checks only; it does not establish that the UI or file mutation works.

## Security and privacy

The inspection script uses local system tools and does not upload data or change extension registration. Output can include local paths and team identifiers. Installing the skill does not authorize changing signing, App Groups, entitlements, sandbox settings, or file access. Reuse existing task authorization; ask before expanding its scope. Restarting Finder can interrupt the user's work and must fit the authorized test scope.

## Validation and troubleshooting

```bash
python3 scripts/test_inspection.py
```

Tests use disposable bundle fixtures and command stubs for signature and registration cases. They do not install an extension or prove real Finder interaction. Follow [verification.md](references/verification.md) for the real app and extension test matrix.

Inspect a bundled menu image with the macOS Swift toolchain:

```bash
swift scripts/inspect_menu_icon.swift /path/to/FinderExtension.appex ActionTemplate
swift scripts/inspect_menu_icon.swift /path/to/FinderExtension.appex AppMenuIcon --full-color
python3 scripts/test_menu_icons.py
```

This check needs AppKit and a local Swift compiler. It validates the image's declared intent and archive behavior, while [menu-icons.md](references/menu-icons.md) covers the required real Finder Light/Dark and highlighted-state observations. A successful resource check does not establish correct menu colors.
