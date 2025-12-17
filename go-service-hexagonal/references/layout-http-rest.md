# HTTP REST/JSON Service Layout

Use this when the primary interface is HTTP/REST (or HTTP+JSON RPC) and you want a `net/http` baseline.

If you prefer Echo, use `references/layout-http-echo.md`.

## Additions to base layout

```text
cmd/
  <service>-api/
    main.go
internal/<service>/
  adapter/in/http/
    handlers/            # Request handlers, DTO mapping, validation
    middleware/          # Authn/z, request IDs, timeouts, logging
    router.go            # Routes → handlers
  bootstrap/
    http.go              # Build router, server options, graceful shutdown
api/openapi/
  <service>.yaml         # Optional but recommended
```

## Common inbound port pattern

- Define inbound ports in `internal/<service>/port/in` as small interfaces per use case.
- Implement them in `internal/<service>/app`.
- HTTP handlers depend on `port/in` (not on concrete `app` types).

## Common outbound adapters

```text
internal/<service>/adapter/out/
  postgres/
  redis/
  httpclient/
```

Define interfaces in `internal/<service>/port/out`, implement in `adapter/out/*`, and inject into `app/*`.

## Ops endpoints + logging

- Expose `GET /health/live` and `GET /health/ready` from the HTTP adapter (keep them fast and dependency-light).
- Use Logrus (`github.com/sirupsen/logrus`) for structured request logging via adapter middleware.

## Scaffolding

Generate a net/http baseline with:

`python3 scripts/scaffold_hex_service.py --root <repo> --service <name> --kinds http --http-framework nethttp`
