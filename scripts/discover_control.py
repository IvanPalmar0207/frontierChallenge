#!/usr/bin/env python3
"""Descubre controles válidos fuzzeando el servicio original con rate limiting respetado."""
import httpx, time

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}

def send(msg):
    time.sleep(0.12)  # ~8 req/s para no pegarnos contra rate limit
    try:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=10)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        return r.status_code, body
    except Exception as e:
        return -1, str(e)

def reset():
    time.sleep(0.12)
    httpx.post(f"{URL}/__reset", headers=headers, timeout=10)

# 1. ALTA;Test control
print("=== ALTA;Test ===")
reset()
alta_test_ctrl = None
for c in range(100):
    status, body = send(f"ALTA;Test;{c}")
    if status == 201:
        alta_test_ctrl = c
        print(f"  VALID: ALTA;Test;{c} -> 201")
        break
    if c % 20 == 0:
        print(f"  probando {c}...")

if alta_test_ctrl is None:
    print("  No encontrado en 0-99!")

# 2. Crear cuenta con control válido, luego fuzzear CONSULTA
if alta_test_ctrl is not None:
    cuenta_id = None
    status, body = send(f"ALTA;Test;{alta_test_ctrl}")
    if status == 201:
        cuenta_id = body.get("cuentaId", "AC-0001")
    
    print(f"\n=== CONSULTA;{cuenta_id} ===")
    consulta_ctrl = None
    for c in range(100):
        status, body = send(f"CONSULTA;{cuenta_id};{c}")
        if status == 200:
            consulta_ctrl = c
            print(f"  VALID: CONSULTA;{cuenta_id};{c} -> 200")
            break
        if c % 20 == 0:
            print(f"  probando {c}...")

# 3. DEPOSITO control
if cuenta_id:
    print(f"\n=== DEPOSITO;{cuenta_id};1000 ===")
    deposito_ctrl = None
    for c in range(100):
        status, body = send(f"DEPOSITO;{cuenta_id};1000;{c}")
        if status == 200:
            deposito_ctrl = c
            print(f"  VALID: DEPOSITO;{cuenta_id};1000;{c} -> 200")
            break
        if c % 20 == 0:
            print(f"  probando {c}...")

# 4. PING (ya sabemos que acepta cualquiera, confirmemos)
print("\n=== PING ===")
for c in [0, 1, 99]:
    status, body = send(f"PING;{c}")
    print(f"  PING;{c} -> {status}")

print("\n=== RESUMEN ===")
print(f"  ALTA;Test -> {alta_test_ctrl}")
if alta_test_ctrl:
    print(f"  CONSULTA;{cuenta_id} -> {consulta_ctrl}")
    print(f"  DEPOSITO;{cuenta_id};1000 -> {deposito_ctrl}")
