# Worker / Consumer / Scheduler Layout

Use this for queue consumers, cron-like jobs, background processors, or outbox publishers.

## Additions to base layout

```text
cmd/
  <service>-worker/
    main.go
internal/
  adapter/in/worker/
    consumer/            # Message handlers / job runners
    scheduler/           # Cron wiring (if applicable)
  bootstrap/
    worker.go            # Start loops, concurrency limits, shutdown
```

## Outbox and eventing (common patterns)

```text
internal/adapter/out/
  kafka/
  sqs/
  nats/
internal/port/out/
  event_publisher.go
```

Treat the queue/broker as an outbound adapter unless it is the system’s primary interface.
