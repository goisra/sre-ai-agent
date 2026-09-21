# Architecture Decision Records

## 1. Django + DRF as the API layer

**Context:** Need a production-grade web framework with batteries included
(ORM, migrations, admin-ready models) for a small but "real" service.
**Decision:** Django + Django REST Framework.
**Reason:** Mature, well-understood conventions for validation, middleware,
and testing; DRF gives serializers and a pluggable exception handler for
free.
**Trade-offs:** More structure/boilerplate than a micro-framework like
FastAPI or Flask for an app this small — accepted because the challenge
explicitly asks for production-mindedness (migrations, admin extensibility,
mature ecosystem) over minimal line count.

## 2. SvelteKit + TypeScript for the frontend

**Context:** Need a small, professional chat UI.
**Decision:** SvelteKit with TypeScript, `adapter-node` for the Docker
build.
**Reason:** Minimal boilerplate for a single-page interaction, first-class
TypeScript support, small bundle size.
**Trade-offs:** Smaller ecosystem/hiring pool than React — acceptable for a
demo of this size where the UI is intentionally simple.

## 3. Agent Service decoupled from Django

**Context:** The spec requires the agent's logic not to live in Django
views, and to be testable without a real LLM.
**Decision:** `agent/` is a separate, framework-agnostic Python package
(installed editable into the backend), containing the tool-calling loop,
the tool registry, and the LLM provider abstraction.
**Reason:** A hard package boundary (no Django import) is a stronger
guarantee of separation than a convention like "don't call Django from this
module." It also means the agent can be reused by something other than
Django later (a CLI, a worker) with zero changes.
**Trade-offs:** One more installable package to manage (`pip install -e .`)
instead of everything living under `backend/`. Judged worth it for the
architectural clarity.

## 4. LLM Provider abstraction with a deterministic default

**Context:** The spec requires the LLM to be swappable via configuration,
and requires tests not to depend on a real LLM.
**Decision:** `LLMProvider` is an abstract interface (`agent/providers/base.py`).
`LLM_PROVIDER=mock` (the default) uses a deterministic, rule-based
implementation with no external dependency; `LLM_PROVIDER=openai` uses
OpenAI's native tool-calling API.
**Reason:** Two goals collapse into one implementation: `docker compose up`
works with zero API keys out of the box, *and* the same `MockProvider`
doubles as the deterministic test double the spec asks for (no LLM calls
in unit tests). This wasn't originally spelled out in the requirements — it
was the natural resolution of "make it demoable with no keys" and "make
tests deterministic" being the same underlying need.
**Trade-offs:** The mock's "intelligence" is a fixed investigation plan
(status → deployments → error rate, +incidents if asked), not a real
reasoning model. It is good enough to demonstrate the tool-calling
architecture; a real provider is a config change away.

## 5. PostgreSQL for persistence

**Context:** Need to persist conversations, messages, and tool call
records.
**Decision:** PostgreSQL, via Django's ORM.
**Reason:** Required by the challenge; also the realistic choice for this
kind of relational, low-write-volume data.
**Trade-offs:** None significant at this scale — SQLite would have worked
for a demo, but Postgres matches what a production deployment would
actually use, and Docker Compose makes the extra service free to run
locally.

## 6. Docker Compose for local development

**Context:** Need a one-command way to run the full stack.
**Decision:** `docker-compose.yml` with `db`, `backend`, `frontend`
services; `docker compose up --build` is the only required step.
**Reason:** Reproducibility across machines; matches how the app would be
composed (minus orchestration) in production.
**Trade-offs:** Slower inner dev loop than running Django/Vite natively;
mitigated by documenting the native `make dev` path too.

## 7. CI as a quality gate, no CD

**Context:** Need automated checks; a real deployment target is out of
scope.
**Decision:** GitHub Actions runs backend lint+tests, frontend lint+tests,
then builds both Docker images. No deployment step.
**Reason:** Matches the acceptance criteria exactly — CI must fail the
build on any lint/test failure; CD to a real target isn't asked for and
would be unverifiable without real cloud credentials.
**Trade-offs:** None — this is intentionally scoped down.

