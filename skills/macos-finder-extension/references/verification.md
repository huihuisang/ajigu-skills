# Build, Installation, and Verification

## Build the Exact Candidate

Rebuild immediately before installation. An existing process causes `open` to activate stale code, so quit the containing app and extension before copying or launching the candidate.

For a release-style handoff:

1. Build the relevant scheme and configuration.
2. Inspect the built app's embedded `.appex`.
3. Quit old app and extension processes.
4. Unregister development or DerivedData copies when they compete with the installed bundle.
5. Install one canonical app copy, normally in `/Applications`.
6. Register and enable the installed extension using its exact bundle identifier.
7. Restart Finder.
8. Launch the installed app and confirm process paths.

Do not force-enable or change system extension settings from product code. `pluginkit` is useful for local development diagnostics, not a product architecture.

## Inspect the Installed State

Run the bundled `inspect_finder_extension.sh`. Also use:

```bash
pluginkit -m -v -i com.example.App.FinderExtension
```

Confirm exactly one intended registration and inspect its path. Duplicate registrations, an extension running from DerivedData, or a stale app copy can produce intermittent menus and wrong URL routing.

Inspect entitlements from the signed artifacts, not only source files or the Xcode Capabilities UI:

```bash
codesign -d --entitlements - --xml /Applications/App.app 2>/dev/null | plutil -p -
codesign -d --entitlements - --xml \
  /Applications/App.app/Contents/PlugIns/FinderExtension.appex \
  2>/dev/null | plutil -p -
```

For an untouched Release artifact, also run the project's normal signature verification. Development builds may contain Xcode-injected debug dylibs after launch, so distinguish an altered development install from the pristine built product.

## Feature Matrix

Test only the surfaces the product implements, but test each end to end:

- Context menu: correct selection, menu kind, enabled state, localization, icon appearance, action delivery, and result.
- Menu glyphs: run the built-resource inspection and capture real Finder Light/Dark menus with the extension item both normal and highlighted, as specified in [menu-icons.md](menu-icons.md). Do not treat action success or `isTemplate` as a visual pass.
- Badges: registration, initial display, updates, clearing, and behavior across Finder windows.
- Toolbar: metadata, enabled state, selected/targeted URL behavior, and action delivery.
- Monitored directories: every intended root plus exclusions; distinguish coverage from authorization.
- Host communication: cold launch, already-running app, payload validation, stale-copy avoidance, and non-activating actions.
- File mutation: real success and rollback/reset, not just receipt of a path.

Use disposable fixtures for write or destructive tests. Do not use personal files merely because they reproduce the bug.

The first menu immediately after Finder restarts can be missing while Finder reconnects. Revisit the monitored directory and reopen once. If it remains missing or repeatedly flakes, diagnose registration and lifecycle instead of accepting retries as normal behavior.

## Logs and Handoff

Inspect recent logs for extension crashes, sandbox denies, bookmark failures, Launch Services errors, and app-specific action failures. Remove only test fixtures created for verification. Leave the latest intended app running if the project requires a ready manual-test build.
