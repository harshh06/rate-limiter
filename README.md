# Rate Limiter (Python + FastAPI)

A rate limiter built from scratch to learn how token bucket rate limiting actually works

## Status: Single Client, Single Process, Token Bucket (In-Memory)

Currently supports a single hardcoded client (`alice`) hitting a dummy protected endpoint,
rate-limited via the Token Bucket algorithm, with state held in memory (no persistence,
no distribution yet).

## How it works

- Each client has a `TokenBucket`: a starting `tokens` count, a `capacity` (max tokens can
  ever refill to), a `refill_rate` (tokens added per second), and a `last_refill_time`.
- On every request:
  1. Calculate elapsed time since `last_refill_time`.
  2. Add `elapsed_seconds * refill_rate` tokens, capped at `capacity`.
  3. Update `last_refill_time` to now.
  4. If at least 1 token is available: allow the request, deduct 1 token.
  5. Otherwise: reject with `429 Too Many Requests`.
- Refilling is **lazy** — it's calculated on-demand at request time based on elapsed time,
  not on a background timer/loop.

## Running the server

```bash
uvicorn main:app --reload --port 8000
```

(adjust `main` to match your actual filename)

## Testing

### Basic burst test (no delay between requests)

Fires 20 requests back-to-back to see burst capacity get exhausted:

```bash
for i in {1..20}; do curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/api/ping; done
```

Expected: the first `tokens` (starting count) requests return `200`, the rest return `429`,
since almost no time passes between requests for meaningful refill to occur.

### Refill test (with delay between requests)

Fires requests roughly 1 second apart, to observe tokens regenerating over time:

```bash
for i in {1..20}; do
  curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/api/ping
  sleep 1
done
```

Expected: fewer/no rejections, since tokens are refilling between requests
(depending on your configured `refill_rate`).

### Inspecting response headers

To see rate-limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`,
`X-RateLimit-Reset`), use `-i` instead of `-s -o /dev/null -w`:

```bash
curl -i localhost:8000/api/ping
```

## Known limitations (by design, for now)

- Single hardcoded client (`alice`) 
- In-memory state only — a single process, single dictionary. This will visibly break
  once multiple server instances are introduced, which is intentional, fixed via Redis later.
