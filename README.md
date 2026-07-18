# Rate Limiter (Python + FastAPI)

A rate limiter built from scratch to learn how token bucket rate limiting actually works.

## Status: Multi-Client, Tier-Based, Token Bucket (In-Memory)

Supports multiple clients identified by `X-Client-Id` header, each with their own
independent token bucket created lazily on first request. Clients are assigned a tier
via the `tier` query param (`free` or `premium`), which determines their rate limit capacity.

## How it works

- Each client has a `TokenBucket`: a `capacity` (max tokens), a `refill_rate`
  (tokens added per second), current `tokens`, and a `last_refill_time`.
- Capacity is determined by client tier:
  - `premium`: 10 requests
  - `free`: 3 requests
- On every request:
  1. Identify the client via the `X-Client-Id` header.
  2. If the client has no bucket yet, create one (lazy initialization).
  3. Calculate elapsed time since `last_refill_time`.
  4. Add `elapsed_seconds * refill_rate` tokens, capped at `capacity`.
  5. Update `last_refill_time` to now.
  6. If at least 1 token is available: allow the request, deduct 1 token.
  7. Otherwise: reject with `429 Too Many Requests`.
- Refilling is **lazy** — it's calculated on-demand at request time based on elapsed time,
  not on a background timer/loop.

## Project structure

```
├── main.py       # FastAPI app and route handler
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

### `GET /api/ping`

**Headers:**
- `X-Client-Id` (required): Client identifier string

**Query params:**
- `tier` (required): `free` or `premium`

**Response headers:**
- `X-RateLimit-Limit`: Max tokens (capacity)
- `X-RateLimit-Remaining`: Tokens left after this request
- `X-RateLimit-Reset`: (on 429) When the next token will be available

**Example:**
```bash
curl -i 'localhost:8000/api/ping?tier=premium' -H 'X-Client-Id: alice'
```

## Testing

### Test script

Run the test script to verify client isolation and tier-based rate limiting:

```bash
uv run python script.py
```

This script:
- Sends 20 rapid requests as `alice` (premium, capacity=10) — confirms 10 pass, 10 throttled
- Sends 10 requests as `bob` (free, capacity=3) — confirms 3 pass, 7 throttled
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
