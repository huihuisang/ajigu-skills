# Ajigu Skills Agent Guide

## Project Scope

This repository owns the reusable skills, plugin manifests, and [project guide template](templates/README.md).

## Required Constraints

- Push only when the user explicitly requests it for the current change.
- Keep credentials, machine-specific configuration, and private project inventories out of this public repository.
- Keep Codex and Claude plugin manifests aligned when changing bundled skills. Follow the versioning instructions before a bundle release.

## Verification

- Run `python3 scripts/validate_plugins.py` for plugin metadata changes. Use the existing skill-specific tests for changes to a skill or tool.

## Read for This Task

- Installation and distribution changes → [README](README.md).
- Template or agent routing changes → [template guide](templates/README.md) and [design record](docs-ai/004-agent-harness/000-plan.md).