## 8. Structured (JSON) logging without extra dependencies

**Context:** Need structured logs with a `request_id` on every entry.
**Decision:** A ~30-line custom `JsonFormatter` (`config/logging.py`)
instead of `structlog` or `python-json-logger`.
**Reason:** The requirement (JSON lines, consistent fields, no secrets) is
small enough that a dependency wasn't justified — keeps the dependency
list, and the app, smaller.
**Trade-offs:** Less feature-rich than a dedicated structured-logging
library (no built-in context binding). Acceptable at this scale; would
reconsider if the logging needs grew (e.g. multiple bound context values
per request).

## 9. Health checks split into liveness/readiness

**Context:** Spec asks for endpoints designed with Kubernetes in mind.
**Decision:** `/live` never checks dependencies; `/ready` checks the
database.
**Reason:** This is the standard Kubernetes pattern — conflating the two
causes pods to be killed (not just removed from load balancing) when a
dependency is briefly unavailable, which makes outages worse, not better.
**Trade-offs:** None.

## 10. Authentication is out of scope, but the seam exists

**Context:** Spec explicitly says "authentication (future)" — not required
now.
**Decision:** No authentication is implemented. `ChatRequestSerializer`
validation and DRF's `APIView` are the only gates on `/api/v1/chat`.
**Reason:** Out of scope per the challenge; adding real auth without a
defined user model/identity provider would be speculative.
**Trade-offs:** The endpoint is open. Documented explicitly in
`docs/security.md` as a known limitation, not silently omitted.

## 11. Backend listens on `$PORT`, not a hardcoded port

**Context:** Deploying the backend to Railway for the public demo (see
`docs/deployment.md`), the container crash-looped with Postgres connection
errors even though the database was configured correctly. The real cause:
Railway's proxy was routing traffic to the port chosen when generating a
public domain (`8080`), while `backend/Dockerfile`'s `CMD` had gunicorn
hardcoded to `0.0.0.0:8000` — every request hit a dead port before it ever
reached Django.
**Decision:** `CMD` binds to `0.0.0.0:${PORT:-8000}` instead of a fixed
port.
**Reason:** Railway (and most similar PaaS providers) inject a `PORT` env
var and expect the container to listen on it; there's no way to know that
port ahead of time since it's chosen per-deployment. Falling back to
`8000` keeps `docker-compose.yml` (which doesn't set `PORT`) unchanged.
**Trade-offs:** None — this is strictly more portable than a fixed port,
with no cost to the existing Docker Compose setup.

## 12. Frontend chat page is explicitly non-prerendered

**Context:** After fixing CORS and deployment protection for the Vercel
demo, the app still silently failed every chat request in production. The
cause: `src/routes/+page.svelte` has no server `load` function, so
SvelteKit's default `prerender = "auto"` rendered it to **static HTML at
build time**. `$env/dynamic/public` (used deliberately — see the LLM
Provider ADR's sibling reasoning: same idea, config without a rebuild) is
only injected into a page when it goes through actual server-side
rendering per request; a prerendered page never does that, so the browser
silently used this project's `localhost:8000` fallback in `chat.ts`
instead of the real backend URL — with no error until the fetch itself
failed.
**Decision:** `frontend/src/routes/+page.ts` sets `export const prerender
= false`, forcing this route to render per-request in both Vercel and
Docker.
**Reason:** This is the only way to keep using `$env/dynamic/public` (and
therefore keep the "one Docker image, configurable per environment"
property from ADR 4) without this class of bug. The alternative —
switching to `$env/static/public` — would have silently fixed Vercel but
reintroduced a rebuild-per-environment requirement for Docker deployments.
**Trade-offs:** This page can no longer be served as a cached static
asset; it's rendered on every request. Irrelevant at this app's traffic
scale, and the only page in the app besides it is a plain layout.
