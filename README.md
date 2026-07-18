# Rate Limiter (Python + FastAPI)

A rate limiter built from scratch to learn how token bucket rate limiting actually works.

## Status: Multi-Client, Middleware-Based, Token Bucket (In-Memory)

Rate limiting is implemented as FastAPI middleware that wraps all `/api/*` endpoints.
Multiple clients are identified by `X-Client-Id` header, each with their own independent
token bucket created lazily on first request. Clients are assigned a tier via the `tier`
query param (`free` or `premium`), which determines their rate limit capacity.

## How it works

- Rate limiting runs as **middleware** — it applies automatically to all protected endpoints
  without any per-route logic. Routes like `/`, `/docs`, and `/openapi.json` are excluded.
- Each client has a `TokenBucket`: a `capacity` (max tokens), a `refill_rate`
  (tokens added per second), current `tokens`, and a `last_refill_time`.
- Capacity is determined by client tier:
  - `premium`: 10 requests
  - `free`: 3 requests
- On every request:
  1. Middleware checks if the path is excluded — if so, pass through.
  2. Identify the client via the `X-Client-Id` header (400 if missing).
  3. If the client has no bucket yet, create one (lazy initialization).
  4. Calculate elapsed time since `last_refill_time`.
  5. Add `elapsed_seconds * refill_rate` tokens, capped at `capacity`.
  6. Update `last_refill_time` to now.
  7. If at least 1 token is available: allow the request, deduct 1 token.
  8. Otherwise: reject with `429 Too Many Requests`.
- Refilling is **lazy** — it's calculated on-demand at request time based on elapsed time,
  not on a background timer/loop.
- Rate-limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`)
  are set by the middleware, keeping route handlers clean.

## Project structure

```
├── main.py       # FastAPI app, middleware, and route handlers
├── models.py     # TokenBucket class and tier config
├── utils.py      # Token refill logic
├── script.py     # Test script for client isolation
└── pyproject.toml
```

## Running the server

```bash
# Using FastAPI CLI (recommended for development)
fastapi dev

# Or using uvicorn directly
uvicorn main:app --reload --port 8000
```

## API

All `/api/*` endpoints are rate-limited via middleware. The following endpoints are available:

### `GET /api/ping`

Returns `{"message": "Server pinged"}`.

### `GET /api/tweets`

Returns `{"message": "Tweet!"}`.

### Common request format

**Headers:**
- `X-Client-Id` (required): Client identifier string

**Query params:**
- `tier` (required): `free` or `premium`

**Response headers (set by middleware):**
- `X-RateLimit-Limit`: Max tokens (capacity)
- `X-RateLimit-Remaining`: Tokens left after this request
- `X-RateLimit-Reset`: (on 429) When the next token will be available

**Example:**
```bash
curl -i 'localhost:8000/api/ping?tier=premium' -H 'X-Client-Id: alice'
curl -i 'localhost:8000/api/tweets?tier=free' -H 'X-Client-Id: bob'
```

### Excluded paths

The following paths bypass rate limiting:
- `/` — root / health check
- `/docs` — Swagger UI
- `/openapi.json` — OpenAPI spec

## Testing

### Test script

Run the test script to verify client isolation and tier-based rate limiting:

```bash
uv run python script.py
```

This script:
- Sends 20 rapid requests as `alice` (premium, capacity=10) — confirms 10 pass, 10 throttled
- Sends 10 requests as `bob` on a different endpoint (free, capacity=3) — confirms 3 pass, 7 throttled
- Verifies bob is NOT affected by alice's throttling (client isolation)
- Tests that requests without `X-Client-Id` return 400

### Manual curl tests

```bash
# Burst test — fires 20 requests back-to-back
for i in {1..20}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    'localhost:8000/api/ping?tier=premium' \
    -H 'X-Client-Id: alice'
done

# Refill test — fires requests 1 second apart
for i in {1..20}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    'localhost:8000/api/ping?tier=premium' \
    -H 'X-Client-Id: alice'
  sleep 1
done
```

## Known limitations (by design, for now)

- In-memory state only — a single process, single dictionary. This will visibly break
  once multiple server instances are introduced, which is intentional, fixed via Redis later.
- Tier is passed as a query param on every request — only used on first request to create
  the bucket. A real system would look this up from a database.
