# Project Agent Guide Template

Copy [AGENTS.template.md](AGENTS.template.md) to the root `AGENTS.md` of a new repository, or merge its rules into an existing guide. The base works as written. Add a short project scope and the actual check commands when the repository has them.

Copy each applicable guide below to `.agents/guides/` in the destination repository. Add the matching line under **Read for This Task**. If the repository already has an authoritative guide for that work, merge the applicable rules there and link to it.

| Copy this guide | Add this route |
| --- | --- |
| [apple-app.md](guides/apple-app.md) | Apple builds, simulator or device checks, localization, or signing → `[Apple app workflow](.agents/guides/apple-app.md)` |
| [web-app.md](guides/web-app.md) | Website UI, browser checks, SEO, or public output → `[Web app workflow](.agents/guides/web-app.md)` |
| [release-and-data.md](guides/release-and-data.md) | Release, deployment, credentials, persistent data, or migrations → `[Release and data workflow](.agents/guides/release-and-data.md)` |

- Keep boundaries that affect routine decisions in the root guide. Include the affected-target check and any required safety or approval gate.
- Use a task, path, or operation as the trigger for each reference. Read only the references that match the work. A link to an ordinary Markdown file requires an explicit read.
- Reuse the README, existing design decisions, workflow scripts, and skills as sources of truth. A scoped `AGENTS.md` supplements the root guide for local rules. Keep a root route for high-risk work that may start from the repository root.
- If a repository already uses Claude Code, it can share the root guide through `@AGENTS.md` in `CLAUDE.md`. Keep host-specific instructions there only if they are required.
- Verify project-specific paths, schemes, supported locales, and commands before listing them. Keep machine paths, credentials, private evidence, and personal notification settings outside the template. Start a new session to check instruction discovery.

See [AGENTS.md discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md) and [skill loading](https://learn.chatgpt.com/docs/build-skills).
