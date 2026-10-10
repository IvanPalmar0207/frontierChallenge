#!/usr/bin/env python3
"""
Fuzzing incremental contra el servicio original.
Strategy: find valid controls in small batches with long delays.
Rate limit target: ~6 req/s to avoid 429.
"""
import httpx, time, json
from pathlib import Path

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}

DELAY = 0.18

def send(msg):
    try:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=15)
        return r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
    except Exception as e:
        return -1, str(e)

def reset():
    httpx.post(f"{URL}/__reset", headers=headers, timeout=15)
    time.sleep(DELAY)

def find(prefix, max_ctrl=99, start=0):
    """Find valid control. Returns (control, status, body)."""
    for c in range(start, max_ctrl + 1):
        status, body = send(f"{prefix};{c}")
        if status < 400:
            time.sleep(DELAY)
            return c, status, body
        time.sleep(DELAY)
    return None, None, None

results = {}

print("=== BATCH 1: ALTA with 5 names ===")
reset()
for name in ["A", "B", "C", "D", "E"]:
    ctrl, status, body = find(f"ALTA;{name}")
    if ctrl is not None:
        print(f"  ALTA;{name} -> {ctrl}")
        results[f"ALTA;{name}"] = ctrl

print("\n=== BATCH 2: CONSULTA controls ===")
accounts = []
for name in ["A", "B", "C", "D", "E"]:
    ctrl = results.get(f"ALTA;{name}")
    if ctrl is not None:
        accounts.append(f"AC-00{len(accounts)+1:02d}")

for i, acc in enumerate(accounts):
    ctrl, status, body = find(f"CONSULTA;{acc}")
    if ctrl is not None:
        print(f"  CONSULTA;{acc} -> {ctrl}")
        results[f"CONSULTA;{acc}"] = ctrl

print("\n=== BATCH 3: DEPOSITO controls ===")
if accounts:
    acc = accounts[0]
    ctrl, status, body = find(f"DEPOSITO;{acc};1000")
    if ctrl is not None:
        print(f"  DEPOSITO;{acc};1000 -> {ctrl}")
        results[f"DEPOSITO;{acc};1000"] = ctrl

print("\n=== BATCH 4: TRANSFER controls ===")
if len(accounts) >= 2:
    acc1 = accounts[0]
    acc2 = accounts[1]
    # Deposit to acc1
    ctrl_d, _, _ = find(f"DEPOSITO;{acc1};50000")
    if ctrl_d is not None:
        # Transfer 1000
        ctrl_t, _, _ = find(f"TRANSFER;{acc1};{acc2};1000")
        if ctrl_t is not None:
            print(f"  TRANSFER;{acc1};{acc2};1000 -> {ctrl_t}")
            results[f"TRANSFER;{acc1};{acc2};1000"] = ctrl_t
        # Transfer 2000
        ctrl_t2, _, _ = find(f"TRANSFER;{acc1};{acc2};2000")
        if ctrl_t2 is not None:
            print(f"  TRANSFER;{acc1};{acc2};2000 -> {ctrl_t2}")
            results[f"TRANSFER;{acc1};{acc2};2000"] = ctrl_t2

print("\n=== BATCH 5: Same ALTA twice (determinism) ===")
reset()
ctrl1, _, _ = find("ALTA;X")
if ctrl1 is not None:
    print(f"  ALTA;X (1st) -> {ctrl1}")
    reset()
    ctrl2, _, _ = find("ALTA;X")
    if ctrl2 is not None:
        print(f"  ALTA;X (2nd) -> {ctrl2}")
        if ctrl1 == ctrl2:
            print("  ✓ Deterministic")
        else:
            print("  ✗ NOT DETERMINISTIC")

print("\n=== BATCH 6: Same CONSULTA twice ===")
reset()
ctrl_a, _, body_a = find("ALTA;Y")
if ctrl_a is not None:
    acc = "AC-0001"
    ctrl1, _, _ = find(f"CONSULTA;{acc}")
    if ctrl1 is not None:
        print(f"  CONSULTA;{acc} (1st) -> {ctrl1}")
        ctrl2, _, _ = find(f"CONSULTA;{acc}")
        if ctrl2 is not None:
            print(f"  CONSULTA;{acc} (2nd) -> {ctrl2}")
            if ctrl1 == ctrl2:
                print("  ✓ Deterministic")
            else:
                print("  ✗ NOT DETERMINISTIC")

print("\n=== ALL RESULTS ===")
for k, v in sorted(results.items()):
    print(f"  {k} -> {v}")

# Analysis
print("\n=== ANALYSIS: ALTA pattern ===")
for name in ["A", "B", "C", "D", "E"]:
    ctrl = results.get(f"ALTA;{name}")
    if ctrl is not None:
        ascii_sum = sum(ord(c) for c in name)
        xor_val = 0
        for c in name:
            xor_val ^= ord(c)
        print(f"  ALTA;{name}: ctrl={ctrl}, ascii_sum={ascii_sum}, xor={xor_val}, sum%100={ascii_sum%100}, xor%100={xor_val%100}")

# Try XOR of full message
print("\n=== ANALYSIS: XOR of full ALTA messages ===")
for name in ["A", "B", "C", "D", "E", "Lucia", "Mateo"]:
    ctrl = results.get(f"ALTA;{name}")
    msg = f"ALTA;{name}"
    xor_val = 0
    for c in msg:
        xor_val ^= ord(c)
    print(f"  {msg}: ctrl={ctrl}, xor_full={xor_val}, xor_full%100={xor_val%100}")

# CRC8
print("\n=== ANALYSIS: CRC8 of full ALTA messages ===")
def crc8(s, poly=0x07):
    crc = 0
    for c in s:
        crc ^= ord(c)
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc

for name in ["A", "B", "C", "D", "E", "Lucia", "Mateo"]:
    ctrl = results.get(f"ALTA;{name}")
    msg = f"ALTA;{name}"
    crc = crc8(msg)
    print(f"  {msg}: ctrl={ctrl}, crc8={crc}, crc8%100={crc%100}")

out_file = Path(__file__).parent.parent / "experimentos_control.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {out_file}")
