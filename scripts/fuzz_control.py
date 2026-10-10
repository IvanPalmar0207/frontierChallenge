#!/usr/bin/env python3
"""Fuzzer enfocado: descubre el dígito de control del servicio original."""
import httpx, json, time
from pathlib import Path
from collections import defaultdict

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}

EXPERIMENTOS = Path(__file__).parent.parent / "experimentos.jsonl"

def send(msg, seq="fuzz", hipotesis="", x_req=0):
    time.sleep(0.12)  # rate limit
    r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=10)
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
    log = {
        "id": _next_id(),
        "seq": seq,
        "x_req": x_req,
        "hipotesis": hipotesis,
        "request": {"m": msg},
        "status": r.status_code,
        "response": body,
        "conclusion": ""
    }
    _append_log(log)
    return r.status_code, body

def reset():
    httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
    time.sleep(0.12)

_log_counter = 0
def _next_id():
    global _log_counter
    _log_counter += 1
    return _log_counter

def _append_log(entry):
    with open(EXPERIMENTOS, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# FASE 1: Descubrir control para ALTA
print("=== FASE 1: ALTA brute-force control ===")
reset()
valid_controls = []
for c in range(100):
    status, body = send(f"ALTA;Test;{c}", seq="f1", hipotesis=f"ALTA;Test control={c}", x_req=c)
    if status == 201:
        valid_controls.append(("ALTA;Test", c))
        print(f"  [VALID] ALTA;Test;{c} -> 201")
        break
    if c % 10 == 0:
        print(f"  probando {c}...")

print(f"  Valid controls found: {valid_controls}")

# FASE 2: Descubrir si el control depende del contenido
print("\n=== FASE 2: Variaciones de contenido ===")
reset()
test_names = ["A", "AB", "ABC", "Test", "Lucia", "Mateo", "X"]
results = {}
for name in test_names:
    found = None
    for c in range(100):
        status, body = send(f"ALTA;{name};{c}", seq="f2", hipotesis=f"ALTA;{name} control={c}")
        if status == 201:
            found = c
            print(f"  ALTA;{name} -> control {c}")
            break
    results[name] = found

print(f"\n  Results: {results}")

# FASE 3: Analizar PING (sin args)
print("\n=== FASE 3: PING control ===")
reset()
for c in range(100):
    status, body = send(f"PING;{c}", seq="f3", hipotesis=f"PING control={c}")
    if status == 200:
        print(f"  [VALID] PING;{c} -> 200")
        break

# FASE 4: DEPOSITO control (necesita cuenta existente)
print("\n=== FASE 4: DEPOSITO control ===")
reset()
# Primero crear cuenta
for c in range(100):
    status, body = send(f"ALTA;Dep;{c}", seq="f4-prep", hipotesis=f"ALTA;Dep control={c}")
    if status == 201:
        cuenta_id = body["cuentaId"]
        print(f"  Cuenta creada: {cuenta_id}")
        break

for c in range(100):
    status, body = send(f"DEPOSITO;{cuenta_id};1000;{c}", seq="f4", hipotesis=f"DEPOSITO control={c}")
    if status == 200:
        print(f"  [VALID] DEPOSITO;{cuenta_id};1000;{c} -> 200")
        break

# FASE 5: CONSULTA control
print("\n=== FASE 5: CONSULTA control ===")
for c in range(100):
    status, body = send(f"CONSULTA;{cuenta_id};{c}", seq="f5", hipotesis=f"CONSULTA control={c}")
    if status == 200:
        print(f"  [VALID] CONSULTA;{cuenta_id};{c} -> 200")
        break

# FASE 6: TRANSFER control (necesita 2 cuentas)
print("\n=== FASE 6: TRANSFER control ===")
reset()
# Crear 2 cuentas
for c in range(100):
    status, body = send(f"ALTA;A;{c}", seq="f6-prep", hipotesis="ALTA A")
    if status == 201:
        cuenta_a = body["cuentaId"]
        break
for c in range(100):
    status, body = send(f"ALTA;B;{c}", seq="f6-prep", hipotesis="ALTA B")
    if status == 201:
        cuenta_b = body["cuentaId"]
        break
# Depositar a A
for c in range(100):
    status, body = send(f"DEPOSITO;{cuenta_a};10000;{c}", seq="f6-prep", hipotesis="DEPOSITO A")
    if status == 200:
        break
# Transferir A->B
for c in range(100):
    status, body = send(f"TRANSFER;{cuenta_a};{cuenta_b};1000;{c}", seq="f6", hipotesis=f"TRANSFER control={c}")
    if status == 200:
        print(f"  [VALID] TRANSFER;{cuenta_a};{cuenta_b};1000;{c} -> 200")
        break

# FASE 7: ANULA control (necesita operación)
print("\n=== FASE 7: ANULA control ===")
# Usar la transfer anterior
op_id = body.get("operacionId", "")
if op_id:
    for c in range(100):
        status, body = send(f"ANULA;{op_id};{c}", seq="f7", hipotesis=f"ANULA control={c}")
        if status == 200:
            print(f"  [VALID] ANULA;{op_id};{c} -> 200")
            break

print(f"\n=== Total experimentos: {_log_counter} ===")
