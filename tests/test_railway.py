#!/usr/bin/env python3
"""Valida el deploy en Railway contra los 20 ejemplos."""
import httpx, json
from pathlib import Path

URL = "https://caja-negra-replacement-production.up.railway.app"
TOKEN = "test-railway"
headers = {"Authorization": f"Bearer {TOKEN}"}
EJEMPLOS = Path(__file__).parent.parent / "pruebas" / "ejemplos.jsonl"

def send(msg):
    r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=15)
    body = r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
    return r.status_code, body

# Reset
httpx.post(f"{URL}/__reset", headers=headers, timeout=15)

passed = 0
failed = 0
with open(EJEMPLOS, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip(): continue
        ex = json.loads(line)
        msg = ex["request"]["m"]
        expected_status = ex["status"]
        expected_body = ex["response"]
        actual_status, actual_body = send(msg)

        match = actual_status == expected_status
        if isinstance(actual_body, dict) and isinstance(expected_body, dict):
            match = match and all(actual_body.get(k) == v for k, v in expected_body.items())
        else:
            match = match and actual_body == expected_body

        if match:
            passed += 1
            print(f"  PASS: {msg}")
        else:
            failed += 1
            print(f"  FAIL: {msg}")
            print(f"    expected: {expected_status} {expected_body}")
            print(f"    actual:   {actual_status} {actual_body}")

print(f"\n=== Railway: {passed} pass / {failed} fail ===")
