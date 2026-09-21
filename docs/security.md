# Security

## Secrets

- No secret is hardcoded. `SECRET_KEY`, database credentials, and
  `LLM_API_KEY` are all read from environment variables (`django-environ`).
- `.env` is git-ignored; `.env.example` documents every variable without
  real values.
- `production.py` refuses to start if `SECRET_KEY` is left at its insecure
  development default.
- Logs never include secrets: the structured logger only ever receives
  request metadata (method, path, status, duration, request ID, tool
  name/duration) — never headers, bodies, or credentials.

## Input validation

- Every request into `/api/v1/chat` is validated by a DRF serializer
  (`ChatRequestSerializer`) before it reaches any business logic. Invalid
  input returns `400` with the standard error envelope, never a stack
  trace.

## Tool execution boundary

This is the most security-relevant design decision in the project:

- The agent can only call functions listed in `agent/tools/registry.py`'s
  `TOOL_REGISTRY`. There is no dynamic dispatch by name to arbitrary
  functions, no `eval`/`exec`, and no shell access.
- Tools are pure functions operating on fixture data — they cannot reach
  the filesystem, network, or OS.
- Even with a real LLM provider, the model can only pick a tool name and
  arguments from the schema it was given; it cannot cause the agent to run
  anything outside `TOOL_REGISTRY`.

## Error handling

- All API errors — validation errors, unexpected exceptions, and
  agent/provider failures — are normalized to
  `{"error": {"code", "message"}, "request_id"}` by
  `config/exceptions.py`. Unexpected exceptions are logged with a full
  traceback server-side and never exposed to the client.

## CORS

- `CORS_ALLOWED_ORIGINS` is configurable per environment. Development
  defaults to the local Vite dev server ports; production must set it
  explicitly via environment variable — there is no wildcard in
  production settings.

## Transport and deployment

- `DEBUG` is `False` by default and only enabled in `development.py`.
- Production settings set `SECURE_CONTENT_TYPE_NOSNIFF`,
  `SECURE_BROWSER_XSS_FILTER`, and `X_FRAME_OPTIONS: DENY`. TLS termination
  is expected to happen at the ingress/load balancer, consistent with the
  Kubernetes manifests in `infrastructure/kubernetes/`.
- Container images run as a non-root user (see `backend/Dockerfile` and
  `frontend/Dockerfile`).

## Rate limiting

Not implemented in this version (out of scope for a demo), but the
codebase is prepared for it: DRF's `DEFAULT_THROTTLE_CLASSES` can be added
to `REST_FRAMEWORK` in `config/settings/base.py` without touching any view
or service code, since throttling is applied at the DRF view layer.

## Known limitations

- There is no authentication yet (see `docs/decisions.md` — "Authentication
  is out of scope"). `/api/v1/chat` is open. This is acceptable for a demo
  but would need to change before any real deployment.
