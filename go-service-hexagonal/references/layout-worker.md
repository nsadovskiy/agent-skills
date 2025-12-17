# Worker / Consumer / Scheduler Layout

Use this for queue consumers, cron-like jobs, background processors, or outbox publishers.

## Additions to base layout

```text
cmd/
  <service>-worker/
    main.go
internal/<service>/
  adapter/in/worker/
    consumer/            # Message handlers / job runners
    scheduler/           # Cron wiring (if applicable)
  bootstrap/
    worker.go            # Start loops, concurrency limits, shutdown
```

## Outbox and eventing (common patterns)

```text
internal/<service>/adapter/out/
  kafka/
  sqs/
  nats/
internal/<service>/port/out/
  event_publisher.go
```

Treat the queue/broker as an outbound adapter unless it is the system’s primary interface.
