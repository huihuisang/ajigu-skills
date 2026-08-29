---
name: xcode-cloud-setup
description: Audit, configure, update, and verify Xcode Cloud workflows for Apple-platform projects using asc. Use for repository readiness, workflow triggers and toolchains, TestFlight or App Store build eligibility, and Xcode Cloud build diagnosis; do not use for ordinary local Xcode builds.
---

# Xcode Cloud Setup

Treat an Xcode Cloud pipeline as three connected configuration planes:

1. The repository supplies a shared scheme, signing settings, capabilities, and optional `ci_scripts` hooks.
2. App Store Connect stores the workflow trigger, toolchain, clean-build policy, and actions.
3. The archive audience determines where the resulting build can be distributed.

Audit all three before proposing a change. Do not copy identifiers, team values, paths, or secrets from another project.

## Core invariant

Use `APP_STORE_ELIGIBLE` at archive time whenever a build may need external TestFlight testing or App Store submission. An `INTERNAL_ONLY` build cannot later be promoted to an external group; changing the workflow affects only future builds.

TestFlight group assignment and beta review are separate from archive eligibility. Do not describe a successful archive as externally distributed until the build and group state confirm it.

## Authorization boundary

Perform repository inspection and `asc` list/view operations without extra approval. Before creating, updating, enabling, disabling, deleting, or triggering a workflow—or distributing a build—show the proposed change and obtain authorization unless the user already explicitly requested that mutation.

Never expose secret environment-variable values. If a web-session command requires renewed login or 2FA, report that requirement; do not work around it or store credentials in the repository.

## Audit workflow

1. Read the applicable repository instructions and preserve unrelated changes.
2. Resolve the app dynamically with `asc`; do not assume an App ID from the bundle identifier alone.
3. Run `scripts/audit.sh APP_SELECTOR [WORKFLOW_ID]` for a concise public-API snapshot.
4. Inspect the repository for shared schemes, project/workspace paths, automatic signing, entitlements, and `ci_scripts` hooks.
5. Classify every finding as repository, workflow, or distribution state so the proposed fix targets the correct plane.

The audit script is read-only. When multiple workflows exist, pass the intended workflow ID to collect its repository, latest run, and produced build details.

## Configure or update

Read [references/setup.md](references/setup.md) before creating or changing a workflow. Use `asc` for App Store Connect operations and query `asc schema --pretty ciWorkflows` before generating a create or update payload. Prefer the public API commands under `asc xcode-cloud`; use `asc web xcode-cloud` only for fields the public API does not expose and only with an authorized user session.

Keep repository hooks minimal and conditional. For example, only add Swift package macro trust configuration when the project actually uses package macros and Cloud builds fail fingerprint validation.

## Verify the outcome

After a workflow mutation:

1. Read the workflow back with `asc xcode-cloud workflows view` and confirm its repository.
2. Trigger a run only when authorized, then wait for a terminal state.
3. Read the run's builds and require the expected `buildAudienceType` and `processingState`.
4. For external TestFlight, separately verify group assignment and beta review state.
5. Stop after a failed run and diagnose its actions and issues before retrying. Do not create retry loops.

Read [references/troubleshooting.md](references/troubleshooting.md) when a workflow, archive, signing step, or TestFlight handoff fails.

Report server-side changes, repository changes, verification evidence, and any fields that could not be inspected. Do not claim success from configuration writes or archive completion alone.
