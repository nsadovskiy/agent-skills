# HTTP REST/JSON Service Layout

Use this when the primary interface is HTTP/REST (or HTTP+JSON RPC) and you want a `net/http` baseline.

If you prefer Echo, use `references/layout-http-echo.md`.

## Additions to base layout

```text
cmd/
  <service>-api/
    main.go
internal/
  adapter/in/http/
    handlers/            # Request handlers, DTO mapping, validation
    middleware/          # Authn/z, request IDs, timeouts, logging
    router.go            # Routes → handlers
  adapter/in/debughttp/  # Optional: pprof/trace handler mux (served on separate debug server)
  bootstrap/
    http.go              # Build router, server options, graceful shutdown
api/openapi/
  <service>.yaml         # Optional but recommended
```

## Common inbound port pattern

- Define inbound ports in `internal/port/in` as small interfaces per use case.
- Implement them in `internal/app`.
- HTTP handlers depend on `port/in` (not on concrete `app` types).

## Common outbound adapters

```text
internal/adapter/out/
  postgres/
  redis/
  httpclient/
```

Define interfaces in `internal/port/out`, implement in `adapter/out/*`, and inject into `app/*`.

## Ops endpoints + logging

- Expose `GET /health/live` and `GET /health/ready` from the HTTP adapter (keep them fast and dependency-light).
- Add profiling endpoints only when needed (opt-in) and serve them from a separate debug server (set `PPROF_PORT`, optional `PPROF_ADDR`).
- Use Logrus (`github.com/sirupsen/logrus`) for structured request logging via adapter middleware.

## Scaffolding

Generate a net/http baseline with:

`python3 scripts/scaffold_hex_service.py --root <repo> --service <name> --kinds http --http-framework nethttp`

Optional debug endpoints:

- Add pprof: append `--http-pprof`
- Add trace: append `--http-trace`
- Enable the debug server: set `PPROF_PORT` (and optional `PPROF_ADDR`, default `127.0.0.1`)
