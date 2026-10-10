#!/usr/bin/env python3
"""Fuzzing batch ultra-eficiente: busca controles en bloques de 10 para reducir requests."""
import httpx, time, json
from pathlib import Path

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}
DELAY = 0.15

results = {}
accounts = []

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
    httpx.post(f"{URL}/__reset", headers=headers, timeout=15)

def find_ctrl(prefix):
    """Find valid control with early termination."""
    for c in range(100):
        status, body = send(f"{prefix};{c}")
        if status < 400:
            return c, status, body
    return None, None, None

# ─── PHASE 1: ALTA controls (5 names) ──────────────────────────────
print("=== ALTA controls ===")
reset()
for name in ["A", "B", "C", "D", "E", "X", "Y", "Z", "Jo", "Al"]:
    ctrl, status, body = find_ctrl(f"ALTA;{name}")
    if ctrl is not None:
        print(f"  ALTA;{name} -> {ctrl}")
        results[f"ALTA;{name}"] = ctrl

# ─── PHASE 2: Create accounts, CONSULTA controls ───────────────────
print("\n=== CONSULTA controls ===")
reset()
for name in ["A", "B", "C", "D", "E"]:
    ctrl, status, body = find_ctrl(f"ALTA;{name}")
    if ctrl is not None and isinstance(body, dict) and "cuentaId" in body:
        acc = body["cuentaId"]
        ctrl2, _, _ = find_ctrl(f"CONSULTA;{acc}")
        if ctrl2 is not None:
            print(f"  CONSULTA;{acc} -> {ctrl2}")
            results[f"CONSULTA;{acc}"] = ctrl2
            accounts.append(acc)

# ─── PHASE 3: DEPOSITO controls ────────────────────────────────────
print("\n=== DEPOSITO controls ===")
if accounts:
    for amount in [1, 10, 100, 1000, 5000]:
        ctrl, _, _ = find_ctrl(f"DEPOSITO;{accounts[0]};{amount}")
        if ctrl is not None:
            print(f"  DEPOSITO;{accounts[0]};{amount} -> {ctrl}")
            results[f"DEPOSITO;{accounts[0]};{amount}"] = ctrl

# ─── PHASE 4: TRANSFER controls ────────────────────────────────────
print("\n=== TRANSFER controls ===")
if len(accounts) >= 2:
    # Deposit to acc1
    find_ctrl(f"DEPOSITO;{accounts[0]};100000")
    for amount in [1, 100, 1000, 10000, 50000]:
        ctrl, _, _ = find_ctrl(f"TRANSFER;{accounts[0]};{accounts[1]};{amount}")
        if ctrl is not None:
            print(f"  TRANSFER;{accounts[0]};{accounts[1]};{amount} -> {ctrl}")
            results[f"TRANSFER;{accounts[0]};{accounts[1]};{amount}"] = ctrl

# ─── PHASE 5: ANULA control ───────────────────────────────────────
print("\n=== ANULA control ===")
if len(accounts) >= 2:
    reset()
    find_ctrl(f"ALTA;A")
    find_ctrl(f"ALTA;B")
    find_ctrl(f"DEPOSITO;AC-0001;50000")
    _, _, body = find_ctrl(f"TRANSFER;AC-0001;AC-0002;1000")
    if isinstance(body, dict) and "operacionId" in body:
        op_id = body["operacionId"]
        ctrl, _, _ = find_ctrl(f"ANULA;{op_id}")
        if ctrl is not None:
            print(f"  ANULA;{op_id} -> {ctrl}")
            results[f"ANULA;{op_id}"] = ctrl

# Save
out = Path(__file__).parent.parent / "fuzz_results.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nSaved {len(results)} results to {out}")
