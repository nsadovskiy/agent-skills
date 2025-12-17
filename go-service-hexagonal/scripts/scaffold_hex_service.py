#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


GO_VERSION = "1.25"


@dataclass
class Options:
    root: Path
    module: str | None
    service: str
    kinds: tuple[str, ...]
    http_framework: str
    skip_deps: bool


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    _write(path, content)


def _maybe_write_go_mod(root: Path, module: str | None) -> bool:
    if module is None:
        return False
    go_mod = root / "go.mod"
    if go_mod.exists():
        return False
    _write(
        go_mod,
        f"module {module}\n\ngo {GO_VERSION}\n",
    )
    return True


def _install_deps_for_new_project(root: Path) -> None:
    env = os.environ.copy()
    env["GOCACHE"] = str(root / ".gocache")
    env["GOMODCACHE"] = str(root / ".gomodcache")

    try:
        proc = subprocess.run(
            ["go", "mod", "tidy"],
            cwd=root,
            env=env,
            check=False,
        )
    except FileNotFoundError:
        print("⚠️  go not found; skipping dependency install")
        return

    if proc.returncode != 0:
        print("⚠️  go mod tidy failed (likely no network access); run `go mod tidy` later in an online environment.")

def _discover_module_from_go_mod(root: Path) -> str | None:
    go_mod = root / "go.mod"
    if not go_mod.exists():
        return None
    for line in go_mod.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("module "):
            return line.removeprefix("module ").strip()
    return None


def _svc(root: Path, service: str) -> Path:
    return root / "internal" / service


def _base_tree(opt: Options) -> None:
    required = [
        f"internal/{opt.service}/domain",
        f"internal/{opt.service}/app",
        f"internal/{opt.service}/port/in",
        f"internal/{opt.service}/port/out",
        f"internal/{opt.service}/adapter/in",
        f"internal/{opt.service}/adapter/out",
        f"internal/{opt.service}/bootstrap",
    ]
    if "grpc" in opt.kinds:
        required.append(f"api/proto/{opt.service}/v1")
    if "http" in opt.kinds:
        required.append("test")

    for rel in required:
        (opt.root / rel).mkdir(parents=True, exist_ok=True)

    _write_project_docs(opt)

    _write(
        _svc(opt.root, opt.service) / "domain" / "doc.go",
        f"package domain\n\n// Package domain contains core business rules for the {opt.service} service.\n",
    )
    _write(
        _svc(opt.root, opt.service) / "app" / "doc.go",
        f"package app\n\n// Package app contains use cases for the {opt.service} service.\n",
    )
    _write(
        _svc(opt.root, opt.service) / "bootstrap" / "doc.go",
        f"package bootstrap\n\n// Package bootstrap wires adapters and use cases for the {opt.service} service.\n",
    )
    _write_bootstrap_compose(opt)


