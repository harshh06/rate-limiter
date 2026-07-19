import asyncio
import httpx

async def make_request(client, i, port, endpoint, tier, client_id):
    url = f'http://localhost:{port}/api/{endpoint}?tier={tier}'
    headers = {'X-Client-Id': client_id} if client_id else {}
    resp = await client.get(url, headers=headers)
    return {
        'i': i,
        'status': resp.status_code,
        'remaining': resp.headers.get('X-RateLimit-Remaining', 'N/A'),
        'limit': resp.headers.get('X-RateLimit-Limit', 'N/A')
    }

async def test_client_isolation():
    print("=" * 60)
    print("TEST: Client Isolation & Tier-Based Rate Limiting (CONCURRENT)")
    print("=" * 60)

    alice_200 = 0
    alice_429 = 0
    bob_200 = 0
    bob_429 = 0

    async with httpx.AsyncClient() as client:
        # Phase 1: Alice
        print("\n--- Phase 1: Alice sends 20 rapid requests concurrently ---")
        tasks = []
        for i in range(20):
            port = 8000 if i % 2 == 0 else 8001
            tasks.append(make_request(client, i+1, port, 'ping', 'premium', 'alice'))
        
        results = await asyncio.gather(*tasks)
        
        for res in results:
            if res['status'] == 200:
                alice_200 += 1
            else:
                alice_429 += 1
            print(f"  [{res['i']:2d}] alice -> {res['status']}  remaining={res['remaining']}  limit={res['limit']}")
            
        print(f"\n  Alice summary: {alice_200} allowed, {alice_429} throttled")

        # Phase 2: Bob
        print("\n--- Phase 2: Bob sends 10 rapid requests concurrently ---")
        tasks = []
        for i in range(10):
            port = 8000 if i % 2 == 0 else 8001
            tasks.append(make_request(client, i+1, port, 'tweets', 'free', 'bob'))
            
        results = await asyncio.gather(*tasks)
        
        for res in results:
            if res['status'] == 200:
                bob_200 += 1
            else:
                bob_429 += 1
            print(f"  [{res['i']:2d}] bob   -> {res['status']}  remaining={res['remaining']}  limit={res['limit']}")
            
        print(f"\n  Bob summary: {bob_200} allowed, {bob_429} throttled")

    # Verify results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    passed = True

    if alice_200 == 10 and alice_429 == 10:
        print("PASS - Alice: 10 allowed, 10 throttled (global premium capacity=10)")
    else:
        print(f"FAIL - Alice: expected 10/10, got {alice_200}/{alice_429}")
        passed = False

    if bob_200 == 3 and bob_429 == 7:
        print("PASS - Bob: 3 allowed, 7 throttled (global free capacity=3)")
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

async def test_missing_client_id():
    print("\n" + "=" * 60)
    print("TEST: Missing X-Client-Id returns 400")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        resp = await client.get('http://localhost:8000/api/ping?tier=free')
        if resp.status_code == 400:
            print(f"PASS - Got 400: {resp.json()['detail']}")
        else:
            print(f"FAIL - Expected 400, got {resp.status_code}")

async def main():
    await test_client_isolation()
    await test_missing_client_id()

if __name__ == "__main__":
    asyncio.run(main())