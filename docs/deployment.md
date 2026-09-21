# Deploying a shareable, persistent demo (Vercel + Railway)

This is not required for the challenge (`docker compose up --build` is the
graded path). It documents how this project is deployed as a public demo,
live at **https://frontend-israel-jesus-projects.vercel.app**.

**Why two platforms:** Vercel is serverless — well suited to the SvelteKit
frontend, but not to a long-lived Django process with a persistent
Postgres connection. Railway runs plain Docker containers with a managed
Postgres add-on, which the backend needs. Pairing a serverless frontend
with a container-based backend host is a common production pattern, not a
workaround.

This guide also documents three issues encountered during the initial
deployment and how each was resolved, so a repeat of this setup does not
need to rediscover them.

## 0. Push the code to GitHub

Both platforms deploy from a GitHub repo.

```bash
gh auth login
gh auth refresh -h github.com -s workflow   # needed to push .github/workflows/*
gh repo create sre-ai-agent --public --source=. --remote=origin --push
```

## 1. Backend + Postgres on Railway

1. Go to **railway.app** → sign in with GitHub → **New Project** → **Deploy
   from GitHub repo** → select this repo. Railway creates one service from
   the repo root.
2. Open the service's **Settings → Build** section:
   - **Builder**: set explicitly to **Dockerfile** — do not leave this on
     auto-detect. Railway's default builder ("Railpack") tries to infer how
     to run the app and ignores a Dockerfile that isn't at the repo root;
     ours is at `backend/Dockerfile`, so without this explicit setting
     Railway detects "Python" and fails with *"No start command detected."*
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Root Directory**: leave empty / `/` (the repo root) — required
     because `backend/Dockerfile` also copies `agent/` and the root
     `pyproject.toml`, so the build context must be the repo root, exactly
     like `docker-compose.yml` does.
3. **+ New → Database → PostgreSQL** in the same project. This is a
   separate, manual step — Railway does not provision a database
   automatically.
4. Backend service → **Variables** tab → **Raw Editor**, paste:

   ```env
   DJANGO_SETTINGS_MODULE=config.settings.production
   SECRET_KEY=<generate your own: python -c "import secrets; print(secrets.token_urlsafe(50))">
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ALLOWED_HOSTS=<filled in after step 5>
   CORS_ALLOWED_ORIGINS=<filled in after step 2 of the Vercel section>
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4o-mini
   LLM_API_KEY=<your OpenAI key>
   ```

   `${{Postgres.DATABASE_URL}}` is Railway's cross-service variable
   reference syntax — `Postgres` must match the exact name of the database
   service created in step 3 (Railway names it `Postgres` by default).
5. Backend service → **Settings → Networking → Public Networking** →
   **Generate Domain**. Railway asks for a **target port**; leave it at its
   default (commonly `8080`) — this becomes the `PORT` env var Railway
   injects into the container. Set `ALLOWED_HOSTS` above to the generated
   domain (e.g. `sre-ai-agent-production.up.railway.app`) and redeploy.

   `backend/Dockerfile`'s `CMD` binds gunicorn to `0.0.0.0:${PORT:-8000}`
   rather than a fixed port, so it listens on whatever port Railway assigns
   and falls back to `8000` for docker-compose/local, where `PORT` isn't
   set. See Issue 1 below for why this matters.
6. Verify: `curl https://<your-backend-domain>/api/v1/health/ready` should
   return `{"status": "ok", "checks": {"database": true}}`. The container's
   `CMD` runs `python manage.py migrate` on every boot, so the schema is
   created automatically.

## 2. Frontend on Vercel

1. Go to **vercel.com** → sign in with GitHub → **Add New... → Project** →
   import this repo. Set **Root Directory** to `frontend`. Vercel
   auto-detects SvelteKit.
2. Add an environment variable (Project → Settings → Environment
   Variables, or `vercel env add PUBLIC_API_BASE_URL production`):

   | Variable | Value |
   |---|---|
   | `PUBLIC_API_BASE_URL` | the Railway backend's public URL from step 1 |

