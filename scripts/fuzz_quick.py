#!/usr/bin/env python3
"""Fuzzing rápido con batches pequeños y manejo de excepciones."""
import httpx, time, json, sys
from pathlib import Path

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}
DELAY = 0.2

def send(msg):
    time.sleep(DELAY)
    try:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=10)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        return r.status_code, body
    except Exception as e:
        print(f"    ERROR sending {msg}: {e}", file=sys.stderr)
        return -1, str(e)

def reset():
    time.sleep(DELAY)
    try:
        httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
    except Exception as e:
        print(f"    ERROR reset: {e}", file=sys.stderr)

def find(prefix):
    for c in range(100):
        status, body = send(f"{prefix};{c}")
        if status < 400:
            return c, status, body
        if c % 20 == 0:
            print(f"    tested {c}...")
    return None, None, None

results = {}

print("=== Batch 1: ALTA names ===")
reset()
for name in ["Juan", "Maria", "Pedro", "Ana", "Luis"]:
    print(f"  Finding ALTA;{name}...")
    ctrl, status, body = find(f"ALTA;{name}")
    if ctrl is not None:
        print(f"    -> {ctrl}")
        results[f"ALTA;{name}"] = ctrl
    else:
        print(f"    -> NOT FOUND")

print("\n=== Batch 2: CONSULTA ===")
accounts = []
for name in ["Juan", "Maria", "Pedro", "Ana", "Luis"]:
    ctrl = results.get(f"ALTA;{name}")
    if ctrl is not None:
        _, body = send(f"ALTA;{name};{ctrl}")
        if isinstance(body, dict) and "cuentaId" in body:
            accounts.append(body["cuentaId"])

for acc in accounts:
    print(f"  Finding CONSULTA;{acc}...")
    ctrl, _, _ = find(f"CONSULTA;{acc}")
    if ctrl is not None:
        print(f"    -> {ctrl}")
        results[f"CONSULTA;{acc}"] = ctrl

print("\n=== Batch 3: DEPOSITO ===")
if accounts:
    acc = accounts[0]
    for amount in [100, 1000, 10000]:
        print(f"  Finding DEPOSITO;{acc};{amount}...")
        ctrl, _, _ = find(f"DEPOSITO;{acc};{amount}")
        if ctrl is not None:
            print(f"    -> {ctrl}")
            results[f"DEPOSITO;{acc};{amount}"] = ctrl

print("\n=== Batch 4: TRANSFER ===")
if len(accounts) >= 2:
    acc1 = accounts[0]
    acc2 = accounts[1]
    print(f"  Depositing to {acc1}...")
    find(f"DEPOSITO;{acc1};100000")
    for amount in [100, 1000, 10000]:
        print(f"  Finding TRANSFER;{acc1};{acc2};{amount}...")
        ctrl, _, _ = find(f"TRANSFER;{acc1};{acc2};{amount}")
        if ctrl is not None:
            print(f"    -> {ctrl}")
            results[f"TRANSFER;{acc1};{acc2};{amount}"] = ctrl

print(f"\n=== TOTAL: {len(results)} controls ===")
for k, v in sorted(results.items()):
    print(f"  {k} -> {v}")

out = Path(__file__).parent.parent / "fuzz_quick_results.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"Saved to {out}")
