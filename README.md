# agent-skills

This repository is a collection of reusable “skills” for code-assistant tooling, intended for use with OpenAI Codex CLI and Anthropic Claude Code.

Each skill lives in its own folder and is documented by a `SKILL.md` entrypoint (with workflow, commands, and references).

## Skills

- [`go-service-hexagonal`](go-service-hexagonal/SKILL.md): Define, review, and scaffold Go service directory structures using hexagonal (ports-and-adapters) architecture and Go best practices.
- [`m4b-audiobook-builder`](m4b-audiobook-builder/SKILL.md): Build and merge M4B audiobooks from mixed audio files or multi-part M4B sets with chapter generation, metadata normalization, UTF-8 handling, and validation.

## Ubuntu Dependencies

Install the following apt packages to use the M4B audiobook skill on Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y \
  ffmpeg \
  libimage-exiftool-perl \
  atomicparsley \
  mp4v2-utils \
  gpac \
  mediainfo \
  bento4 \
  convmv \
  python3-mutagen
```

## Using the Skills

- Copy the skill folder(s) into `~/.codex/skills/` so they’re discoverable at startup.
- Open the skill’s `SKILL.md` and follow the workflow for that task.

## Contributing

- Keep skill docs short and actionable; put deeper guidance in `references/`.
- Prefer scripts in `scripts/` for repeatable scaffolding/automation.
- Update the skill’s `SKILL.md` (and `references/index.md` when applicable) whenever you add or change behavior.

## License

MIT — see `LICENSE`.
