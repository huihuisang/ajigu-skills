# macOS Direct Distribution

Prepare and inspect a Developer ID-signed macOS app delivered in a DMG. The workflow connects signing, notarization, stapling, packaged-app checks, and a real download test so that release evidence describes the artifact users receive.

## Install

Ask your Agent: "Install macos-direct-distribution from https://github.com/huihuisang/ajigu-skills."

```bash
npx skills add huihuisang/ajigu-skills -g -y --skill macos-direct-distribution
```

Or copy the complete skill directory into your host's skill directory. Node.js and network access are needed only for the command installation method.

## Configuration and requirements

Requires macOS, the project's supported Xcode toolchain, and Apple command-line tools. Actual signing needs an authorized Developer ID identity with its private key. Notarization needs an existing Keychain profile or project-native authentication and access to Apple's service. No custom API-key configuration page is provided: use Apple's interactive credential tooling or the project's established authentication entry point.

Review the selected toolchain's help before using example commands. No new credential, certificate, or signing setting is created automatically.

## Usage and output

Request: "Review our DMG release workflow and identify missing verification gates."

For a release request, the outputs are the final DMG and evidence covering source revision, signatures, notarization status, ticket, hashes, and the actual user path. The [manual workflow](references/manual-workflow.md) and [troubleshooting guide](references/verification-troubleshooting.md) contain focused instructions.

## Security and privacy

Notarization uploads the selected distribution artifact to Apple. Publishing to any other service requires authorization for that destination. Keep private keys, passwords, and API-key files out of source, logs, and release evidence. A build request alone does not authorize publication.

This skill covers direct distribution, not Mac App Store submission. No real signing, paid account operation, notarization upload, or fresh-Mac installation is exercised by this repository's publication checks; these must be verified for each release.

## Validation and troubleshooting

Check Markdown resource links and inspect command syntax against the selected tools. A successful build or an Accepted notarization status does not prove the complete user path. Use the documented gates and report tests that remain pending.