def _write_project_docs(opt: Options) -> None:
    binaries = []
    for kind in opt.kinds:
        if kind == "http":
            binaries.append(f"- `cmd/{opt.service}-api`: HTTP server (Echo default)")
        elif kind == "grpc":
            binaries.append(f"- `cmd/{opt.service}-grpc`: gRPC server")
        elif kind == "worker":
            binaries.append(f"- `cmd/{opt.service}-worker`: background worker")
        elif kind == "cli":
            binaries.append(f"- `cmd/{opt.service}-cli`: CLI")

    binaries_block = "\n".join(binaries) if binaries else "- (none scaffolded)"

    _write_if_missing(
        opt.root / "README.md",
        f"""# {opt.service}

Go service scaffold using hexagonal (ports-and-adapters) architecture.

## Binaries

{binaries_block}

## Health endpoints (HTTP)

- `GET /health/live`
- `GET /health/ready`

## Local run (HTTP)

```bash
go run ./cmd/{opt.service}-api
```

Environment:

- `HTTP_ADDR` (default `:8080`)
- `LOG_LEVEL` (e.g. `info`, `debug`)
""",
    )

    _write_if_missing(
        opt.root / "AGENTS.md",
        f"""# Agent Instructions

This repository follows Go best practices and hexagonal (ports-and-adapters / “jexagonal”) architecture.

## Architecture (hexagonal)

**Dependency rule (must hold):**

- `internal/{opt.service}/domain` depends on nothing in the service (only stdlib / pure helpers).
- `internal/{opt.service}/app` depends on `domain` and `port/out`.
- `internal/{opt.service}/port/in` and `internal/{opt.service}/port/out` define interfaces at the boundaries.
- `internal/{opt.service}/adapter/in/*` depends on `port/in` (+ domain types for mapping).
- `internal/{opt.service}/adapter/out/*` depends on `port/out` (+ domain types for mapping).
- **All wiring happens only in the composition root**: `internal/{opt.service}/bootstrap/compose.go` (`bootstrap.Compose()`).
- `cmd/*` is a thin entrypoint: read env/config, call `bootstrap.Compose()`, start servers/loops, handle shutdown.

**Design guidance:**

- Keep ports small and use-case focused; avoid “interface soup”.
- Keep transport/ORM/SDK types out of `domain` and `app` (map in adapters).
- Prefer explicit package names over generic `util`/`common`.

## Project structure (all supported shapes)

The scaffolder creates only what you asked for, but these are the standard directories you may add over time:

```text
.
├── AGENTS.md
├── README.md
├── cmd/
│   ├── {opt.service}-api/          # HTTP server (Echo default)
│   ├── {opt.service}-grpc/         # gRPC server (optional)
│   ├── {opt.service}-worker/       # worker/consumer/scheduler (optional)
│   └── {opt.service}-cli/          # CLI tool (optional)
├── internal/
│   └── {opt.service}/
│       ├── domain/                 # Entities/value objects/invariants
│       ├── app/                    # Use-cases (application services)
│       ├── port/
│       │   ├── in/                 # Inbound ports (interfaces)
│       │   └── out/                # Outbound ports (interfaces)
│       ├── adapter/
│       │   ├── in/                 # HTTP/gRPC/CLI/worker adapters
│       │   └── out/                # DB/queue/cache/httpclient adapters
│       └── bootstrap/
│           └── compose.go           # Single DI composition root
├── api/                            # Create only when you have contracts
│   ├── openapi/                    # OpenAPI specs (HTTP)
│   └── proto/                      # Protobuf IDL (gRPC)
├── configs/                        # Default configs / examples (optional)
├── deploy/                         # Docker/K8s/helm/terraform (optional)
├── migrations/                     # DB migrations (optional)
├── scripts/                        # Dev scripts (optional)
├── tools/                          # Codegen/tools helpers (optional)
├── pkg/                            # Public/reusable packages (rare; opt-in)
└── test/                           # Integration tests (package `test`)
```

## Composition root (DI)

- Put **all construction/injection** in `internal/{opt.service}/bootstrap/compose.go`.
- `bootstrap.Compose()` returns a `Root` struct that holds initialized dependencies (logger, servers, clients, repos).
- Adapters should be constructed with explicit dependencies (interfaces), not by reaching into globals.

## HTTP (when present)

- Expose only health endpoints by default:
  - `GET /health/live`
  - `GET /health/ready`
- Keep health handlers fast and dependency-light.
- Request logging must be enabled (Logrus-backed).

## Logging

- Use Logrus (`github.com/sirupsen/logrus`) for structured logs.
- Prefer fields (`WithField(s)`) over formatted strings.
- Control verbosity with `LOG_LEVEL` (e.g. `info`, `debug`).

## Testing

- Run `go test ./...` before finishing changes.
- Use `test/` (package `test`) for integration-style tests that exercise the composed app via `bootstrap.Compose()`.
- Keep most unit tests next to packages in `internal/...` as `*_test.go`.

## Go hygiene

- Format with `gofmt`.
- Keep imports tidy (`goimports` if available, otherwise `gofmt` + manual cleanup).
- Avoid long-lived contexts without cancellation; respect shutdown signals in `cmd/*`.
""",
    )

    make_run_target = f"{opt.service}-api"
    if "worker" in opt.kinds:
        make_run_target = f"{opt.service}-worker"
    if "http" in opt.kinds:
        make_run_target = f"{opt.service}-api"

    _write_if_missing(
        opt.root / "Makefile",
        f""".PHONY: help tidy fmt test build run

SERVICE ?= {opt.service}
BINARY ?= {make_run_target}

help:
\t@echo \"Targets: tidy fmt test build run\"
\t@echo \"Variables: SERVICE (default $(SERVICE)), BINARY (default $(BINARY))\"

tidy:
\tgo mod tidy

fmt:
\tgofmt -w $$(find . -name '*.go' -not -path './.gomodcache/*' -not -path './.gocache/*')

test:
\tgo test ./...

build:
\tgo build ./...

run:
\tgo run ./cmd/$(BINARY)
""",
    )


