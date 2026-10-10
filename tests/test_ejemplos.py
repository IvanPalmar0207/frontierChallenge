#!/usr/bin/env python3
"""
Reproduce los 20 ejemplos contra el reemplazo local.
Compara status y body exacto.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
EJEMPLOS = Path(__file__).parent.parent / "pruebas" / "ejemplos.jsonl"
TOKEN = "test-token-123"

def _compare_json(a, b):
    if type(a) != type(b):
        return False
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_compare_json(a[k], b[k]) for k in a)
    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(_compare_json(x, y) for x, y in zip(a, b))
    return a == b

def test_all_20_examples():
    """Reproduce all 20 examples from pruebas/ejemplos.jsonl sequentially."""
    headers = {"Authorization": f"Bearer {TOKEN}"}

    # Reset
    r = client.post("/__reset", headers=headers)
    assert r.status_code == 200, f"Reset failed: {r.status_code}"

    passed = 0
    failed = 0
    errors = []

    with open(EJEMPLOS, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ex = json.loads(line)
            msg = ex["request"]["m"]
            expected_status = ex["status"]
            expected_body = ex["response"]

            r = client.post("/msg", json={"m": msg}, headers=headers)
            actual_status = r.status_code
            try:
                actual_body = r.json()
            except:
                actual_body = r.text

            match = (actual_status == expected_status)
            if isinstance(actual_body, dict) and isinstance(expected_body, dict):
                match = match and _compare_json(actual_body, expected_body)
            else:
                match = match and (actual_body == expected_body)

            if match:
                passed += 1
            else:
                failed += 1
                errors.append(f"  FAIL: {msg}\n    expected: {expected_status} {expected_body}\n    actual:   {actual_status} {actual_body}")

    if errors:
        print("\n".join(errors))
    assert failed == 0, f"{failed}/20 ejemplos fallaron"
    assert passed == 20, f"Solo {passed}/20 pasaron"
