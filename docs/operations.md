# Operations

## Health checks

- `GET /api/v1/health/live` — process liveness. Always returns `200` if the
  process can serve HTTP; has no dependency checks, so it never flaps due
  to a slow database.
- `GET /api/v1/health/ready` — readiness. Checks that PostgreSQL is
  reachable; returns `503` if not. Suitable for a Kubernetes
  `readinessProbe` (see `infrastructure/kubernetes/backend.yaml`), so a
  pod that loses its database connection is taken out of the load balancer
  without being killed.

## Logging

All logs are structured JSON (`config/logging.py`), one line per event,
suitable for ingestion by any log aggregator (Loki, CloudWatch, ELK). Every
event includes a `request_id` so a single user request can be traced across
the access log, the tool-execution logs, and any error log it produced.

Events emitted:

| Event                 | When                                  | Key fields                                |
|------------------------|----------------------------------------|--------------------------------------------|
| `request_completed`    | Every HTTP request                    | `method`, `path`, `status_code`, `duration_ms` |
| `tool_execution`       | Every tool the agent calls            | `tool`, `duration_ms`                      |
| `agent_execution_failed` | The agent/provider raised           | (stack trace only in server logs)          |
| `unhandled_exception`  | Any exception not otherwise handled   | (stack trace only in server logs)          |

`X-Request-ID` is also echoed back as a response header, and reused from
the inbound request if the caller already set one — useful behind a
gateway/load balancer that generates its own IDs.

## Deployment path (illustrative)

```text
Docker image
  -> Container Registry
  -> Kubernetes
  -> Deployment (rolling update, liveness/readiness probes)
  -> Service
  -> Ingress (TLS termination, routing /api to the backend)
```

See `infrastructure/kubernetes/` for the manifests and
`infrastructure/terraform/README.md` for how the surrounding cloud
infrastructure would be provisioned.

## Runbook: agent returns `AGENT_UNAVAILABLE`

1. Check `unhandled_exception` / `agent_execution_failed` logs for the
   `request_id` in the response.
2. If `LLM_PROVIDER=openai`, confirm `LLM_API_KEY` is set and the OpenAI
   API is reachable from the backend pod/container.
3. If `LLM_PROVIDER=mock` and this still happens, it's a code bug, not a
   provider outage — the mock provider has no external dependency.

## Runbook: readiness probe failing

1. `GET /api/v1/health/ready` locally — the response body names the failing
   check (`checks.database`).
2. Confirm the `db` service/Postgres instance is up and the backend's
   `POSTGRES_*` environment variables are correct.
