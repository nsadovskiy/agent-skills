# Hexagonal Dependency Rules (Go)

Use this as a checklist when reviewing or proposing a directory structure.

## Allowed dependencies (high level)

- `domain` depends on nothing in the service (only standard library or small pure helpers).
- `app` depends on `domain` and `port/out`.
- `port/in` and `port/out` depend on `domain` types as needed.
- `adapter/in/*` depends on `port/in` and `domain` (DTO mapping).
- `adapter/out/*` depends on `port/out` and `domain` (persistence/message mapping).
- `bootstrap` depends on everything to wire it together.
- `cmd/*` depends on `bootstrap` (and minimal infra like `os`, `signal`, config parsing).

## Single composition root

- Centralize DI in `internal/<service>/bootstrap.Compose()` (one place to construct and inject dependencies).

## Keep interfaces at the boundary

- Define inbound interfaces where adapters need them (`port/in`).
- Define outbound interfaces where the app needs them (`port/out`).
- Avoid “interface soup”: keep ports small and focused on a single use case or capability.

## Common structure smells

- `domain` importing `adapter/*` or transport packages.
- `cmd/*` importing `adapter/*` directly (skip bootstrap).
- A `common` or `utils` package that accumulates unrelated helpers.
- Repository packages that return transport DTOs instead of domain/application types.
