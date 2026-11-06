# Project Agent Guide Template

Use [AGENTS.template.md](AGENTS.template.md) to create the root `AGENTS.md` for a new repository or to shorten an existing guide. Replace placeholders and omit sections that have no project-specific information.

- Keep boundaries that affect routine decisions in the root guide. Include the affected-target check and any required safety or approval gate.
- Use a task, path, or operation as the trigger for each reference. Read only the references that match the work. A link to an ordinary Markdown file requires an explicit read.
- Reuse the README, existing design decisions, workflow scripts, and skills as sources of truth. A scoped `AGENTS.md` supplements the root guide for local rules. Keep a root route for high-risk work that may start from the repository root.
- If a repository already uses Claude Code, it can share the root guide through `@AGENTS.md` in `CLAUDE.md`. Keep host-specific instructions there only if they are required.
- Verify each path and command before keeping it. Keep machine paths, credentials, private evidence, and personal notification settings outside the template. Start a new session to check instruction discovery.

See [AGENTS.md discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md) and [skill loading](https://learn.chatgpt.com/docs/build-skills).
