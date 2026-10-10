#!/usr/bin/env python3
"""Fuzzing minimalista para descubrir el dígito de control."""
import httpx, time

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}

def send(msg):
    time.sleep(0.15)
    r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=10)
    return r.status_code, r.json() if r.headers.get("content-type","").startswith("application/json") else r.text

def reset():
    time.sleep(0.15)
    httpx.post(f"{URL}/__reset", headers=headers, timeout=10)

def find_valid(prefix, max_ctrl=99):
    """Find valid control for a message prefix by brute force."""
    for c in range(max_ctrl + 1):
        status, body = send(f"{prefix};{c}")
        if status < 400:
            return c, status, body
    return None, None, None

# ─── ALTA ──────────────────────────────────────────────────────────
print("=== ALTA controls ===")
reset()
for name in ["A", "B", "C", "Test", "Lucia"]:
    ctrl, status, body = find_valid(f"ALTA;{name}")
    ascii_sum = sum(ord(c) for c in name)
    print(f"  ALTA;{name}: ctrl={ctrl}, ascii_sum={ascii_sum}, mod50={ascii_sum%50}, mod100={ascii_sum%100}, diff={ascii_sum-ctrl if ctrl else 'N/A'}")

# ─── CONSULTA ──────────────────────────────────────────────────────
print("\n=== CONSULTA controls ===")
reset()
ctrl, status, body = find_valid("ALTA;X")
if ctrl is not None:
    cuenta = body["cuentaId"]
    ctrl2, _, _ = find_valid(f"CONSULTA;{cuenta}")
    print(f"  CONSULTA;{cuenta}: ctrl={ctrl2}")
    
    # Create another account
    ctrl3, _, body3 = find_valid("ALTA;Y")
    if ctrl3 is not None:
        cuenta2 = body3["cuentaId"]
        ctrl4, _, _ = find_valid(f"CONSULTA;{cuenta2}")
        print(f"  CONSULTA;{cuenta2}: ctrl={ctrl4}")
        
        # Difference?
        if ctrl2 and ctrl4:
            print(f"  diff between {cuenta} and {cuenta2}: {ctrl4 - ctrl2}")

# ─── DEPOSITO ───────────────────────────────────────────────────────
print("\n=== DEPOSITO controls ===")
reset()
ctrl, status, body = find_valid("ALTA;Z")
if ctrl is not None:
    cuenta = body["cuentaId"]
    for amount in [100, 1000]:
        ctrl2, _, _ = find_valid(f"DEPOSITO;{cuenta};{amount}")
        print(f"  DEPOSITO;{cuenta};{amount}: ctrl={ctrl2}")

# ─── TRANSFER ──────────────────────────────────────────────────────
print("\n=== TRANSFER controls ===")
reset()
ctrl1, _, body1 = find_valid("ALTA;A")
if ctrl1 is not None:
    acc1 = body1["cuentaId"]
    ctrl2, _, body2 = find_valid("ALTA;B")
    if ctrl2 is not None:
        acc2 = body2["cuentaId"]
        # Deposit to acc1
        ctrl3, _, _ = find_valid(f"DEPOSITO;{acc1};100000")
        if ctrl3 is not None:
            for amount in [1, 1000]:
                ctrl4, _, _ = find_valid(f"TRANSFER;{acc1};{acc2};{amount}")
                print(f"  TRANSFER;{acc1};{acc2};{amount}: ctrl={ctrl4}")

# ─── PING ──────────────────────────────────────────────────────────
print("\n=== PING controls ===")
for c in [0, 1, 64, 99]:
    status, body = send(f"PING;{c}")
    print(f"  PING;{c}: {status}")

print("\n=== DONE ===")
