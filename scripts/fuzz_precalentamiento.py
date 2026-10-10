#!/usr/bin/env python3
"""
Fuzzing de precalentamiento contra el servicio original.
Descubre controles validos para expandir la lookup table.
Rate limit target: ~6 req/s (delay 0.17s).
"""
import httpx, time, json
from pathlib import Path

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}
DELAY = 0.17

def send(msg):
    time.sleep(DELAY)
    try:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=15)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        return r.status_code, body
    except Exception as e:
        return -1, str(e)

def reset():
    time.sleep(DELAY)
    try:
        httpx.post(f"{URL}/__reset", headers=headers, timeout=15)
    except:
        pass

def find_ctrl(prefix):
    """Find valid control 0-99."""
    for c in range(100):
        status, body = send(f"{prefix};{c}")
        if status < 400:
            return c, status, body
    return None, None, None

results = {}

# ─── PHASE 1: ALTA with common names ───────────────────────────────
print("=== PHASE 1: ALTA controls ===")
reset()
names = ["Juan", "Maria", "Pedro", "Ana", "Luis", "Carlos", "Sofia", "Diego", "Laura", "Pablo"]
accounts = []
for name in names:
    ctrl, status, body = find_ctrl(f"ALTA;{name}")
    if ctrl is not None:
        print(f"  ALTA;{name} -> {ctrl}")
        results[f"ALTA;{name}"] = ctrl
        if isinstance(body, dict) and "cuentaId" in body:
            accounts.append(body["cuentaId"])

# ─── PHASE 2: CONSULTA for created accounts ───────────────────────
print("\n=== PHASE 2: CONSULTA controls ===")
for acc in accounts:
    ctrl, status, body = find_ctrl(f"CONSULTA;{acc}")
    if ctrl is not None:
        print(f"  CONSULTA;{acc} -> {ctrl}")
        results[f"CONSULTA;{acc}"] = ctrl

# ─── PHASE 3: DEPOSITO with various amounts ──────────────────────
print("\n=== PHASE 3: DEPOSITO controls ===")
if accounts:
    acc = accounts[0]
    for amount in [1, 100, 1000, 5000, 10000, 50000, 100000]:
        ctrl, status, body = find_ctrl(f"DEPOSITO;{acc};{amount}")
        if ctrl is not None:
            print(f"  DEPOSITO;{acc};{amount} -> {ctrl}")
            results[f"DEPOSITO;{acc};{amount}"] = ctrl

# ─── PHASE 4: TRANSFER with various amounts ────────────────────────
print("\n=== PHASE 4: TRANSFER controls ===")
if len(accounts) >= 2:
    # Deposit to first account
    find_ctrl(f"DEPOSITO;{accounts[0]};200000")
    for amount in [1, 100, 1000, 10000, 50000, 100000]:
        ctrl, status, body = find_ctrl(f"TRANSFER;{accounts[0]};{accounts[1]};{amount}")
        if ctrl is not None:
            print(f"  TRANSFER;{accounts[0]};{accounts[1]};{amount} -> {ctrl}")
            results[f"TRANSFER;{accounts[0]};{accounts[1]};{amount}"] = ctrl

# ─── PHASE 5: ANULA control ───────────────────────────────────────
print("\n=== PHASE 5: ANULA control ===")
if len(accounts) >= 2:
    reset()
    find_ctrl(f"ALTA;A")
    find_ctrl(f"ALTA;B")
    find_ctrl(f"DEPOSITO;AC-0001;100000")
    _, _, body = find_ctrl(f"TRANSFER;AC-0001;AC-0002;1000")
    if isinstance(body, dict) and "operacionId" in body:
        op_id = body["operacionId"]
        ctrl, _, _ = find_ctrl(f"ANULA;{op_id}")
        if ctrl is not None:
            print(f"  ANULA;{op_id} -> {ctrl}")
            results[f"ANULA;{op_id}"] = ctrl

# ─── PHASE 6: Case insensitive CONSULTa ───────────────────────────
print("\n=== PHASE 6: Case insensitive ===")
if accounts:
    ctrl, _, _ = find_ctrl(f"CONSULTa;{accounts[0]}")
    if ctrl is not None:
        print(f"  CONSULTa;{accounts[0]} -> {ctrl}")
        results[f"CONSULTa;{accounts[0]}"] = ctrl

# ─── Save results ─────────────────────────────────────────────────
print(f"\n=== RESULTS: {len(results)} controls discovered ===")
for k, v in sorted(results.items()):
    print(f"  {k} -> {v}")

out = Path(__file__).parent.parent / "fuzz_results_precalentamiento.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {out}")