def _write_bootstrap_compose(opt: Options) -> None:
    if opt.module is None:
        raise SystemExit("Go module path not set; pass --module or run inside an existing module (go.mod).")

    if "http" in opt.kinds and opt.http_framework == "echo":
        _write(
            _svc(opt.root, opt.service) / "bootstrap" / "compose.go",
            """package bootstrap

import (
	"net/http"
	"os"

	"github.com/labstack/echo/v4"
	"github.com/sirupsen/logrus"

	httpadapter "REPLACE_MODULE/internal/REPLACE_SERVICE/adapter/in/http"
)

// Root is the single composition root for dependency injection.
// Add databases/clients/etc here and wire them into adapters/use-cases.
type Root struct {
	Logger     *logrus.Logger
	HTTPServer *echo.Echo
	HTTPHandler http.Handler
}

func Compose() *Root {
	logger := newLogger()
	srv := httpadapter.New(logger)
	return &Root{
		Logger:     logger,
		HTTPServer: srv,
		HTTPHandler: srv,
	}
}

func newLogger() *logrus.Logger {
	l := logrus.New()
	l.SetOutput(os.Stdout)
	l.SetFormatter(&logrus.JSONFormatter{})
	if lvl, err := logrus.ParseLevel(os.Getenv("LOG_LEVEL")); err == nil {
		l.SetLevel(lvl)
	}
	return l
}
""".replace("REPLACE_SERVICE", opt.service),
        )
        return

    if "http" in opt.kinds and opt.http_framework == "nethttp":
        _write(
            _svc(opt.root, opt.service) / "bootstrap" / "compose.go",
            """package bootstrap

import (
	"net/http"
	"os"

	"github.com/sirupsen/logrus"

	httpadapter "REPLACE_MODULE/internal/REPLACE_SERVICE/adapter/in/http"
)

// Root is the single composition root for dependency injection.
// Add databases/clients/etc here and wire them into adapters/use-cases.
type Root struct {
	Logger     *logrus.Logger
	HTTPHandler http.Handler
}

func Compose() *Root {
	logger := newLogger()
	return &Root{
		Logger:      logger,
		HTTPHandler: httpadapter.Router{Logger: logger}.Handler(),
	}
}

func newLogger() *logrus.Logger {
	l := logrus.New()
	l.SetOutput(os.Stdout)
	l.SetFormatter(&logrus.JSONFormatter{})
	if lvl, err := logrus.ParseLevel(os.Getenv("LOG_LEVEL")); err == nil {
		l.SetLevel(lvl)
	}
	return l
}
""".replace("REPLACE_SERVICE", opt.service),
        )
        return

    _write(
        _svc(opt.root, opt.service) / "bootstrap" / "compose.go",
        """package bootstrap

import (
	"os"

	"github.com/sirupsen/logrus"
)

// Root is the single composition root for dependency injection.
type Root struct {
	Logger *logrus.Logger
}

func Compose() *Root {
	return &Root{Logger: newLogger()}
}

func newLogger() *logrus.Logger {
	l := logrus.New()
	l.SetOutput(os.Stdout)
	l.SetFormatter(&logrus.JSONFormatter{})
	if lvl, err := logrus.ParseLevel(os.Getenv("LOG_LEVEL")); err == nil {
		l.SetLevel(lvl)
	}
	return l
}
""",
    )


