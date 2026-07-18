import requests


def test_client_isolation():
    """Test that alice (premium, 10 tokens) and bob (free, 3 tokens) have independent buckets."""

    print("=" * 60)
    print("TEST: Client Isolation & Tier-Based Rate Limiting")
    print("=" * 60)

    alice_200 = 0
    alice_429 = 0
    bob_200 = 0
    bob_429 = 0

    # Send 20 rapid requests as alice (premium, capacity=10)
    print("\n--- Phase 1: Alice sends 20 rapid requests (premium tier, capacity=10) ---")
    for i in range(20):
        resp = requests.get('http://localhost:8000/api/ping?tier=premium', headers={
            'X-Client-Id': 'alice'
        })
        status = resp.status_code
        remaining = resp.headers.get('X-RateLimit-Remaining', 'N/A')
        limit = resp.headers.get('X-RateLimit-Limit', 'N/A')

        if status == 200:
            alice_200 += 1
        else:
            alice_429 += 1

        print(f"  [{i+1:2d}] alice -> {status}  remaining={remaining}  limit={limit}")

    print(f"\n  Alice summary: {alice_200} allowed, {alice_429} throttled")

    # Send 10 requests as bob (free, capacity=3) — alice being throttled should NOT affect bob
    print("\n--- Phase 2: Bob sends 10 rapid requests (free tier, capacity=3) ---")
    for i in range(10):
        resp = requests.get('http://localhost:8000/api/ping?tier=free', headers={
            'X-Client-Id': 'bob'
        })
        status = resp.status_code
        remaining = resp.headers.get('X-RateLimit-Remaining', 'N/A')
        limit = resp.headers.get('X-RateLimit-Limit', 'N/A')

        if status == 200:
            bob_200 += 1
        else:
            bob_429 += 1

        print(f"  [{i+1:2d}] bob   -> {status}  remaining={remaining}  limit={limit}")

    print(f"\n  Bob summary: {bob_200} allowed, {bob_429} throttled")

    # Verify results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    passed = True

    if alice_200 == 10 and alice_429 == 10:
        print("PASS - Alice: 10 allowed, 10 throttled (premium capacity=10)")
    else:
        print(f"FAIL - Alice: expected 10/10, got {alice_200}/{alice_429}")
        passed = False

    if bob_200 == 3 and bob_429 == 7:
        print("PASS - Bob: 3 allowed, 7 throttled (free capacity=3)")
    else:
        print(f"FAIL - Bob: expected 3/7, got {bob_200}/{bob_429}")
        passed = False

    if alice_429 > 0 and bob_200 > 0:
        print("PASS - Client isolation: Bob was NOT affected by Alice's throttling")
    else:
        print("FAIL - Client isolation: Could not confirm independence")
        passed = False

    print()
    if passed:
        print("All checks passed!")
    else:
        print("WARNING: Some checks failed -- review output above")


def test_missing_client_id():
    """Test that requests without X-Client-Id are rejected with 400."""
    print("\n" + "=" * 60)
    print("TEST: Missing X-Client-Id returns 400")
    print("=" * 60)

    resp = requests.get('http://localhost:8000/api/ping?tier=free')
    if resp.status_code == 400:
        print(f"PASS - Got 400: {resp.json()['detail']}")
    else:
        print(f"FAIL - Expected 400, got {resp.status_code}")


if __name__ == "__main__":
    test_client_isolation()
    test_missing_client_id()