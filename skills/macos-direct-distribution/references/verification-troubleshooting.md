# Verification and troubleshooting

Diagnose the first broken invariant. Do not weaken security settings or repeat mutations until the failure is understood.

## Verification matrix

| Layer | What must be true | Useful checks |
| --- | --- | --- |
| Nested code | Every executable is independently signed with its required entitlements | `codesign --verify --strict --verbose=4 <item>` |
| Exported app | Recursive signature is intact; identity, Team ID, timestamp, Hardened Runtime, and entitlements are correct | `codesign --verify --deep --strict --verbose=2 <app>`; `codesign -dvvv <app>`; `codesign -d --entitlements :- <app>` |
| App distribution policy | macOS considers the top-level app distributable | `xcrun syspolicy_check distribution <app>` on macOS 14+; otherwise `spctl --assess --type exec --verbose=4 <app>` |
| DMG integrity | The image's internal checksums are valid before submission and after stapling | `hdiutil verify <dmg>` |
| Signed DMG | The exact DMG is signed by the expected Developer ID Application identity | `codesign --verify --strict --verbose=2 <dmg>`; `codesign -dvvv <dmg>` |
| Notary submission | Status is `Accepted`; log covers the expected nested code and has no ignored release-policy issue | `notarytool info/log` or the project-native equivalent |
| Stapled DMG | The ticket is attached and readable | `xcrun stapler validate <dmg>` |
| DMG policy | Gatekeeper accepts opening the DMG | `spctl --assess --type open --context context:primary-signature --verbose=4 <dmg>` |
| User journey | A fresh system accepts a quarantined download while offline, installs it, and launches it | Fresh VM/Mac, real download, network disconnected, drag to `/Applications`, launch |

Command-line policy checks are quick diagnostics, not complete substitutes for the final user-journey test.

## Failure map

### `The signature of the binary is invalid`

Likely causes:

- the bundle was modified after signing;
- nested code is unsigned, signed in the wrong order, or in an invalid bundle location;
- the wrong identity or entitlements were applied;
- a packaging/copy step damaged metadata.

Actions:

1. Run strict verification on the top-level app and follow the first `in subcomponent` path.
2. Verify that nested item independently and inspect its signature and entitlements.
3. Rebuild from a clean trusted source; avoid emergency re-signing of an already-mutated release.
4. If signing manually, sign deepest code first and the app last. Never solve this by adding `--deep` to a signing command.

### Missing secure timestamp

`codesign -dvv` should show `Timestamp=<date>`. `Signed Time=<date>` is not equivalent. Xcode normally adds a secure timestamp during archive/export, not ordinary development builds. In a manual signing flow, use `--timestamp` and ensure the host can reach Apple's timestamp service.

### Missing Hardened Runtime

Rebuild with the Hardened Runtime capability or manual `--options=runtime` on the correct code items. Do not add broad hardened-runtime exception entitlements unless the executable genuinely requires them and the security tradeoff is reviewed.

### `com.apple.security.get-task-allow` is present

Export a distribution build through Xcode or remove debug entitlement injection from the distribution configuration. Do not strip or re-sign only the outer app while leaving nested code inconsistent; rebuild/export the release correctly.

### Wrong certificate type or identity

Apps, helpers, command-line code, and DMGs use `Developer ID Application`. Flat installer packages use `Developer ID Installer`. Resolve duplicate names by fingerprint and verify the Team ID. Confirm the identity includes its private key and is valid for code signing.

### Notarization status is `Invalid`

Retrieve the JSON log immediately and group issues by path. Fix the earliest/root signing or packaging error before downstream messages. Rebuild the artifact, verify locally, and submit the newly signed immutable outermost container. Do not staple an invalid submission.

### Local wait timed out or network failed

`notarytool submit --wait --timeout ...` timing out does not cancel the server job. Prefer a recoverable flow that saves the submit response, submission ID, pre-submit SHA-256, and DMG CDHash immediately after upload, then waits by ID. Use `info`, `wait`, or `log` on that ID. If the ID was lost, inspect the project's history/list operation and correlate by artifact name and submission time. Resubmit only when you establish that upload never created a usable submission or after producing a changed artifact.

### Stapling fails

Confirm:

- submission status is `Accepted`;
- the local file is the same signed artifact that was submitted;
- the format supports stapling (UDIF DMG, signed executable bundle, or signed flat installer package; not ZIP);
- the file and containing location are writable enough for `stapler` to attach the ticket;
- selected Xcode command-line tools are current.

Compare the DMG's `CDHash` from `codesign -dvvv` with the notary log when artifact identity is in doubt. Preserve both the pre-staple candidate and notary log during diagnosis.

### Gatekeeper rejects an `Accepted` submission

Notarization acceptance is necessary but not sufficient. Verify the exact distributed bytes and check:

- stapled ticket validation;
- correct DMG assessment type/context;
- the app copied from the final mounted DMG, not a nearby build;
- quarantine-aware download behavior;
- nested code and runtime behavior;
- whether the app is launched from `/Applications` instead of directly from the DMG;
- current macOS-specific trusted-execution diagnostics.

Reproduce in a fresh VM. Gatekeeper caches assessments, so repeatedly testing the same artifact on a development Mac can produce misleading results. Do not remove `com.apple.quarantine` as a release fix; doing so bypasses the path users must pass.

### The DMG layout is wrong

This is a packaging/presentation failure, not a reason to re-sign code inside the app. Recreate the writable layout image, detach it cleanly, convert to a new final read-only DMG, then restart the DMG signing/notarization/stapling chain because the outer artifact changed.

## Current-tool checks

Before updating a durable pipeline, inspect the selected toolchain rather than assuming blog syntax remains current:

```zsh
xcode-select --print-path
xcodebuild -version
xcrun notarytool --help
xcrun notarytool help submit
xcrun stapler --help
diskutil image create --help
```

Apple no longer accepts `altool` notarization uploads. Use `notarytool`, a current project-native wrapper such as `asc` when required by repository policy, or the Notary API.

## Primary sources

- [Resolving common notarization issues](https://developer.apple.com/documentation/security/resolving-common-notarization-issues)
- [TN3147: Migrating to the latest notarization tool](https://developer.apple.com/documentation/technotes/tn3147-migrating-to-the-latest-notarization-tool)
- [Testing a Notarised Product](https://developer.apple.com/forums/thread/130560)
- [Resolving Gatekeeper Problems](https://developer.apple.com/forums/thread/706379)
- [Code Signing Tasks](https://developer.apple.com/library/archive/documentation/Security/Conceptual/CodeSigningGuide/Procedures/Procedures.html)
