# Apple App Workflow

- Build and test the affected scheme. If shared code or configuration changes, check each affected platform and extension. Prefer the project's build-only entry point. Start or replace a user-facing app instance only when the user requests foreground verification.
- Use the project's simulator or device workflow for UI checks. Verify affected layouts, appearance, and accessibility. Report hardware, entitlement, and synchronization behavior only for the environment that was actually checked.
- Use the affected target's String Catalog for user-facing and accessibility text. Follow the project's source language and update its supported locales in the same change. Include extensions, widgets, intents, and notifications when affected.
- Preserve bundle identifiers, signing teams, entitlements, capabilities, and extension embedding. Obtain explicit approval before changing these boundaries. Follow the project's signing requirements for simulator builds that depend on entitlements.
- Use the project's approved App Store Connect workflow. Build upload, tester distribution, and review submission each require authorization for that operation.
