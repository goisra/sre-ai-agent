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
- Verified, not just designed: `git log --all -p | grep` for the real
  OpenAI key and generated `SECRET_KEY` used in the live deployment
  returns zero matches across the entire history — neither was ever
  committed, even transiently.

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
  anything outside `TOOL_REGISTRY`. This is a code-level guarantee — true
  regardless of what the model is asked to do, including deliberate
  jailbreak/prompt-injection attempts.

## Topic scoping is a soft guardrail, not a hard one

`agent/prompts/system_prompt.txt` instructs the model to only engage with
service-health questions and ask for a known service name otherwise (with
`LLM_PROVIDER=openai`, this is enforced by the model actually following
that instruction — verified live: it correctly declines off-topic
questions like cooking recipes). This is **prompt-based, not code-based**:
a sufficiently adversarial user could likely get the model to talk about
something else with enough effort. What such an attempt still *cannot* do
is make the agent call anything outside `TOOL_REGISTRY` (see above) — the
tool boundary is the part of this system that's actually adversarial-safe;
the topic boundary is a UX/cost nicety, not a security control.

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

**Not implemented — a live, deliberate, accepted risk, not an oversight.**
The demo deployment (see `docs/deployment.md`) is publicly reachable with
`LLM_PROVIDER=openai`, so every unthrottled message costs real OpenAI
credit; this was explicitly reviewed and knowingly left unmitigated for
convenience while sharing the demo. The codebase is prepared for the fix:
DRF's `DEFAULT_THROTTLE_CLASSES` can be added to `REST_FRAMEWORK` in
`config/settings/base.py` without touching any view or service code, since
throttling is applied at the DRF view layer.

## Known limitations

- There is no authentication yet (see `docs/decisions.md` — "Authentication
  is out of scope"). `/api/v1/chat` is open. This is acceptable for a demo
  but would need to change before any real deployment.
- No formal security audit (SQL injection fuzzing, penetration testing,
  dependency vulnerability scanning) was performed — what's documented
  here is a code/architecture review appropriate to this project's size,
  not a substitute for one.
