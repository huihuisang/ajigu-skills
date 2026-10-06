# Custom and Reset Icon Actions

Use this reference for Finder Sync custom-icon actions. Verify behavior on the target macOS version with disposable fixtures.

## Working Shape

- The extension exposes two localized menu items for files and folders.
- It sends an action plus selected paths to the containing app using a small transient payload.
- Customize activates the app and remembers the selection until the user chooses an icon.
- Reset wakes the process without intentionally bringing its window forward, performs the reset, then keeps Finder in front.
- A sandboxed main app obtains durable access through a user-selected security-scoped root consistent with product UX.

## Lessons

### Menu icons must be templates

Bundle monochrome vector artwork in the extension asset catalog, set it to about 16×16 points, and set `isTemplate = true`. This lets Finder render correct Light, Dark, and selected colors. A fixed-color raster commonly appears black or mismatched.

### A target path is not write permission

It is possible for Customize to open the app and show the correct filename while replacement still fails. That proves the transport worked, not the sandbox authority. Verify the process calling `NSWorkspace.setIcon` holds a live scope covering the target.

### Static Downloads access can create an extra prompt

In a design that already authorizes a user-selected root, a signed static Downloads entitlement can trigger a separate macOS Files & Folders prompt. Check both entitlement files and every Debug/Release `ENABLE_FILE_ACCESS_DOWNLOADS_FOLDER` build setting, then inspect the signed app and extension.

### Home-level access is a product choice, not a Finder requirement

For a product intentionally operating across the user's Home directory, requesting Home once avoids a prompt for every Desktop, Documents, or Downloads child. A narrower product should request a narrower root. Do not universalize the Home choice.

### Diagnose metadata before changing reset behavior

A reset can leave stale custom-icon metadata on some system versions. Inspect the custom-icon resource, FinderInfo flag, and any folder-icon extended attribute before and after `NSWorkspace.setIcon(nil, ...)`. Do not delete all extended attributes or rewrite opaque metadata based on a fixed version assumption. Change only documented or fixture-verified custom-icon fields, preserve unrelated metadata, and retest the supported systems.

### Verify filesystem state

After Customize, verify the custom icon bit or `Icon\r` resource exists. After Reset, verify `GetFileInfo -a` reports lowercase `c`, the FinderInfo bit is clear, and `Icon\r` is absent. A menu click without this state change is not a successful test.
