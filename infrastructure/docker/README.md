# Docker

The actual Dockerfiles live next to the code they build
(`backend/Dockerfile`, `frontend/Dockerfile`) so they stay easy to find and
in sync with dependency changes. This directory is kept as the documented
home for shared/local infrastructure tooling (e.g. an nginx reverse proxy
config) if this project ever needs one — it doesn't today, so it's
intentionally empty besides this file.

See `docker-compose.yml` at the repo root to run everything together.