def _scaffold_http_nethttp(opt: Options) -> None:
    if opt.module is None:
        raise SystemExit("--module is required when scaffolding --kinds http (Go imports need a module path).")
    (opt.root / "cmd" / f"{opt.service}-api").mkdir(parents=True, exist_ok=True)
    (_svc(opt.root, opt.service) / "adapter" / "in" / "http").mkdir(parents=True, exist_ok=True)
    (_svc(opt.root, opt.service) / "adapter" / "in" / "http" / "middleware").mkdir(parents=True, exist_ok=True)

    _write(
        _svc(opt.root, opt.service) / "adapter" / "in" / "http" / "router.go",
        """package http

import (
	"net/http"

	"github.com/sirupsen/logrus"

	"REPLACE_MODULE/internal/REPLACE_SERVICE/adapter/in/http/middleware"
)

type Router struct {
	Logger logrus.FieldLogger
}

func (r Router) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health/live", func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusOK) })
	mux.HandleFunc("/health/ready", func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusOK) })
	return middleware.RequestLogger(r.Logger, mux)
}
""".replace("REPLACE_SERVICE", opt.service),
    )
    _write(
        _svc(opt.root, opt.service) / "adapter" / "in" / "http" / "middleware" / "logging.go",
        """package middleware

import (
	"net/http"
	"time"

	"github.com/sirupsen/logrus"
)

type statusCapturingResponseWriter struct {
	http.ResponseWriter
	status int
	bytes  int
}

func (w *statusCapturingResponseWriter) WriteHeader(statusCode int) {
	w.status = statusCode
	w.ResponseWriter.WriteHeader(statusCode)
}

func (w *statusCapturingResponseWriter) Write(p []byte) (int, error) {
	if w.status == 0 {
		w.status = http.StatusOK
	}
	n, err := w.ResponseWriter.Write(p)
	w.bytes += n
	return n, err
}

func RequestLogger(logger logrus.FieldLogger, next http.Handler) http.Handler {
	if logger == nil {
		logger = logrus.StandardLogger()
	}
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		cw := &statusCapturingResponseWriter{ResponseWriter: w}
		next.ServeHTTP(cw, r)
		logger.WithFields(logrus.Fields{
			"method":   r.Method,
			"path":     r.URL.Path,
			"status":   cw.status,
			"bytes":    cw.bytes,
			"duration": time.Since(start).String(),
		}).Info("http_request")
	})
}
""",
    )
    _write(
        opt.root / "cmd" / f"{opt.service}-api" / "main.go",
        """package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"REPLACE_MODULE/internal/REPLACE_SERVICE/bootstrap"
)

func main() {
	root := bootstrap.Compose()
	logger := root.Logger
	addr := envOr("HTTP_ADDR", ":8080")
	srv := &http.Server{
		Addr:              addr,
		Handler:           root.HTTPHandler,
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		logger.WithField("addr", addr).Info("http_listen")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.WithError(err).Fatal("http_server_error")
		}
	}()

	<-shutdownSignal()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = srv.Shutdown(ctx)
}

func shutdownSignal() <-chan os.Signal {
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
	return ch
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
""".replace("REPLACE_SERVICE", opt.service),
    )
    _write_health_tests(opt)


def _scaffold_http_echo(opt: Options) -> None:
    if opt.module is None:
        raise SystemExit("--module is required when scaffolding --kinds http (Go imports need a module path).")
    (opt.root / "cmd" / f"{opt.service}-api").mkdir(parents=True, exist_ok=True)
    (_svc(opt.root, opt.service) / "adapter" / "in" / "http").mkdir(parents=True, exist_ok=True)

    _write(
        _svc(opt.root, opt.service) / "adapter" / "in" / "http" / "server.go",
        """package http

import (
	"net/http"

	"github.com/labstack/echo/v4"
	echomw "github.com/labstack/echo/v4/middleware"
	"github.com/sirupsen/logrus"
)

func New(logger *logrus.Logger) *echo.Echo {
	e := echo.New()
	if logger == nil {
		logger = logrus.New()
	}
	e.HideBanner = true

	e.Use(echomw.RequestLoggerWithConfig(echomw.RequestLoggerConfig{
		LogStatus:   true,
		LogMethod:   true,
		LogURI:      true,
		LogLatency:  true,
		LogError:    true,
		LogValuesFunc: func(c echo.Context, v echomw.RequestLoggerValues) error {
			entry := logger.WithFields(logrus.Fields{
				"method":  v.Method,
				"uri":     v.URI,
				"status":  v.Status,
				"latency": v.Latency.String(),
			})
			if v.Error != nil {
				entry.WithError(v.Error).Error("http_request")
				return nil
			}
			entry.Info("http_request")
			return nil
		},
	}))

	e.GET("/health/live", func(c echo.Context) error {
		return c.NoContent(http.StatusOK)
	})
	e.GET("/health/ready", func(c echo.Context) error {
		return c.NoContent(http.StatusOK)
	})

	return e
}
""".replace("REPLACE_SERVICE", opt.service),
    )

    _write(
        opt.root / "cmd" / f"{opt.service}-api" / "main.go",
        """package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"REPLACE_MODULE/internal/REPLACE_SERVICE/bootstrap"
)

func main() {
	addr := envOr(\"HTTP_ADDR\", \":8080\")
	root := bootstrap.Compose()
	logger := root.Logger
	e := root.HTTPServer

	go func() {
		logger.WithField("addr", addr).Info("http_listen")
		if err := e.Start(addr); err != nil && err != http.ErrServerClosed {
			logger.WithError(err).Fatal("http_server_error")
		}
	}()

	<-shutdownSignal()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = e.Shutdown(ctx)
}

func shutdownSignal() <-chan os.Signal {
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
	return ch
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != \"\" {
		return v
	}
	return fallback
}
""".replace("REPLACE_SERVICE", opt.service),
    )
    _write_health_tests(opt)


