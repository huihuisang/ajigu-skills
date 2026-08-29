# Xcode Cloud Setup Reference

Use this reference when creating or updating an Xcode Cloud workflow. Keep values project-specific and discover them at runtime.

## Repository readiness

Confirm the following before changing App Store Connect:

- The selected `.xcodeproj` or `.xcworkspace` is committed and opens without generated local-only dependencies.
- The intended scheme is shared and committed under `xcshareddata/xcschemes`.
- Release builds use valid signing settings and the required capabilities and entitlements.
- Swift package dependencies resolve without interactive prompts.
- Secrets are stored as Xcode Cloud environment variables, not in source control.
- Repository hooks use Xcode Cloud's conventional names: `ci_post_clone.sh`, `ci_pre_xcodebuild.sh`, and `ci_post_xcodebuild.sh`.
- Hook files are executable, non-interactive, and fail clearly when a required command fails.

Do not create an Xcode Cloud manifest by copying product or target IDs from another project. Treat an existing manifest as server-linked project data and preserve it unless the current project regenerates it intentionally.

## Discover the server model

Use the public API first:

```sh
asc auth doctor
asc xcode-cloud products list --app "$APP_SELECTOR" --paginate --output json
asc xcode-cloud workflows list --app "$APP_SELECTOR" --paginate --output json
asc xcode-cloud scm repositories list --paginate --output json
asc xcode-cloud xcode-versions list --paginate --output json
asc xcode-cloud macos-versions list --paginate --output json
asc schema --pretty ciWorkflows
```

For an existing workflow:

```sh
asc xcode-cloud workflows view --id "$WORKFLOW_ID" --output json
asc xcode-cloud workflows repository --id "$WORKFLOW_ID" --output json
```

The public workflow response may omit linked toolchain details or shared environment-variable metadata. When those fields matter and the user has an authorized web session, inspect them with:

```sh
asc web xcode-cloud workflows describe \
  --product-id "$PRODUCT_ID" \
  --workflow-id "$WORKFLOW_ID" \
  --output table
```

If the session is expired, stop the web-only inspection and ask the user to renew it interactively. Public API inspection can continue.

## Design the workflow

Choose each setting from the requested release outcome:

- Use a branch trigger for continuous integration on a stable integration branch.
- Enable automatic cancellation when obsolete runs should not consume Cloud minutes.
- Use a clean build when reproducibility matters more than incremental speed.
- Select the actual committed project/workspace and shared scheme.
- Mark the archive action required to pass.
- Use `APP_STORE_ELIGIBLE` if any future external TestFlight or App Store use is possible.
- Use `INTERNAL_ONLY` only when the user explicitly wants a permanently internal artifact.
- Select compatible Xcode and macOS version IDs returned by `asc`, not display names guessed from local Xcode.

An App Store Connect API create payload follows this shape. Resolve every ID and re-check the runtime schema before writing the file:

```json
{
  "data": {
    "type": "ciWorkflows",
    "attributes": {
      "name": "TestFlight - Main",
      "description": "Archive the main branch for TestFlight distribution.",
      "branchStartCondition": {
        "source": {
          "patterns": [
            {
              "pattern": "main"
            }
          ]
        },
        "autoCancel": true
      },
      "actions": [
        {
          "name": "Archive - iOS",
          "actionType": "ARCHIVE",
          "buildDistributionAudience": "APP_STORE_ELIGIBLE",
          "scheme": "App",
          "platform": "IOS",
          "isRequiredToPass": true
        }
      ],
      "isEnabled": true,
      "clean": true,
      "containerFilePath": "App.xcodeproj"
    },
    "relationships": {
      "product": {
        "data": {
          "type": "ciProducts",
          "id": "resolved-product-id"
        }
      },
      "repository": {
        "data": {
          "type": "scmRepositories",
          "id": "resolved-repository-id"
        }
      },
      "xcodeVersion": {
        "data": {
          "type": "ciXcodeVersions",
          "id": "resolved-xcode-version-id"
        }
      },
      "macOsVersion": {
        "data": {
          "type": "ciMacOsVersions",
          "id": "resolved-macos-version-id"
        }
      }
    }
  }
}
```

Show the resolved plan to the user before applying it. Then use:

```sh
asc xcode-cloud workflows create --file "$PAYLOAD_FILE" --output json
asc xcode-cloud workflows update --id "$WORKFLOW_ID" --file "$PAYLOAD_FILE" --output json
```

For updates, include only intended mutable attributes and supported toolchain relationships. The public API does not treat product and repository relationships as ordinary patch fields.

## Verify a workflow and build

Read the workflow back after any mutation. If the user authorized a test run:

```sh
asc xcode-cloud run \
  --workflow-id "$WORKFLOW_ID" \
  --git-reference-id "$GIT_REFERENCE_ID"

asc xcode-cloud status --run-id "$RUN_ID" --wait
asc xcode-cloud actions --run-id "$RUN_ID" --output table
asc xcode-cloud build-runs builds --run-id "$RUN_ID" --output json
```

For an App Store-eligible workflow, require the produced build to report:

- `processingState` equal to `VALID` after processing completes.
- `buildAudienceType` equal to `APP_STORE_ELIGIBLE`.

External TestFlight still requires a separate group association and, when applicable, beta app review approval.
