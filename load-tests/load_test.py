#!/usr/bin/env python3
"""
Baseline load test for AgentAichain API.
Target: 100+ RPS sustained for 30 seconds.

Usage: python3 load_test.py
Requirements: httpx
"""
import asyncio
import httpx
import time
import statistics
from datetime import datetime

BASE_URL = "http://localhost:8000"
TOTAL_REQUESTS = 3000  # 100 RPS for 30 seconds
CONCURRENCY = 100
BATCH_SIZE = 100

# Demo credentials (from seeded data)
DEMO_EMAIL = "admin@demo.com"
DEMO_PASSWORD = "demo123"


async def get_token(client: httpx.AsyncClient) -> str:
    """Obtain JWT token for demo admin"""
    resp = await client.post(
        f"{BASE_URL}/api/v1/auth/token",
        data={
            "username": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def health_check_worker(client: httpx.AsyncClient, sem: asyncio.Semaphore, results: list):
    """Worker for health endpoint (no auth)"""
    async with sem:
        start = time.perf_counter()
        try:
            resp = await client.get(f"{BASE_URL}/health")
            latency = (time.perf_counter() - start) * 1000  # ms
            results.append({
                "status": resp.status_code,
                "latency": latency,
                "timestamp": time.time()
            })
        except Exception as e:
            results.append({
                "status": 0,
                "latency": 0,
                "error": str(e)
            })


async def agents_list_worker(client: httpx.AsyncClient, sem: asyncio.Semaphore, token: str, results: list):
    """Worker for agents list endpoint (JWT auth)"""
    async with sem:
        start = time.perf_counter()
        try:
            resp = await client.get(
                f"{BASE_URL}/api/v1/agents/",
                headers={"Authorization": f"Bearer {token}"}
            )
            latency = (time.perf_counter() - start) * 1000  # ms
            results.append({
                "status": resp.status_code,
                "latency": latency,
                "timestamp": time.time()
            })
        except Exception as e:
            results.append({
                "status": 0,
                "latency": 0,
                "error": str(e)
            })


async def auth_token_worker(client: httpx.AsyncClient, sem: asyncio.Semaphore, results: list):
    """Worker for auth/token endpoint (login)"""
    async with sem:
        start = time.perf_counter()
        try:
            resp = await client.post(
                f"{BASE_URL}/api/v1/auth/token",
                data={
                    "username": DEMO_EMAIL,
                    "password": DEMO_PASSWORD
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            latency = (time.perf_counter() - start) * 1000  # ms
            results.append({
                "status": resp.status_code,
                "latency": latency,
                "timestamp": time.time()
            })
        except Exception as e:
            results.append({
                "status": 0,
                "latency": 0,
                "error": str(e)
            })


async def run_health_test(total_requests: int):
    """Run load test on health endpoint"""
    print("\n" + "="*60)
    print("LOAD TEST: Health Endpoint (GET /health)")
    print("="*60)

    results = []
    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        tasks = []
        start_time = time.time()

        for i in range(0, total_requests, BATCH_SIZE):
            batch = min(BATCH_SIZE, total_requests - i)
            tasks.extend([health_check_worker(client, sem, results) for _ in range(batch)])
            if len(tasks) >= 100:
                await asyncio.gather(*tasks)
                tasks = []
                print(f"  Progress: {i + batch}/{total_requests} requests sent...")

        if tasks:
            await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

    # Calculate metrics
    successful = [r for r in results if r["status"] == 200]
    errors = [r for r in results if r["status"] != 200]
    latencies = [r["latency"] for r in successful]

    rps = len(results) / elapsed
    error_rate = len(errors) / len(results) * 100 if results else 0

    print(f"\n📊 Results:")
    print(f"  Total requests: {len(results)}")
    print(f"  Duration: {elapsed:.2f}s")
    print(f"  RPS (requests/sec): {rps:.1f}")
    print(f"  Target RPS: 100")
    print(f"  ✅ Target {'MET' if rps >= 100 else 'NOT MET'}")
    print(f"\n  Successful: {len(successful)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Error rate: {error_rate:.2f}%")
    if latencies:
        print(f"\n  Latency (ms):")
        print(f"    Avg: {statistics.mean(latencies):.2f}")
        print(f"    Min: {min(latencies):.2f}")
        print(f"    Max: {max(latencies):.2f}")
        print(f"    P50: {statistics.median(latencies):.2f}")
        if len(latencies) >= 10:
            p95_index = int(0.95 * len(latencies))
            p95 = sorted(latencies)[p95_index]
            print(f"    P95: {p95:.2f}")


async def run_agents_test(total_requests: int):
    """Run load test on agents list endpoint (authenticated)"""
    print("\n" + "="*60)
    print("LOAD TEST: Agents List (GET /api/v1/agents/)")
    print("="*60)

    # Get token first
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        try:
            token = await get_token(client)
            print(f"  ✅ Obtained JWT token (length: {len(token)})")
        except Exception as e:
            print(f"  ❌ Failed to get token: {e}")
            return

    results = []
    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        tasks = []
        start_time = time.time()

        for i in range(0, total_requests, BATCH_SIZE):
            batch = min(BATCH_SIZE, total_requests - i)
            tasks.extend([agents_list_worker(client, sem, token, results) for _ in range(batch)])
            if len(tasks) >= 100:
                await asyncio.gather(*tasks)
                tasks = []
                print(f"  Progress: {i + batch}/{total_requests} requests sent...")

        if tasks:
            await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

    # Calculate metrics
    successful = [r for r in results if r["status"] == 200]
    errors = [r for r in results if r["status"] != 200]
    latencies = [r["latency"] for r in successful]

    rps = len(results) / elapsed
    error_rate = len(errors) / len(results) * 100 if results else 0

    print(f"\n📊 Results:")
    print(f"  Total requests: {len(results)}")
    print(f"  Duration: {elapsed:.2f}s")
    print(f"  RPS: {rps:.1f}")
    print(f"  Target RPS: 100")
    print(f"  ✅ Target {'MET' if rps >= 100 else 'NOT MET'}")
    print(f"\n  Successful: {len(successful)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Error rate: {error_rate:.2f}%")
    if latencies:
        print(f"\n  Latency (ms):")
        print(f"    Avg: {statistics.mean(latencies):.2f}")
        print(f"    Min: {min(latencies):.2f}")
        print(f"    Max: {max(latencies):.2f}")
        print(f"    P50: {statistics.median(latencies):.2f}")
        if len(latencies) >= 10:
            p95_index = int(0.95 * len(latencies))
            p95 = sorted(latencies)[p95_index]
            print(f"    P95: {p95:.2f}")


async def run_auth_test(total_requests: int):
    """Run load test on auth/token endpoint (login)"""
    print("\n" + "="*60)
    print("LOAD TEST: Auth Token (POST /api/v1/auth/token)")
    print("="*60)

    results = []
    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        tasks = []
        start_time = time.time()

        for i in range(0, total_requests, BATCH_SIZE):
            batch = min(BATCH_SIZE, total_requests - i)
            tasks.extend([auth_token_worker(client, sem, results) for _ in range(batch)])
            if len(tasks) >= 100:
                await asyncio.gather(*tasks)
                tasks = []
                print(f"  Progress: {i + batch}/{total_requests} requests sent...")

        if tasks:
            await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

    # Calculate metrics
    successful = [r for r in results if r["status"] == 200]
    errors = [r for r in results if r["status"] != 200]
    latencies = [r["latency"] for r in successful]

    rps = len(results) / elapsed
    error_rate = len(errors) / len(results) * 100 if results else 0

    print(f"\n📊 Results:")
    print(f"  Total requests: {len(results)}")
    print(f"  Duration: {elapsed:.2f}s")
    print(f"  RPS: {rps:.1f}")
    print(f"  Target RPS: 100")
    print(f"  ✅ Target {'MET' if rps >= 100 else 'NOT MET'}")
    print(f"\n  Successful: {len(successful)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Error rate: {error_rate:.2f}%")
    if latencies:
        print(f"\n  Latency (ms):")
        print(f"    Avg: {statistics.mean(latencies):.2f}")
        print(f"    Min: {min(latencies):.2f}")
        print(f"    Max: {max(latencies):.2f}")
        print(f"    P50: {statistics.median(latencies):.2f}")
        if len(latencies) >= 10:
            p95_index = int(0.95 * len(latencies))
            p95 = sorted(latencies)[p95_index]
            print(f"    P95: {p95:.2f}")


async def main():
    print(f"🚀 AgentAichain Load Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: 100+ RPS sustained")
    print(f"Concurrency: {CONCURRENCY} concurrent connections")
    print(f"Total requests per endpoint: {TOTAL_REQUESTS}")

    try:
        # Test 1: Health check (no auth)
        await run_health_test(TOTAL_REQUESTS)

        # Test 2: Agents list (JWT auth)
        await run_agents_test(TOTAL_REQUESTS)

        # Test 3: Auth token (login)
        await run_auth_test(TOTAL_REQUESTS)

        print("\n" + "="*60)
        print("✅ ALL LOAD TESTS COMPLETED")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\n⚠️  Load test interrupted by user")
    except Exception as e:
        print(f"\n❌ Load test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())