def _write_health_tests(opt: Options) -> None:
    if opt.module is None:
        return
    _write(
        opt.root / "test" / "health_test.go",
        """package test

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"REPLACE_MODULE/internal/REPLACE_SERVICE/bootstrap"
)

func TestHealthLive(t *testing.T) {
	t.Parallel()
	root := bootstrap.Compose()
	if root.HTTPHandler == nil {
		t.Fatal("root.HTTPHandler is nil")
	}

	req := httptest.NewRequest(http.MethodGet, "/health/live", nil)
	rec := httptest.NewRecorder()
	root.HTTPHandler.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d", http.StatusOK, rec.Code)
	}
}

func TestHealthReady(t *testing.T) {
	t.Parallel()
	root := bootstrap.Compose()
	if root.HTTPHandler == nil {
		t.Fatal("root.HTTPHandler is nil")
	}

	req := httptest.NewRequest(http.MethodGet, "/health/ready", nil)
	rec := httptest.NewRecorder()
	root.HTTPHandler.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d", http.StatusOK, rec.Code)
	}
}
""".replace("REPLACE_SERVICE", opt.service),
    )


def _scaffold_placeholder(opt: Options, kind: str) -> None:
    (opt.root / "cmd" / f"{opt.service}-{kind}").mkdir(parents=True, exist_ok=True)
    (_svc(opt.root, opt.service) / "adapter" / "in" / kind).mkdir(parents=True, exist_ok=True)
    _write(
        opt.root / "cmd" / f"{opt.service}-{kind}" / "main.go",
        f"""package main

import "REPLACE_MODULE/internal/{opt.service}/bootstrap"

func main() {{
	logger := bootstrap.Compose().Logger
	logger.WithField("binary", "{opt.service}-{kind}").Info("todo_implement")
}}
""",
    )


def _replace_module_placeholders(root: Path, module: str | None) -> None:
    if module is None:
        return
    for path in root.rglob("*.go"):
        text = path.read_text(encoding="utf-8")
        if "REPLACE_MODULE" not in text:
            continue
        path.write_text(text.replace("REPLACE_MODULE", module), encoding="utf-8")


def parse_args() -> Options:
    parser = argparse.ArgumentParser(description="Scaffold a Go service repo using hexagonal layout.")
    parser.add_argument("--root", required=True, help="Target repo directory (created if missing).")
    parser.add_argument(
        "--module",
        help="Go module path (writes go.mod if missing; replaces imports). If omitted for a new project, defaults to the root folder name.",
    )
    parser.add_argument("--service", required=True, help="Service name (e.g., billing, payments).")
    parser.add_argument(
        "--kinds",
        default="http",
        help="Comma-separated binaries to scaffold: http,grpc,worker,cli (default: http).",
    )
    parser.add_argument(
        "--http-framework",
        default="echo",
        choices=["nethttp", "echo"],
        help="HTTP framework for --kinds http: echo (default) or nethttp.",
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip dependency install (do not run `go mod tidy` even if go.mod is created).",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    kinds = tuple(k.strip() for k in args.kinds.split(",") if k.strip())
    return Options(
        root=root,
        module=args.module,
        service=args.service,
        kinds=kinds,
        http_framework=args.http_framework,
        skip_deps=args.skip_deps,
    )


def main() -> None:
    opt = parse_args()
    if opt.module is None:
        opt.module = _discover_module_from_go_mod(opt.root)
    if opt.module is None and not (opt.root / "go.mod").exists():
        # Default to local module path based on folder name (avoid assuming github.com-style paths).
        opt.module = opt.root.name

    go_mod_created = _maybe_write_go_mod(opt.root, opt.module)
    _base_tree(opt)

    for kind in opt.kinds:
        if kind == "http":
            if opt.http_framework == "nethttp":
                _scaffold_http_nethttp(opt)
            elif opt.http_framework == "echo":
                _scaffold_http_echo(opt)
            else:
                raise SystemExit(f"Unsupported http framework: {opt.http_framework}")
        elif kind in {"grpc", "worker", "cli"}:
            _scaffold_placeholder(opt, kind)
        else:
            raise SystemExit(f"Unsupported kind: {kind} (supported: http, grpc, worker, cli)")

    _replace_module_placeholders(opt.root, opt.module)
    if go_mod_created and not opt.skip_deps:
        print("📦 Installing dependencies (go mod tidy)...")
        _install_deps_for_new_project(opt.root)


if __name__ == "__main__":
    main()
