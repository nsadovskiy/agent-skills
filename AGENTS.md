# Repository Guidelines

## Project Structure & Module Organization

- Skill packages live at the repo root (e.g. `go-service-hexagonal/`).
- Each skill directory should contain:
  - `SKILL.md`: the entrypoint with YAML frontmatter (`name`, `description`) and a clear workflow.
  - `references/`: small, task-focused Markdown docs (include an `index.md` when there are multiple).
  - `scripts/`: helper tooling (scaffolders, validators) invoked from `SKILL.md`.

## Build, Test, and Development Commands

- `python3 go-service-hexagonal/scripts/scaffold_hex_service.py --help`: show scaffolder options.
- `python3 go-service-hexagonal/scripts/scaffold_hex_service.py --root /tmp/my-svc --service billing --kinds http,worker --skip-deps`: generate a sample service tree without downloading Go deps (useful in restricted/offline environments).
- `rg "TODO|FIXME" -n`: quick scan for unfinished work.

## Coding Style & Naming Conventions

- Markdown: keep headings descriptive, prefer short sections, and use fenced code blocks for commands.
- Skill naming: use kebab-case for directory names and keep `SKILL.md` `name:` aligned (e.g. `go-service-hexagonal`).
- Python scripts: 4-space indentation, type hints where practical, prefer `pathlib.Path`, and avoid side effects at import time (put work under `main()`).

## Testing Guidelines

- This repo currently has no shared test runner.
- If you add tests for a script, keep them close to the skill (e.g. `go-service-hexagonal/tests/`) and document how to run them in that skill’s `SKILL.md`.

## Commit & Pull Request Guidelines

- Git history is minimal (“Initial commit”), so no established convention yet.
- Prefer short, imperative commit subjects; Conventional Commits are welcome (e.g. `feat(go-service-hexagonal): add grpc layout`).
- PRs should include: a brief summary, rationale, updated docs (`SKILL.md` and/or `references/index.md`), and an example command demonstrating the change (plus expected output/tree if relevant).

## Agent-Specific Notes

- Skills are expected to be discoverable from `~/.codex/skills`; during local development, symlinking this repo (or individual skill folders) there keeps iteration fast.
- Keep `SKILL.md` instructions “progressively disclosed”: link to `references/` instead of pasting long guidance inline.
