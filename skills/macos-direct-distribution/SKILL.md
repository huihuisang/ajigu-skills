---
name: macos-direct-distribution
license: MIT
description: Prepare, audit, or troubleshoot a Developer ID-signed macOS app distributed outside the Mac App Store in a DMG, including archive/export, hardened-runtime and entitlement checks, DMG construction, notarization, stapling, Gatekeeper testing, and release evidence. Use when preparing direct-download macOS releases; do not use for Mac App Store submissions.
---

# macOS Direct Distribution

Produce the exact immutable artifact users will download, then prove that its code signature, notarization ticket, and Gatekeeper behavior are valid. Treat packaging, signing, notarization, stapling, and post-staple verification as one release chain; after signing, only `stapler` may intentionally change the DMG, and the resulting bytes must remain unchanged through publication.

## Start with repository truth

Before proposing commands or changing a pipeline:

1. Read repository instructions and release documentation.
2. Find existing archive, export, packaging, signing, notarization, and publishing scripts. Audit a release script before running it for source edits, version writes, artifact overwrites, `stash`, `reset`, `clean`, or other repository mutations.
3. Inspect the build system, product type, supported macOS versions, entitlements, signing settings, source commit/ref, submodules or LFS inputs, current branch, and working-tree state.
4. Prefer the project's existing release entry point and authentication mechanism. For example, if repository policy requires `asc` for notarization, use `asc`; do not replace it with `notarytool` merely because the generic recipe uses `notarytool`.
5. Keep unrelated and pre-existing changes out of the task. Never overwrite an existing release artifact silently.

For a production release, establish source provenance before building. Follow any repository rule for the release branch or ref. If the working tree is dirty, do not stash, reset, clean, or silently include those changes: determine whether the requested release intentionally includes them, or build the named commit/ref in an isolated checkout or worktree. A signature proves who signed the bytes, not that they came from the intended source.

Classify the request before acting:

- **Explain, review, or diagnose:** remain read-only unless the user also asks for changes.
- **Build or sign-only:** create a clearly named `unnotarized` artifact and state that it must not be published.
- **Release:** archive/export, package, sign, notarize, staple, and verify. A request to build does not by itself authorize publishing or uploading anywhere other than the Apple notary service when notarization was requested. Upload to a public or private distribution target only when that target is authorized; otherwise report the quarantined-download test as pending.

## Preserve the signing invariants

- Use a `Developer ID Application` identity for app code and DMGs. A flat installer package uses `Developer ID Installer` instead.
- Enable Hardened Runtime for every executable that requires it, use a secure timestamp, and remove `com.apple.security.get-task-allow` from distribution code.
- Use only the entitlements each code item needs. Hardened-runtime exceptions are security decisions, not generic fixes.
- Let Xcode export distribution-signed Xcode apps when possible. In a manual flow, sign nested code from the inside out and sign the outer app last.
- Never use `codesign --deep` to sign. It is appropriate for recursive verification.
- Do not modify the app bundle after signing. Do not modify the DMG after it is signed except with `stapler`.
- Sign every layer, but normally notarize and staple only the outermost distributable container. A ZIP cannot be stapled directly; staple its contents before recreating the ZIP.

## Use the release gates

Stop at the first failed gate; do not submit a known-bad artifact or publish an unverified one.

1. **Preflight:** confirm the selected Xcode toolchain, required tools, exact signing identity, credentials, output path, and enough temporary disk space.
2. **Archive and export:** build a Release archive and export a Developer ID-signed app. Reuse the project workflow rather than inventing generic flags.
3. **Verify the exported app:** recursively verify the signature; inspect its authority, Team ID, secure timestamp, Hardened Runtime, and final entitlements; assess it with `syspolicy_check` or `spctl`.
4. **Construct the DMG:** stage only the intended app and installer assets in an isolated temporary directory. Preserve bundle metadata with `ditto`, add an `/Applications` symlink if appropriate, and produce a compressed read-only UDIF image. Verify the image's internal checksums before submission. Finder background/layout polish is optional and must not weaken reproducibility.
5. **Sign and verify the DMG:** sign it with the expected Developer ID Application identity and a secure timestamp, then verify its signature before upload.
6. **Notarize the exact final DMG:** wait for a terminal result. Save the submission ID. A local wait timeout does not cancel server-side processing, so query the same submission instead of blindly uploading again.
7. **Read the notary log:** inspect it even when the status is `Accepted`; warnings are release evidence and may reveal future failures.
8. **Staple and verify:** staple the ticket to the DMG, validate it, recheck the image's internal checksums and signature, reassess the DMG with Gatekeeper, mount the final DMG, and reverify the contained app from that mounted image.
9. **Test the user path:** for a production release, use a fresh macOS VM or Mac, download through a quarantine-aware path such as Safari, disconnect networking to prove stapling works offline, drag the app to `/Applications`, and launch it. Restore the VM snapshot before each retest because Gatekeeper caches decisions.
10. **Record evidence:** report the source commit/ref and dirty state, release script identity, app version/build, artifact path and size, signing identity and Team ID, pre-submit SHA-256 and CDHash, notarization submission ID/status, post-staple SHA-256, verification results, toolchain version, and any test that was not performed.

Read [references/manual-workflow.md](references/manual-workflow.md) when implementing or running a generic DMG release workflow. Read [references/verification-troubleshooting.md](references/verification-troubleshooting.md) when auditing an artifact, interpreting a failure, or designing release checks.

## Credentials and operational safety

- Prefer an existing Keychain profile or project-native credential store. For `notarytool`, use `store-credentials` interactively by omitting `--password`; do not put an app-specific password in shell history, logs, source control, screenshots, or chat.
- API keys and certificate private keys are secrets. Never print or copy their contents. Validate access without exposing them.
- Use a unique temporary working directory. Track mounted volumes and detach them on exit. Delete only a validated task-owned temporary path; preserve failed artifacts and logs when they aid diagnosis.
- Do not disable Gatekeeper, remove quarantine, weaken Hardened Runtime, add broad entitlements, or bypass a failed security check to make a release pass.
- Recheck current Apple documentation and local CLI help before changing a long-lived pipeline; tool names, flags, and platform behavior can change.
