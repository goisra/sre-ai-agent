# Deploying a shareable, persistent demo (Vercel + Railway)

This is not required for the challenge (`docker compose up --build` is the
graded path), but it's how this project is actually deployed as a public
portfolio demo — **live at
https://frontend-israel-jesus-projects.vercel.app** — for free/cheap.

Why two platforms: **Vercel** is serverless — perfect for the SvelteKit
frontend, but it cannot run a long-lived Django process with a persistent
Postgres connection. **Railway** runs plain Docker containers with a
managed Postgres add-on, which is what the backend needs. This split
(static/serverless frontend + a "real" backend host) is a common
production pattern, not a workaround.

This guide includes three issues that came up doing this deploy for real
and how each was fixed — they're the reason this version exists instead of
a generic "connect your repo and go" writeup.

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
     auto-detect. Railway's default builder ("Railpack") tries to guess how
     to run your app from scratch and will ignore a Dockerfile that isn't
     at the repo root; ours is at `backend/Dockerfile`, so without this
     explicit setting Railway detects "Python" and fails with *"No start
     command detected."*
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Root Directory**: leave empty / `/` (the repo root) — required
     because `backend/Dockerfile` also copies `agent/` and the root
     `pyproject.toml`, so the build context must be the repo root, exactly
     like `docker-compose.yml` does.
3. **+ New → Database → PostgreSQL** in the same project. This is a
   separate, manual step — Railway does not add a database automatically
   just because your app needs one.
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
   service you created in step 3 (Railway names it `Postgres` by default).
5. Backend service → **Settings → Networking → Public Networking** →
   **Generate Domain**. Railway will ask for a **target port**; leave it at
   whatever it defaults to (commonly `8080`) — this becomes the `PORT` env
   var Railway injects into the container. Then set `ALLOWED_HOSTS` above to
   that generated domain (e.g. `sre-ai-agent-production.up.railway.app`)
   and redeploy.

   **Why this needs no further app-side work:** `backend/Dockerfile`'s
   `CMD` binds gunicorn to `0.0.0.0:${PORT:-8000}`, not a hardcoded port —
   it automatically listens on whatever port Railway tells it to via
   `PORT`, and falls back to `8000` for docker-compose/local, where `PORT`
   isn't set. (This wasn't the original code — see the note below.)
6. Verify: `curl https://<your-backend-domain>/api/v1/health/ready` should
   return `{"status": "ok", "checks": {"database": true}}`. The container's
   `CMD` runs `python manage.py migrate` on every boot, so the schema is
   created automatically — no manual migration step needed.

**Issue #1 hit doing this for real — mismatched port:** the first deploy
crash-looped with `psycopg.OperationalError: connection to server at
"127.0.0.1", port 5432 failed` even after the domain was generated,
because the container was still listening on a hardcoded `8000` while
Railway's proxy was routing to the port chosen in step 5 (`8080` in our
case) — every request got a 502 before it ever reached Django. Fixed by
changing the Dockerfile's `CMD` to bind to `${PORT:-8000}` instead of a
fixed `8000` (commit `fix: bind gunicorn to PaaS-injected PORT`).

## 2. Frontend on Vercel

1. Go to **vercel.com** → sign in with GitHub → **Add New... → Project** →
   import this repo. Set **Root Directory** to `frontend`. Vercel
   auto-detects SvelteKit.
2. Add an environment variable (Project → Settings → Environment
   Variables, or `vercel env add PUBLIC_API_BASE_URL production`):

   | Variable | Value |
   |---|---|
   | `PUBLIC_API_BASE_URL` | your Railway backend's public URL from step 1 |

3. Deploy. Vercel builds with `adapter-vercel` automatically —
   `svelte.config.js` picks it whenever Vercel's own `VERCEL=1` build env
   var is present; locally and in Docker it still builds with
   `adapter-node`, unaffected.
4. Find the **stable** URL: a fresh `vercel --prod` deploy gets a unique
   per-deployment URL (e.g. `frontend-9oyvxzo7w-<team>.vercel.app`), but
   the project also keeps a **permanent alias** that doesn't change between
   deploys — `vercel inspect <any-deployment-url>` lists it under
   **Aliases** (e.g. `frontend-<team>.vercel.app`). Share that one, not the
   per-deploy URL.
5. **Disable Deployment Protection**, or the app won't be reachable by
   anyone but you: Project → **Settings → Deployment Protection** →
   set **Vercel Authentication** to **Disabled**. Team-scoped Vercel
   projects turn this on by default, which SSO-redirects every visitor —
   fine for an internal tool, not for a link you want to share publicly.

**Issue #2 hit doing this for real — protected by default:** the first
deploy returned `302` redirecting to `vercel.com/sso-api` for every
visitor, including in a private/incognito browser window. This is Vercel's
"Vercel Authentication" deployment protection, which is **on by default**
for any project under a team scope (not just a personal Hobby account).
Fixed by disabling it per step 5 above.

**Issue #3 hit doing this for real — the app silently called
`localhost`:** even after fixing protection, the deployed app failed every
chat request with a generic network error. `PUBLIC_API_BASE_URL` was set
correctly, but `frontend/src/routes/+page.svelte` has no server `load`
function and no dynamic route params, so SvelteKit's default
`prerender = "auto"` **prerendered it to static HTML at build time**.
`$env/dynamic/public` (used deliberately instead of `$env/static/public`,
so the same Docker image can point at different backends without a
rebuild — see `docs/decisions.md`) is only injected into the client when a
page actually goes through server-side rendering per request; on a
prerendered page there is no such request, so the browser fell back to
this project's `http://localhost:8000` default. Fixed by adding
`frontend/src/routes/+page.ts` with `export const prerender = false`,
forcing this route to render dynamically on every visit in both Vercel and
Docker (commit `fix: force the chat page to render dynamically`).

## 3. Close the loop on CORS

Back on Railway → backend service → Variables → set `CORS_ALLOWED_ORIGINS`
to the **stable** Vercel alias from step 4 above (not a per-deploy URL),
then redeploy. Without this, the browser blocks the frontend's requests to
the API with a CORS error.

## 4. Verify end-to-end before sharing

Don't trust "the build succeeded" — confirm the actual request path works:

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

Every `git push` to `main` automatically redeploys both platforms after
this initial setup.

## Cost

- Vercel: free (Hobby/team free tier) for a project at this scale.
- Railway: has a small monthly usage-based cost after any trial credit —
  typically a couple of dollars for a low-traffic demo like this
  (backend + a small Postgres instance running continuously). Check
  railway.app/pricing for current numbers.
- OpenAI: `gpt-4o-mini` costs fractions of a cent per conversation turn.
  There is no rate limiting on the deployed demo (see
  `docs/security.md`), so cost scales with however much traffic it gets.
