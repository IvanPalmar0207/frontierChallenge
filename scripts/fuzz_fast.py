#!/usr/bin/env python3
"""Fuzzer rápido: descubre controles con menos requests."""
import httpx, json, time
from pathlib import Path

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}
EXPERIMENTOS = Path(__file__).parent.parent / "experimentos.jsonl"

def send(msg, seq="fuzz"):
    time.sleep(0.08)
    r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=10)
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
    return r.status_code, body

def reset():
    httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
    time.sleep(0.08)

# FASE 1: PING control (0-99 rápido)
print("=== PING control ===")
reset()
for c in range(100):
    status, body = send(f"PING;{c}")
    if status == 200:
        print(f"  PING;{c} -> 200")
        ping_control = c
        break

# FASE 2: ALTA con diferentes nombres
print("\n=== ALTA controls ===")
reset()
test_cases = [
    ("A", "ALTA;A;"),
    ("B", "ALTA;B;"),
    ("AB", "ALTA;AB;"),
    ("ABC", "ALTA;ABC;"),
    ("Test", "ALTA;Test;"),
    ("Lucia", "ALTA;Lucia;"),
    ("Mateo", "ALTA;Mateo;"),
    ("X", "ALTA;X;"),
]
alta_results = {}
for name, prefix in test_cases:
    for c in range(100):
        status, body = send(f"{prefix}{c}")
        if status == 201:
            alta_results[name] = c
            print(f"  ALTA;{name} -> {c}")
            break

print(f"\n  ALTA results: {alta_results}")

# FASE 3: Analizar patrón
print("\n=== ANÁLISIS DE PATRÓN ===")
for name, ctrl in alta_results.items():
    ascii_sum = sum(ord(c) for c in name)
    print(f"  {name}: control={ctrl}, ascii_sum={ascii_sum}, diff={ascii_sum - ctrl}")

# FASE 4: Probar hipótesis de fórmula
print("\n=== HIPÓTESIS ===")
# Hipótesis: ¿es suma ASCII mod algo?
for mod in [10, 11, 12, 13, 50, 100, 256]:
    match = True
    for name, ctrl in alta_results.items():
        predicted = sum(ord(c) for c in name) % mod
        if predicted != ctrl:
            match = False
            break
    if match:
        print(f"  !!! MATCH: sum(ascii) mod {mod}")
        break
else:
    print("  No match simple encontrado")

# FASE 5: CONSULTA control (necesita cuenta existente)
print("\n=== CONSULTA control ===")
reset()
for c in range(100):
    status, body = send(f"ALTA;C;{c}")
    if status == 201:
        cuenta_id = body["cuentaId"]
        break
for c in range(100):
    status, body = send(f"CONSULTA;{cuenta_id};{c}")
    if status == 200:
        print(f"  CONSULTA;{cuenta_id} -> {c}")
        consulta_control = c
        break

print(f"\n  CONSULTA control: {consulta_control}")

# FASE 6: DEPOSITO control
print("\n=== DEPOSITO control ===")
reset()
for c in range(100):
    status, body = send(f"ALTA;D;{c}")
    if status == 201:
        cuenta_id = body["cuentaId"]
        break
for c in range(100):
    status, body = send(f"DEPOSITO;{cuenta_id};1000;{c}")
    if status == 200:
        print(f"  DEPOSITO;{cuenta_id};1000 -> {c}")
        deposito_control = c
        break

print("\n=== RESUMEN ===")
print(f"  PING: {ping_control}")
print(f"  ALTA: {alta_results}")
print(f"  CONSULTA: {consulta_control}")
print(f"  DEPOSITO: {deposito_control}")
