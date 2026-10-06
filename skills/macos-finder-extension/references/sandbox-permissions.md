# Sandbox and File Authorization

## Permission Decision Tree

First decide whether the extension workflow actually reads or writes file contents or metadata.

1. UI-only badges or menu commands that do not touch the file need no new file entitlement.
2. Work confined to the app container or an already authorized sync root should reuse that existing authority.
3. Work on arbitrary Finder-selected items needs a deliberate authorization design in the component performing the mutation.
4. An intentionally unsandboxed direct-distribution app follows a different model; do not disable sandboxing merely to make development easier.

Never infer permission from `directoryURLs`, `selectedItemURLs()`, a path string, custom URL, pasteboard, App Group, or shared defaults. Those mechanisms identify targets or carry data; they do not automatically grant a sandboxed main app write access.

## Security-Scoped Bookmark Pattern

When product UX calls for reusable access to user-chosen roots:

- Present a system open panel in the main app.
- Store bookmark data with `.withSecurityScope`.
- Resolve with `[.withSecurityScope, .withoutUI]`.
- Balance every successful `startAccessingSecurityScopedResource()`.
- Refresh stale bookmark data.
- Keep active roots alive for the operation or process lifetime as required.
- Remove narrower bookmarks after a broader authorized root supersedes them.

The authorization root is a product choice. A workflow that operates throughout Home may request Home once; a project with stricter scope may request a specific folder. For external volumes, choose a root consistent with the requested operation rather than silently escalating to `/`.

## Static Protected-Folder Entitlements

Static Documents, Downloads, Desktop, Pictures, Music, or Movies entitlements can trigger macOS Files & Folders prompts independently of user-selected bookmarks.

Inspect both entitlement files and Xcode build settings. For example, Downloads access can come from either:

- `com.apple.security.files.downloads.read-write`
- `ENABLE_FILE_ACCESS_DOWNLOADS_FOLDER = readwrite`

The Xcode Capabilities UI can appear empty while build settings still generate a signed entitlement. Inspect the signed `.app` and `.appex` rather than trusting the UI.

Do not universally remove or add protected-folder entitlements. Compare them with the product's authorization design, then obtain explicit approval before changing capabilities.

## Diagnostic Patterns

### The app receives the right path but cannot modify the item

Routing worked; authorization did not. Identify which process performs the mutation and prove that process holds a live scope covering the target.

### Every new child folder requests authorization

The app is likely storing item-level or child-level bookmarks while the intended UX is root-level access. Normalize and deduplicate roots according to product policy.

### Home was authorized, but Downloads asks again

Inspect actual signed protected-folder entitlements. A static Downloads capability can cause a second TCC prompt even when a user-selected root already covers the path.

### Expanding monitored directories seems to fix access

That is correlation, not authority. Separate Finder menu coverage from sandbox access and verify each independently.

### A Finder-created bookmark resolves, but writes still fail

Resolution proves identity, not necessarily transferable write scope. Do not build the architecture around an implicit cross-process permission assumption without an end-to-end mutation test.
