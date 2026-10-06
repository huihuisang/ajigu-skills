# Manual DMG release workflow

Use this reference only when the repository does not already provide an equivalent release command. Adapt names and paths to the project; do not paste the recipe blindly.

## 1. Resolve release inputs

Use task-specific variables and absolute paths. Create a unique task-owned working directory and keep the final output outside it. Require the output path not to exist before continuing.

```zsh
release_source_ref="REVIEWED-COMMIT-SHA"
release_work_dir="$(mktemp -d "${TMPDIR:-/tmp}/MacDirectRelease.XXXXXX")"
release_scheme="ExampleApp"
release_archive="${release_work_dir}/ExampleApp.xcarchive"
release_export_dir="${release_work_dir}/Export"
release_app="${release_export_dir}/ExampleApp.app"
release_stage="${release_work_dir}/DiskImage"
release_dmg="/absolute/release-output/ExampleApp-1.2.3-45.dmg"
release_evidence_dir="/absolute/release-evidence/ExampleApp-1.2.3-45"
release_volume="ExampleApp"
release_identity="Developer ID Application: Example Company (TEAMID1234)"
release_notary_profile="ExampleApp-Notary"
```

Before building, inspect:

```zsh
xcode-select --print-path
xcodebuild -version
security find-identity -v -p codesigning
xcrun notarytool --version
diskutil image create --help
```

Also inspect the repository status, selected commit/ref, submodule/LFS state, and the release script itself. Stop if a formal release would unintentionally include dirty changes or if the script can stash, reset, clean, rewrite source files, or overwrite output beyond the user's authorization. Select the identity by its exact full name or fingerprint when names are ambiguous. Never use a Development, Mac App Distribution, ad hoc, or Installer identity to sign an app or DMG.

## 2. Archive and export the app

Use the project's workspace/project, scheme, configuration, destination, export options, and provisioning behavior. A representative Xcode flow is:

```zsh
xcodebuild archive \
  -project ExampleApp.xcodeproj \
  -scheme "$release_scheme" \
  -configuration Release \
  -destination "generic/platform=macOS" \
  -archivePath "$release_archive"

xcodebuild -exportArchive \
  -archivePath "$release_archive" \
  -exportPath "$release_export_dir" \
  -exportOptionsPlist /absolute/project/Distribution/ExportOptions-DeveloperID.plist
```

The export options must select Developer ID distribution for the project's Xcode version. Prefer a checked-in, reviewed export-options file over generating an unexplained one during the release.

If the product is not an Xcode app or Xcode cannot manage signing, enumerate all nested code, give each item only its required entitlements, and sign from the deepest item outward. Do not sign with `--deep`.

## 3. Gate the exported app

```zsh
codesign --verify --deep --strict --verbose=2 "$release_app"
codesign -dvvv "$release_app"
codesign -d --entitlements :- "$release_app"
```

Confirm all of the following rather than relying only on exit status:

- `Authority` is the expected Developer ID Application identity.
- `TeamIdentifier` is the expected team.
- a secure `Timestamp` is present; `Signed Time` alone is not a secure timestamp.
- Hardened Runtime is enabled.
- `com.apple.security.get-task-allow` is absent or false.
- required project-specific entitlements are present and unexpected high-risk entitlements are absent.

On macOS 14 or later, prefer:

```zsh
xcrun syspolicy_check distribution "$release_app"
```

For older systems or as an additional quick check:

```zsh
spctl --assess --type exec --verbose=4 "$release_app"
```

These checks do not replace a real quarantined-download test.

## 4. Build the DMG

For a reproducible plain installer, create a fresh staging directory, copy the app with metadata intact, and add the standard Applications link:

```zsh
mkdir -p "$release_stage"
ditto "$release_app" "${release_stage}/ExampleApp.app"
ln -s /Applications "${release_stage}/Applications"

diskutil image create from \
  "$release_stage" \
  "$release_dmg" \
  --volumeName "$release_volume" \
  --format UDZO
```

On older macOS hosts where `diskutil image create` is unavailable, inspect local help and use the compatible `hdiutil create -srcfolder ... -format UDZO` form. Do not switch an established pipeline only for stylistic consistency.

For a styled DMG, use a writable temporary image (`UDRW`), mount it, add `.background` assets, configure Finder icon positions/window settings, detach it, then convert it to a new compressed read-only image (`UDZO`). Check local help before choosing the creator: support for writable formats varies between tool versions; use `hdiutil create -format UDRW` when the selected `diskutil` command does not support that operation.

```zsh
hdiutil create \
  -size 250m \
  -fs APFS \
  -volname "$release_volume" \
  -format UDRW \
  "${release_work_dir}/ExampleApp-layout.dmg"
```

Discover the actual mount point from tool output instead of assuming `/Volumes/<name>`, because a conflicting volume can cause a suffix. Track the device identifier and detach it on exit. Treat Finder layout as presentation metadata; test it but keep security gates independent of it.

Never overwrite an existing release DMG. Ensure no unintended files, credentials, logs, aliases, or development artifacts entered the staging directory.

Before signing and uploading the final read-only image, verify its internal checksums:

```zsh
hdiutil verify "$release_dmg"
```

## 5. Sign the final DMG

```zsh
codesign --force \
  --sign "$release_identity" \
  --timestamp \
  "$release_dmg"

codesign --verify --strict --verbose=2 "$release_dmg"
codesign -dvvv "$release_dmg"
```

