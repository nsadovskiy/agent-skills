# gRPC Service Layout

Use this when the primary interface is gRPC.

## Additions to base layout

```text
cmd/
  <service>-grpc/
    main.go
api/proto/
  <service>/
    v1/
      <service>.proto
internal/
  adapter/in/grpc/
    server.go            # gRPC server registration and request mapping
    interceptors/        # Authn/z, logging, metrics, tracing
  bootstrap/
    grpc.go              # Build gRPC server, register services, lifecycle
```

## Protobuf + generated code conventions

- Keep IDL in `api/proto/...`.
- Place generated Go code either:
  - next to IDL (common in small repos), or
  - under `internal/adapter/in/grpc/gen/...` (keeps `internal/` encapsulation).

Pick one and keep it consistent.

## Port mapping

- `adapter/in/grpc` depends on `port/in` and maps protobuf DTOs ↔ domain types.
- Keep business validation in `domain`/`app` rather than in protobuf handlers.
