# Base Go Service Layout (Hexagonal)

This layout fits most Go services and supports HTTP, gRPC, workers, and CLIs by adding binaries under `cmd/`.

## Directory tree (template)

```text
.
├── AGENTS.md                     # Required: agent/coding instructions for this repo
├── Makefile                      # Required: build/run/test entrypoints
├── README.md                     # Required: how to build/run and what it provides
├── cmd/
│   └── <service>-<binary>/
│       └── main.go
├── internal/
│   └── <service>/
│       ├── domain/                 # Entities, value objects, domain services, invariants
│       ├── app/                    # Use cases (application services)
│       ├── port/
│       │   ├── in/                 # Inbound ports (interfaces used by primary adapters)
│       │   └── out/                # Outbound ports (interfaces required by app)
│       ├── adapter/
│       │   ├── in/                 # Primary adapters (http, grpc, cli, consumer)
│       │   └── out/                # Secondary adapters (db, queue, cache, httpclient)
│       └── bootstrap/              # Wiring: construct app + adapters; config; lifecycle
├── test/                           # Integration tests (e.g., health endpoints)
```

## Create when needed (optional top-level folders)

```text
api/                                # OpenAPI/proto (create only for HTTP/gRPC contracts)
configs/                            # Default configs; example env files
deploy/                             # Docker/K8s/helm/terraform manifests
migrations/                         # DB migrations
scripts/                            # Dev scripts (lint, gen, local run)
tools/                              # Tooling modules / codegen helpers
```

## Naming conventions

- Name each deployable binary folder: `cmd/<service>-api`, `cmd/<service>-grpc`, `cmd/<service>-worker`, `cmd/<service>-cli`.
- Prefer `<service>` as a stable domain name (e.g., `billing`, `payments`, `catalog`) rather than transport names.
- Avoid generic packages like `util`/`common`; create a focused package name or keep code close to its consumer.

## Go-specific notes

- Keep most code under `internal/` to prevent accidental reuse across repos.
- Use `pkg/` only for code that is intentionally reusable by external modules/repos.
- Keep `cmd/*` thin: parse config, set up logging/tracing, call `bootstrap`, run.

## Logging

- Standardize on Logrus (`github.com/sirupsen/logrus`) for structured logs.
- Provide `internal/<service>/bootstrap.NewLogger()` and pass the logger into adapters (HTTP) and long-running loops (workers).
