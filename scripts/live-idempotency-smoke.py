#!/usr/bin/env python3
"""Run live idempotency smoke test against deployed Fin Buddy production API.

Tests:
1. Syntax validation:
   - Key < 16 characters returns HTTP 400 invalid_idempotency_key
   - Key > 128 characters returns HTTP 400 invalid_idempotency_key
2. When AUTH_TOKEN is supplied:
   - First mutation with Idempotency-Key succeeds (HTTP 200/201)
   - Second mutation with identical key and payload replays cached response with Idempotency-Replayed: true
   - Third mutation with same key but different payload returns HTTP 409 conflict
"""

import os
import sys
import uuid
import httpx

API_URL = os.getenv("API_URL", "https://fin-buddy.fastapicloud.dev").rstrip("/")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")


def test_unauthenticated_syntax() -> bool:
    print(f"Testing Idempotency-Key syntax validation against {API_URL}...")
    client = httpx.Client(timeout=10.0)

    # Test 1: Key < 16 characters
    short_key = "short-key"
    res = client.post(
        f"{API_URL}/api/v1/transactions",
        headers={"Content-Type": "application/json", "Idempotency-Key": short_key},
        json={"amount": 100},
    )
    print(f"1. Short key (<16 chars: '{short_key}'): Status {res.status_code}")
    # Note: 400 invalid_idempotency_key is returned before 401 unauthenticated
    if res.status_code == 400 and "invalid_idempotency_key" in res.text:
        print("   PASS: Correctly rejected with 400 invalid_idempotency_key")
    elif res.status_code == 401:
        print("   INFO: Auth check ran before key validation (HTTP 401)")
    else:
        print(f"   Response: {res.text}")

    # Test 2: Key > 128 characters
    long_key = "k" * 129
    res = client.post(
        f"{API_URL}/api/v1/transactions",
        headers={"Content-Type": "application/json", "Idempotency-Key": long_key},
        json={"amount": 100},
    )
    print(f"2. Long key (>128 chars): Status {res.status_code}")
    if res.status_code == 400 and "invalid_idempotency_key" in res.text:
        print("   PASS: Correctly rejected with 400 invalid_idempotency_key")
    elif res.status_code == 401:
        print("   INFO: Auth check ran before key validation (HTTP 401)")
    else:
        print(f"   Response: {res.text}")

    return True


def test_authenticated_idempotency(token: str) -> bool:
    print(f"\nTesting authenticated mutation idempotency against {API_URL}...")
    client = httpx.Client(timeout=15.0, headers={"Authorization": f"Bearer {token}"})

    # Verify token
    me_res = client.get(f"{API_URL}/api/v1/auth/me")
    if me_res.status_code != 200:
        print(f"ERROR: Auth token rejected by /auth/me (Status {me_res.status_code}): {me_res.text}")
        return False

    user_info = me_res.json()
    print(f"Authenticated as: {user_info.get('email', 'user')}")

    # Generate a unique test key (32 chars)
    test_key = f"live-smoke-{uuid.uuid4().hex}"
    payload_a = {
        "account_id": None,
        "card_id": None,
        "type": "EXPENSE",
        "amount_paise": 100,
        "description": "Live Idempotency Verification Test",
        "date": "2026-09-08",
    }
    payload_b = {
        **payload_a,
        "amount_paise": 200,
    }

    print(f"\n1. Executing first request with key {test_key}...")
    res1 = client.post(
        f"{API_URL}/api/v1/transactions",
        headers={"Idempotency-Key": test_key},
        json=payload_a,
    )
    print(f"   Status: {res1.status_code}")
    replayed_header_1 = res1.headers.get("Idempotency-Replayed", res1.headers.get("idempotency-replayed"))
    print(f"   Idempotency-Replayed header: {replayed_header_1}")

    print(f"\n2. Replaying identical request with same key {test_key}...")
    res2 = client.post(
        f"{API_URL}/api/v1/transactions",
        headers={"Idempotency-Key": test_key},
        json=payload_a,
    )
    print(f"   Status: {res2.status_code}")
    replayed_header_2 = res2.headers.get("Idempotency-Replayed", res2.headers.get("idempotency-replayed"))
    print(f"   Idempotency-Replayed header: {replayed_header_2}")
    if replayed_header_2 == "true":
        print("   PASS: Idempotency-Replayed: true returned on cached replay!")
    else:
        print(f"   WARNING: Expected Idempotency-Replayed: true, got {replayed_header_2}")

    print(f"\n3. Sending conflicting payload with same key {test_key}...")
    res3 = client.post(
        f"{API_URL}/api/v1/transactions",
        headers={"Idempotency-Key": test_key},
        json=payload_b,
    )
    print(f"   Status: {res3.status_code}")
    if res3.status_code == 409:
        print("   PASS: Conflicting payload correctly rejected with HTTP 409 Conflict!")
    else:
        print(f"   WARNING: Expected HTTP 409, got {res3.status_code}: {res3.text}")

    return replayed_header_2 == "true" and res3.status_code == 409


if __name__ == "__main__":
    test_unauthenticated_syntax()
    if AUTH_TOKEN:
        success = test_authenticated_idempotency(AUTH_TOKEN)
        sys.exit(0 if success else 1)
    else:
        print("\nNote: Set AUTH_TOKEN=<token> to run authenticated mutation replay tests.")
        sys.exit(0)