The DMG is a distinct signed object even when the app inside is already signed.

## 6. Authenticate without exposing secrets

Reuse a validated existing profile when available. To create a local `notarytool` profile with Apple ID authentication, omit `--password` so the tool prompts securely:

```zsh
xcrun notarytool store-credentials "$release_notary_profile" \
  --apple-id "developer@example.com" \
  --team-id "TEAMID1234"
```

`notarytool` also supports App Store Connect API keys. Follow repository policy and CI secret management; pass a key path, key ID, and issuer as required without printing the `.p8` contents.

If the project requires another supported client, such as `asc`, use that client's authenticated profile and equivalent submit/status/log workflow. Inspect installed help instead of guessing flags. A current `asc` flow exposes these operations:

```zsh
asc auth status
asc notarization submit --file "$release_dmg" --output json
asc notarization status --id "SUBMISSION-ID" --output json
asc notarization log --id "SUBMISSION-ID" --output json
asc notarization list --limit 10 --output json
```

The `log` response provides the developer-log URL; retrieve and retain that log without exposing credentials. Follow the repository's existing handling when it is stricter.

## 7. Notarize the immutable outermost container

For a recoverable generic `notarytool` flow, compute and save the pre-submit SHA-256 and DMG `CDHash`, then submit without a long combined wait so the response and submission ID can be persisted immediately:

```zsh
if [[ -e "$release_evidence_dir" ]]; then
  print -u2 "Release evidence path already exists: $release_evidence_dir"
  return 1
fi
mkdir -p "$release_evidence_dir"

shasum -a 256 "$release_dmg"
codesign -dvvv "$release_dmg"

xcrun notarytool submit "$release_dmg" \
  --keychain-profile "$release_notary_profile" \
  --output-format json \
  > "${release_evidence_dir}/notary-submit.json"

release_submission_id="$(plutil -extract id raw -o - "${release_evidence_dir}/notary-submit.json")"
xcrun notarytool wait "$release_submission_id" \
  --keychain-profile "$release_notary_profile" \
  --timeout 1h
```

Persist the submission response, ID, pre-submit hash, and timestamp in release evidence outside ephemeral logs as soon as upload succeeds. If the local wait times out, the service continues processing. Query or wait on that same ID; do not create duplicate submissions just because the client stopped waiting. If the client or network failed before the ID was recorded, use the project's `history` or `list` operation to recover the recent submission and correlate it with the artifact and time window; resubmit only after establishing that no valid submission exists.

Always retrieve the completed submission log, including for `Accepted` submissions:

```zsh
xcrun notarytool log "SUBMISSION-ID" \
  --keychain-profile "$release_notary_profile" \
  /absolute/release-evidence/notary-log.json
```

Proceed only when status is exactly `Accepted` and the log contains no unresolved issue that invalidates release policy.

## 8. Staple and verify the final bytes

```zsh
xcrun stapler staple "$release_dmg"
xcrun stapler validate "$release_dmg"
hdiutil verify "$release_dmg"
codesign --verify --strict --verbose=2 "$release_dmg"
spctl --assess --type open \
  --context context:primary-signature \
  --verbose=4 \
  "$release_dmg"
shasum -a 256 "$release_dmg"
```

Mount the stapled DMG read-only, verify the app actually contained in that DMG with `codesign` and `syspolicy_check distribution` (or `spctl`), inspect its final entitlements again, and confirm the drag-to-Applications experience. Do not assume that verifying the pre-packaging app proves the packaged copy is correct.

For the production acceptance test, use an authorized private staging or real distribution path, download the candidate in a fresh VM through Safari or another quarantine-aware path, take the VM offline, open the DMG, drag the app to `/Applications`, and launch it. Do not upload to any distribution target without authorization. If no approved quarantine-aware path is available, report this test as pending rather than silently publishing. This is the proof that signing, notarization, stapling, quarantine propagation, packaging, and user instructions work together.

## 9. Release evidence

Retain or report:

- product version and build number;
- source commit/ref, clean or dirty state, and relevant submodule/LFS revisions;
- release script path plus its commit or content hash;
- pre-submit filename, byte size, SHA-256, and signed DMG CDHash;
- post-staple final filename, byte size, and SHA-256;
- selected Xcode/macOS versions;
- signing certificate common name, Team ID, and expiry (never the private key);
- notarization submission ID, terminal status, and log location;
- results of app, DMG, stapler, Gatekeeper, and quarantined-download checks;
- deviations, warnings, skipped tests, and the reason for each.

## Primary sources

- [Notarizing macOS software before distribution](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- [Creating distribution-signed code for macOS](https://developer.apple.com/documentation/xcode/creating-distribution-signed-code-for-the-mac)
- [Packaging Mac software for distribution](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution)
- [Customizing the notarization workflow](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow)
- [Code Signing Tasks](https://developer.apple.com/library/archive/documentation/Security/Conceptual/CodeSigningGuide/Procedures/Procedures.html)
- [Technical Note TN2206: macOS Code Signing In Depth](https://developer.apple.com/library/archive/technotes/tn2206/_index.html)

The workflow was informed by Stewart Lynch's [Mac App Direct Distribution, DMG Signing & Notarization Guide](https://www.createchsol.com/blog/2026-08-30-mac-app-direct-distribution-dmg-signing-notarization-guide.html), then tightened against the Apple sources above.
