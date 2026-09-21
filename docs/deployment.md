# Deploying a shareable, persistent demo (Vercel + Railway)

This is not required for the challenge (`docker compose up --build` is the
graded path), but it's how to put this project on the public internet as a
portfolio piece with a permanent URL, for free/cheap.

Why two platforms: **Vercel** is serverless — perfect for the SvelteKit
frontend, but it cannot run a long-lived Django process with a persistent
Postgres connection. **Railway** runs plain Docker containers with a
managed Postgres add-on, which is what the backend needs. This split
(static/serverless frontend + a "real" backend host) is a very common
pattern in production, not a workaround.

## 0. Push the code to GitHub

Both platforms deploy from a GitHub repo.

```bash
gh auth login
gh repo create sre-ai-agent --private --source=. --remote=origin
git add -A
git commit -m "feat: initial SRE AI Agent implementation"
git push -u origin main
```

(Use `--public` instead of `--private` if you want the source visible too.)

## 1. Backend + Postgres on Railway

1. Go to **railway.app** → sign in with GitHub → **New Project** → **Deploy
   from GitHub repo** → select this repo.
2. Railway creates one service from the repo root. Open its **Settings**:
   - **Root Directory**: leave as `/` (the repo root — required, because
     `backend/Dockerfile` copies both `agent/` and `backend/`, so the
     build context must be the repo root, exactly like
     `docker-compose.yml` does).
   - **Dockerfile Path**: `backend/Dockerfile`.
3. In the same project, click **+ New** → **Database** → **PostgreSQL**.
   Railway provisions it and exposes a `DATABASE_URL` you can reference.
4. Back on the backend service → **Variables**, add:

   | Variable | Value |
   |---|---|
   | `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
   | `SECRET_KEY` | a random value — generate your own with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (Railway's variable-reference syntax — pick the Postgres service from the autocomplete) |
   | `ALLOWED_HOSTS` | `your-backend.up.railway.app` (Railway shows you the exact domain once deployed; comma-separate if you also attach a custom domain) |
   | `CORS_ALLOWED_ORIGINS` | `https://your-frontend.vercel.app` (set after step 2, once you know the Vercel URL) |
   | `LLM_PROVIDER` | `openai` |
   | `LLM_MODEL` | `gpt-4o-mini` |
   | `LLM_API_KEY` | your OpenAI key |

5. Deploy. Railway builds `backend/Dockerfile` and gives you a public
   `https://<something>.up.railway.app` URL. The container's `CMD` already
   runs `python manage.py migrate` on every boot, so the schema is created
   automatically — no manual step needed.
6. Verify: `curl https://<your-backend>.up.railway.app/api/v1/health/ready`
   should return `{"status": "ok", ...}`.

## 2. Frontend on Vercel

1. Go to **vercel.com** → sign in with GitHub → **Add New... → Project** →
   import this repo.
2. In the import screen, set **Root Directory** to `frontend`. Vercel
   auto-detects SvelteKit.
3. Add an environment variable:

   | Variable | Value |
   |---|---|
   | `PUBLIC_API_BASE_URL` | `https://<your-backend>.up.railway.app` (from step 1) |

4. Deploy. Vercel builds with `adapter-vercel` automatically — `svelte.config.js`
   picks it whenever Vercel's own `VERCEL=1` build env var is present;
   locally and in Docker it still builds with `adapter-node`, unaffected.
5. You get a permanent `https://<your-project>.vercel.app` URL.

## 3. Close the loop on CORS

Go back to the Railway backend service's variables and set
`CORS_ALLOWED_ORIGINS` to the exact Vercel URL from step 2 (e.g.
`https://sre-ai-agent.vercel.app`), then redeploy the backend. Without
this, the browser will block the frontend's requests to the API.

## 4. Share it

The Vercel URL is what you share. Every `git push` to `main` automatically
redeploys both platforms.

## Cost

- Vercel: free (Hobby plan) for a project at this scale.
- Railway: has a small monthly usage-based cost after any trial credit —
  typically a couple of dollars for a low-traffic demo like this
  (backend + a small Postgres instance running continuously). Check
  railway.app/pricing for current numbers.
- OpenAI: `gpt-4o-mini` costs fractions of a cent per conversation turn.
