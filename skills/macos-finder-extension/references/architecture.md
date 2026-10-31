# Architecture and API Selection

## Choose the Smallest Finder Integration

Apple positions Finder Sync for synchronization-related UI in monitored directories. Confirm that this extension point fits the product and distribution policy before using it for other Finder actions; it is not a general Finder customization API.

Consider another mechanism when Finder Sync is not the real requirement:

- Use File Provider when the product implements a synchronized or virtualized file domain.
- Use a Service or Quick Action for a simple user-invoked operation that does not need badges, monitored directories, or a toolbar item.
- Use ordinary document opening when Finder only needs to pass files to the app.

Do not use Finder Sync as the synchronization engine. Keep it as a UI bridge to the containing app or an existing sync component.

## Target and Embedding Invariants

A Finder Sync extension is an embedded `.appex` with:

- `NSExtensionPointIdentifier` set to `com.apple.FinderSync`.
- `NSExtensionPrincipalClass` naming the `FIFinderSync` subclass.
- Compatible signing with the containing app.
- An Embed Foundation Extensions build phase in the containing app.

Keep bundle identifiers, teams, signing, App Groups, and entitlements aligned with the distribution plan. Treat changes to those values as product configuration changes that must stay within the user's authorized scope.

## Extension Responsibility

Keep the extension small and restart-safe:

- Configure `FIFinderSyncController.default().directoryURLs`.
- Build menus from the current `FIMenuKind` and selection.
- Register badge images and update badge identifiers.
- Expose toolbar metadata and handle toolbar actions if required.
- Capture a small action payload and notify the containing app.

Do not treat the extension process as durable storage. Finder can recreate it, and callbacks can arrive in more than one Finder-related process.

Read `selectedItemURLs()` at the time the menu or action is invoked. Do not cache selections across unrelated callbacks.

## Monitored Directories

`directoryURLs` controls where Finder asks the extension for menus and badges. It does not grant filesystem permission.

If the extension needs the real user Home directory, resolve it with `getpwuid(getuid())`; sandbox APIs can otherwise produce the extension container's Home path.

Broad roots such as Home or `/` may not trigger every Finder surface consistently. When product scope requires wide coverage, include explicit standard-directory fallbacks such as Desktop, Documents, Downloads, Pictures, Movies, Music, Public, CloudStorage, and Mobile Documents. Reapply the set after initialization if Finder connects late, but do not hide persistent registration problems behind repeated timers.

## Context Menus, Badges, and Toolbar

Return an empty menu when the current context has no valid action. Set each menu item's target explicitly.

Keep user-facing source text in English and localize it in the extension's own String Catalog; the containing app's catalog does not automatically localize extension UI.

Use template rendering for neutral glyphs only after verifying Finder adapts them correctly. Use intentional full-color artwork for app or brand icons. Follow [menu-icons.md](menu-icons.md); the source template flag, resource format, and local archive behavior do not prove correct colors across Finder transport.

For badges, register a stable identifier-to-image mapping before assigning badge identifiers to URLs. Keep badge computation outside latency-sensitive Finder callbacks when it depends on expensive work.

## Communication with the Containing App

Choose transport by payload and lifetime:

- App Group storage for durable shared state.
- Shared `UserDefaults` for small preferences, not large or transactional payloads.
- A named pasteboard plus a one-time custom URL for a small immediate action.
- XPC for structured request/response work or a long-lived helper boundary.
- Distributed notifications only as a wake-up signal, not the sole source of truth.

If a custom URL wakes the app, open it explicitly with the installed containing application URL derived from the extension bundle. This avoids Launch Services choosing a stale development copy.

Treat every received path or URL as untrusted routing data. Validate the payload version, action, file URL status, and selection count before use. File authorization is a separate decision described in [sandbox-permissions.md](sandbox-permissions.md).

## Primary source

- [Apple: Finder Sync](https://developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/Finder.html)
