#!/usr/bin/env python3
"""Fuzzing inteligente: descubre controles válidos y busca patrón matemático."""
import httpx, time, json
from pathlib import Path

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}
EXPERIMENTOS = Path(__file__).parent.parent / "experimentos.jsonl"

def send(msg, retries=3):
    for _ in range(retries):
        time.sleep(0.13)
        try:
            r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=15)
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
            return r.status_code, body
        except Exception:
            time.sleep(1)
    return -1, "error"

def reset():
    time.sleep(0.13)
    httpx.post(f"{URL}/__reset", headers=headers, timeout=15)

def log(exp_id, seq, x_req, hipotesis, request_msg, status, response, conclusion=""):
    entry = {
        "id": exp_id, "seq": seq, "x_req": x_req,
        "hipotesis": hipotesis,
        "request": {"m": request_msg},
        "status": status, "response": response,
        "conclusion": conclusion
    }
    with open(EXPERIMENTOS, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ─── PHASE 1: ALTA controls for various names ──────────────────────
print("=== PHASE 1: ALTA controls ===")
reset()
names = ["A", "B", "C", "AA", "AB", "BA", "Test", "Lucia", "Mateo", "X", "Z", "Jo", "John"]
alta_controls = {}
for name in names:
    for c in range(100):
        status, body = send(f"ALTA;{name};{c}")
        if status == 201:
            alta_controls[name] = c
            print(f"  ALTA;{name} -> {c}")
            break
    else:
        print(f"  ALTA;{name} -> NOT FOUND")

# Analyze: is it related to name length?
print("\n--- Analysis: name length ---")
for name, ctrl in alta_controls.items():
    print(f"  {name} (len={len(name)}): ctrl={ctrl}")

# Analyze: is it related to sum of ASCII?
print("\n--- Analysis: ASCII sum ---")
for name, ctrl in alta_controls.items():
    s = sum(ord(c) for c in name)
    print(f"  {name}: ascii_sum={s}, ctrl={ctrl}, diff={s-ctrl}, mod50={s%50}, mod100={s%100}")

# Analyze: maybe it's a hash function
print("\n--- Analysis: hash candidates ---")

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

def djb2(s):
    h = 5381
    for c in s:
        h = ((h << 5) + h) + ord(c)
    return h & 0xFFFFFFFF

def fnv1a(s):
    h = 0x811c9dc5
    for c in s:
        h ^= ord(c)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h

for name, ctrl in alta_controls.items():
    h_crc8 = crc8(name) % 100
    h_djb2 = djb2(name) % 100
    h_fnv = fnv1a(name) % 100
    print(f"  {name}: ctrl={ctrl}, crc8%100={h_crc8}, djb2%100={h_djb2}, fnv1a%100={h_fnv}")

# ─── PHASE 2: CONSULTA controls for various accounts ──────────────
print("\n=== PHASE 2: CONSULTA controls ===")
reset()
# Create several accounts
accounts = []
for i in range(5):
    for c in range(100):
        status, body = send(f"ALTA;A;{c}")
        if status == 201:
            accounts.append(body["cuentaId"])
            break

consulta_controls = {}
for acc in accounts:
    for c in range(100):
        status, body = send(f"CONSULTA;{acc};{c}")
        if status == 200:
            consulta_controls[acc] = c
            print(f"  CONSULTA;{acc} -> {c}")
            break

print("\n--- Analysis: CONSULTA pattern ---")
for acc, ctrl in consulta_controls.items():
    # Account IDs are AC-0001, AC-0002, etc.
    num = int(acc.split("-")[1])
    print(f"  {acc} (num={num}): ctrl={ctrl}, diff={ctrl-num}, mod10={ctrl%10}")

# ─── PHASE 3: DEPOSITO controls for various amounts ───────────────
print("\n=== PHASE 3: DEPOSITO controls ===")
if accounts:
    acc = accounts[0]
    deposito_controls = {}
    for amount in [1, 10, 100, 1000, 5000, 10000, 250000]:
        for c in range(100):
            status, body = send(f"DEPOSITO;{acc};{amount};{c}")
            if status == 200:
                deposito_controls[amount] = c
                print(f"  DEPOSITO;{acc};{amount} -> {c}")
                break

    print("\n--- Analysis: DEPOSITO pattern ---")
    for amount, ctrl in deposito_controls.items():
        print(f"  amount={amount}: ctrl={ctrl}")

# ─── PHASE 4: TRANSFER controls ────────────────────────────────────
print("\n=== PHASE 4: TRANSFER controls ===")
reset()
# Create 2 accounts with balance
for c in range(100):
    status, body = send(f"ALTA;A;{c}")
    if status == 201:
        acc1 = body["cuentaId"]
        break
for c in range(100):
    status, body = send(f"ALTA;B;{c}")
    if status == 201:
        acc2 = body["cuentaId"]
        break

# Deposit to acc1
for c in range(100):
    status, body = send(f"DEPOSITO;{acc1};100000;{c}")
    if status == 200:
        break

transfer_controls = {}
for amount in [1, 100, 1000, 10000, 40000, 100000]:
    for c in range(100):
        status, body = send(f"TRANSFER;{acc1};{acc2};{amount};{c}")
        if status == 200:
            transfer_controls[amount] = c
            print(f"  TRANSFER;{acc1};{acc2};{amount} -> {c}")
            break

print("\n--- Analysis: TRANSFER pattern ---")
for amount, ctrl in transfer_controls.items():
    print(f"  amount={amount}: ctrl={ctrl}")

print("\n=== DONE ===")
