# Kubernetes manifests

These manifests are **illustrative**, not a deployed environment: they show
how the two container images this project builds (backend, frontend) would
be run in a cluster. No real cluster is provisioned as part of this
challenge.

## Files

- `configmap.yaml` — non-secret configuration (CORS origins, LLM provider).
- `secret.example.yaml` — shape of the Secret the Deployments expect
  (`SECRET_KEY`, `POSTGRES_PASSWORD`, `LLM_API_KEY`). Copy it, fill in real
  values, and apply it as `sre-agent-secrets` — never commit the real file.
- `backend.yaml` — backend Deployment + Service (liveness/readiness probes
  wired to `/api/v1/health/live` and `/ready`, resource requests/limits).
- `frontend.yaml` — frontend Deployment + Service.
- `ingress.yaml` — routes `/api` to the backend Service and everything else
  to the frontend Service.

## Assumed path to production

```text
Docker image
  -> Container Registry (e.g. GHCR/ECR)
  -> kubectl apply -f infrastructure/kubernetes/
  -> Deployment (rolling update)
  -> Service (stable in-cluster DNS)
  -> Ingress (external entrypoint, TLS termination)
```

Postgres itself is not modeled here; a real deployment would use a managed
database (RDS/Cloud SQL) rather than running Postgres in-cluster, so it is
intentionally left out.
