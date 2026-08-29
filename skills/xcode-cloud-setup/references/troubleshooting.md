# Xcode Cloud Troubleshooting

Use the smallest diagnostic surface that identifies which configuration plane failed.

## A build cannot be selected for an external TestFlight group

Read the build produced by the run:

```sh
asc xcode-cloud build-runs builds --run-id "$RUN_ID" --output json
```

If `buildAudienceType` is `INTERNAL_ONLY`, the build is permanently ineligible for external TestFlight and App Store submission. Update the archive action to `APP_STORE_ELIGIBLE` and create a new build. Do not keep retrying group assignment for the existing build.

If the audience is correct, inspect TestFlight processing, export compliance, group assignment, and beta review state separately.

## Swift package macro validation blocks the build

Only when the project uses trusted package macros and the issue is macro fingerprint validation, add this to an executable `ci_scripts/ci_post_clone.sh`:

```sh
#!/bin/sh

defaults write com.apple.dt.Xcode IDESkipMacroFingerprintValidation -bool YES
```

Do not add the workaround preemptively to projects that do not use package macros.

## The scheme or container is unavailable

Confirm that the workflow's `containerFilePath` exists at the repository root expected by Xcode Cloud. Ensure the scheme is shared and committed. Generated user schemes and files under `xcuserdata` are not reliable Cloud inputs.

## Signing or capability validation fails

Inspect the archive action issues before changing signing. Verify the app's bundle ID, team, automatic-signing policy, entitlements, extension identifiers, and App Store Connect capabilities agree. Do not remove capabilities merely to make an archive pass when the product requires them.

## Archive succeeds but no usable TestFlight build appears

Check the run's related builds and their processing state. A completed archive action is not the end of App Store Connect processing. Also inspect encryption declarations, bundle validation issues, and whether the workflow includes the intended distribution behavior.

## A web-session inspection asks for 2FA

Public API operations under `asc xcode-cloud` use App Store Connect API authentication and can continue when supported. Web-only commands require an authorized Apple Account session. Ask the user to log in interactively; never place a password or 2FA code in a script, tracked file, shell history, or report.

## The latest run was automatically cancelled

When `autoCancel` is enabled, a newer matching commit can cancel an obsolete run. Inspect the newest run before treating cancellation as a workflow failure. Do not disable automatic cancellation unless the user values completion of every queued commit over Cloud-minute usage.

## Diagnostic commands

```sh
asc xcode-cloud build-runs view --id "$RUN_ID" --output json
asc xcode-cloud actions --run-id "$RUN_ID" --output table
asc xcode-cloud issues list --run-id "$RUN_ID" --output table
asc xcode-cloud artifacts list --run-id "$RUN_ID" --output table
```

After a failure, explain the failing plane and evidence before proposing a mutation. Retry only after a specific corrective change or an identified transient condition.
