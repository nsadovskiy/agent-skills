# agent-skills

This repository is a collection of reusable “skills” for code-assistant tooling, intended for use with OpenAI Codex CLI and Anthropic Claude Code.

Each skill lives in its own folder and is documented by a `SKILL.md` entrypoint (with workflow, commands, and references).

## Skills

- [`go-service-hexagonal`](go-service-hexagonal/SKILL.md): Define, review, and scaffold Go service directory structures using hexagonal (ports-and-adapters) architecture and Go best practices.

## Using the Skills

- Copy the skill folder(s) into `~/.codex/skills/` so they’re discoverable at startup.
- Open the skill’s `SKILL.md` and follow the workflow for that task.

## Contributing

- Keep skill docs short and actionable; put deeper guidance in `references/`.
- Prefer scripts in `scripts/` for repeatable scaffolding/automation.
- Update the skill’s `SKILL.md` (and `references/index.md` when applicable) whenever you add or change behavior.

## License

MIT — see `LICENSE`.
