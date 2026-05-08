# Production Deployment

This project deploys as a Docker web service on Render, with Neon PostgreSQL and
Upstash Redis.

## 1. Render Environment Variables

Go to Render Dashboard > your web service > Environment and add these keys.

Replace the placeholder values with your real Neon, Upstash, and Render values:

```env
DATABASE_URL=postgresql://YOUR_NEON_USER:YOUR_NEON_PASSWORD@YOUR_NEON_HOST/YOUR_NEON_DB?sslmode=require
REDIS_URL=rediss://default:YOUR_UPSTASH_PASSWORD@YOUR_UPSTASH_HOST:6379
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=url_clicks
BASE_URL=https://YOUR_RENDER_SERVICE_NAME.onrender.com
RATE_LIMIT_PER_MINUTE=100
ENABLE_KAFKA=false
CORS_ORIGINS=*
```

Important locations:

- `DATABASE_URL`: paste your Neon PostgreSQL connection string into Render's
  Environment tab under the key `DATABASE_URL`.
- `REDIS_URL`: paste your Upstash Redis connection string into Render's
  Environment tab under the key `REDIS_URL`. Prefer the TLS URL that starts
  with `rediss://`.
- `BASE_URL`: after Render creates the service URL, paste that public URL into
  Render's Environment tab under `BASE_URL`.
- `CORS_ORIGINS`: keep `*` for the public demo, or replace it with your Vercel
  frontend URL after deployment.

Do not paste production secrets into `.env.example`, `.env.production.example`,
or `render.yaml`.

## 2. Render Web Service Settings

Create a new Render Web Service from this GitHub repo.

- Environment: Docker
- Plan: Free
- Dockerfile path: `./Dockerfile`
- Health check path: `/health`

If using Render Blueprints, the committed `render.yaml` already defines these
settings and marks `DATABASE_URL`, `REDIS_URL`, and `BASE_URL` as values you
must provide in Render.

## 3. Smoke Tests

After Render deploys, replace `YOUR_SERVICE_URL` with your Render URL:

```bash
curl https://YOUR_SERVICE_URL/health
```

```bash
curl -X POST https://YOUR_SERVICE_URL/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url":"https://github.com/YOUR_USERNAME","idempotency_key":"prod-test-1"}'
```

Copy the returned `short_code`, then test redirect and analytics:

```bash
curl -i -L --max-redirs 0 https://YOUR_SERVICE_URL/SHORT_CODE
curl https://YOUR_SERVICE_URL/analytics/SHORT_CODE
```
