# Release and Data Workflow

- Test against isolated fixtures or a local environment. Keep real user files, production data, live credentials, and test state separate.
- Preserve existing data and compatibility. Before a schema or storage change, identify how older data loads, how partial failure is handled, and how recovery is verified.
- Before an authorized release or deployment, confirm the exact target, source revision, artifact, and environment. If synchronization changes the candidate, repeat the relevant checks.
- Publish through the project's documented entry point. Check the resulting revision or artifact at the destination and report build, upload, distribution, and deployment as separate states.
