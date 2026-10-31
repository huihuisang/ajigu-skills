---
name: macos-finder-extension
license: MIT
description: Design, implement, debug, and verify macOS Finder Sync extensions for context menus, badges, toolbar actions, monitored directories, and host-app communication. Use when implementing Finder integration or diagnosing missing menus, incorrect icon colors, sandbox access, localization, signing, registration, or stale builds; do not use as a File Provider sync-engine guide.
---

# macOS Finder Extension

Build Finder Sync extensions as thin Finder UI adapters, with durable state and substantial work owned by the containing app or its existing service layer.

Before implementation, decide whether Finder Sync is the correct extension point. Finder Sync is appropriate for menus, badges, labels, and toolbar UI in monitored directories. File Provider is appropriate for synchronized or virtualized file domains; a Service or Quick Action may be enough for one simple command.

Do not change signing, entitlements, sandbox status, bundle identifiers, App Groups, or embedding outside the user's authorized scope. Reuse approval already given for the task; ask only when a required change adds scope.

## Workflow

1. Inspect the existing project and distribution model before adding targets or capabilities.
2. Define Finder-facing features, monitored-directory scope, app communication, state ownership, and file-authorization needs separately.
3. Implement the smallest extension surface that satisfies the request.
4. Localize extension UI in the extension target. For menu icons, read [menu-icons.md](references/menu-icons.md), choose template or intentional full-color rendering, and check the actual colors in Finder.
5. Build the exact signed candidate, install one canonical copy, register it once, restart Finder, and test the real UI.

Read the focused references when relevant:

- Always read [architecture.md](references/architecture.md) when implementing or restructuring a Finder Sync extension.
- Read [sandbox-permissions.md](references/sandbox-permissions.md) when the workflow reads or writes files outside an existing authorized root, or when macOS prompts unexpectedly.
- Read [verification.md](references/verification.md) before installing, diagnosing registration, or handing off a build.
- Read [menu-icons.md](references/menu-icons.md) whenever adding or changing menu icons or diagnosing their color. A runtime symbol with `isTemplate = true` is not sufficient evidence.
- Read [icon-actions.md](references/icon-actions.md) only for custom-icon/reset-icon work or when its failure patterns match the current bug.

Use the bundled inspection script after building or installing:

```bash
bash <skill-path>/scripts/inspect_finder_extension.sh \
  /path/to/App.app \
  Contents/PlugIns/FinderExtension.appex \
  com.example.App.FinderExtension
```

The bundle identifier is optional. The script inspects the extension point, signing teams, actual signed entitlements, and registration count without assuming a specific permission policy.

## Completion Standard

A successful build is not enough. Verify the requested menus, badges, or toolbar behavior in Finder; verify host communication against the installed app; exercise every requested location or file class; and prove that signed permissions and extension registrations match the intended architecture. Menu icons require observed normal and highlighted states in both Light and Dark appearances; report any untested state as incomplete.