3. Deploy. Vercel builds with `adapter-vercel` automatically —
   `svelte.config.js` selects it whenever Vercel's own `VERCEL=1` build env
   var is present; locally and in Docker it still builds with
   `adapter-node`, unaffected.
4. Find the **stable** URL: a fresh `vercel --prod` deploy gets a unique
   per-deployment URL (e.g. `frontend-9oyvxzo7w-<team>.vercel.app`), but
   the project also keeps a **permanent alias** that doesn't change between
   deploys — `vercel inspect <any-deployment-url>` lists it under
   **Aliases** (e.g. `frontend-<team>.vercel.app`). Share that one.
5. **Disable Deployment Protection**: Project → **Settings → Deployment
   Protection** → set **Vercel Authentication** to **Disabled**.
   Team-scoped Vercel projects enable this by default, which redirects
   every visitor through Vercel's own login — appropriate for an internal
   tool, not for a publicly shared demo. See Issue 2 below.

## 3. Close the loop on CORS

Back on Railway → backend service → Variables → set `CORS_ALLOWED_ORIGINS`
to the **stable** Vercel alias from step 4 above, then redeploy. Without
this, the browser blocks the frontend's requests to the API with a CORS
error.

## 4. Verify end-to-end before sharing

A successful build does not guarantee a working request path — confirm it
directly:

```bash
# Backend directly
curl https://<backend-domain>/api/v1/health/ready

# CORS preflight from the real frontend origin
curl -i -X OPTIONS https://<backend-domain>/api/v1/chat \
  -H "Origin: https://<frontend-domain>" \
  -H "Access-Control-Request-Method: POST"
# should include: access-control-allow-origin: https://<frontend-domain>

# The frontend's HTML should embed the real backend domain, not localhost
curl https://<frontend-domain>/ | grep <backend-domain-without-scheme>
```

Every `git push` to `main` redeploys both platforms automatically once
this initial setup is complete.

## Issues encountered during setup

### Issue 1: port mismatch on Railway

The first deploy crash-looped with `psycopg.OperationalError: connection
to server at "127.0.0.1", port 5432 failed`, even with a valid database
connection configured. The cause: the container was listening on a
hardcoded `8000` while Railway's proxy routed traffic to the port chosen
when the public domain was generated (`8080`), so every request returned
502 before reaching Django.

**Fix:** `backend/Dockerfile`'s `CMD` now binds to `${PORT:-8000}` instead
of a fixed port (commit `fix: bind gunicorn to PaaS-injected PORT`).

### Issue 2: Vercel deployment protection enabled by default

The first deploy returned a `302` redirect to `vercel.com/sso-api` for
every visitor, including in a private browser window. This is Vercel's
"Vercel Authentication" deployment protection, enabled by default for any
project under a team scope, not only personal Hobby accounts.

**Fix:** disabled under Project → Settings → Deployment Protection (step 5
above).

### Issue 3: prerendering bypassed the runtime backend URL

After resolving CORS and deployment protection, the app still failed
every chat request with a generic network error, despite
`PUBLIC_API_BASE_URL` being set correctly. The cause: `+page.svelte` has
no server `load` function, so SvelteKit's default `prerender = "auto"`
rendered it to static HTML at build time. `$env/dynamic/public` (used
deliberately instead of `$env/static/public`, so one Docker image can
target different backends without a rebuild — see `docs/decisions.md`) is
only injected into the page when it goes through server-side rendering
per request; a prerendered page never does, so the browser fell back to
this project's `http://localhost:8000` default.

**Fix:** `frontend/src/routes/+page.ts` sets `export const prerender =
false`, forcing this route to render dynamically on every request in both
Vercel and Docker (commit `fix: force the chat page to render
dynamically`; see ADR 12 in `docs/decisions.md`).

## Cost

- Vercel: free (Hobby/team free tier) for a project at this scale.
- Railway: a small monthly usage-based cost after any trial credit —
  typically a couple of dollars for a low-traffic demo like this
  (backend plus a small Postgres instance running continuously). See
  railway.app/pricing for current figures.
- OpenAI: `gpt-4o-mini` costs fractions of a cent per conversation turn.
  The deployed demo has no rate limiting (see `docs/security.md`), so cost
  scales with traffic.
