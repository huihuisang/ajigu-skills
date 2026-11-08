# Project Agent Guide

## Required Constraints

- Read the relevant implementation and tests first. Reuse the project's existing patterns and keep the change scoped to the request.
- Preserve existing work and staging. Commit only verified changes for the current task. Push only when the user explicitly requests it for the current change.
- Keep credentials, private environment values, and personal data out of logs, commits, and generated output. Obtain explicit authorization before a live deployment, production write, or release.
- Keep disposable build outputs, logs, and captures outside the repository. Keep source assets and durable test fixtures with the project when required.

## Verification

- Use the repository's documented commands and checks for the affected target. For prose-only changes, check the diff and edited links. For behavior changes, verify the normal path and relevant failure cases.
- Report the checks that actually ran and distinguish local results from simulator, device, browser, or live service evidence.

## Read for This Task

- Read the nearest project guide or the existing documentation for the affected subsystem before changing its contracts. Read build or release guides when the task needs that workflow.
