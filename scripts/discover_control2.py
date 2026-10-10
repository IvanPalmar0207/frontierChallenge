#!/usr/bin/env python3
"""Fase 2: descubre más controles para deducir patrón."""
import httpx, time

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}

def send(msg):
    time.sleep(0.12)
    try:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=10)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        return r.status_code, body
    except Exception as e:
        return -1, str(e)

def reset():
    time.sleep(0.12)
    httpx.post(f"{URL}/__reset", headers=headers, timeout=10)

# FASE 1: ALTA múltiples nombres para ver si hay patrón
print("=== ALTA con nombres variados ===")
reset()
test_names = ["A", "B", "AA", "AB", "BA", "Test", "Lucia", "Mateo"]
for name in test_names:
    for c in range(100):
        status, body = send(f"ALTA;{name};{c}")
        if status == 201:
            print(f"  ALTA;{name} -> {c}")
            break
    else:
        print(f"  ALTA;{name} -> NOT FOUND")

# FASE 2: Crear cuentas y fuzzear CONSULTA para ver patrón con números de cuenta
print("\n=== CONSULTA para múltiples cuentas ===")
reset()
cuentas = []
for i in range(5):
    for c in range(100):
        status, body = send(f"ALTA;X;{c}")
        if status == 201:
            cuentas.append(body["cuentaId"])
            break

for cuenta in cuentas:
    for c in range(100):
        status, body = send(f"CONSULTA;{cuenta};{c}")
        if status == 200:
            print(f"  CONSULTA;{cuenta} -> {c}")
            break

# FASE 3: DEPOSITO con mismo monto en diferentes cuentas
print("\n=== DEPOSITO con monto fijo en diferentes cuentas ===")
reset()
cuentas2 = []
for i in range(3):
    for c in range(100):
        status, body = send(f"ALTA;Y;{c}")
        if status == 201:
            cuentas2.append(body["cuentaId"])
            break

for cuenta in cuentas2:
    for c in range(100):
        status, body = send(f"DEPOSITO;{cuenta};5000;{c}")
        if status == 200:
            print(f"  DEPOSITO;{cuenta};5000 -> {c}")
            break

# FASE 4: DEPOSITO con diferentes montos en misma cuenta
print("\n=== DEPOSITO con montos variados en misma cuenta ===")
reset()
cuenta_m = None
for c in range(100):
    status, body = send(f"ALTA;Z;{c}")
    if status == 201:
        cuenta_m = body["cuentaId"]
        break

for monto in [100, 500, 1000, 2000, 5000, 10000]:
    for c in range(100):
        status, body = send(f"DEPOSITO;{cuenta_m};{monto};{c}")
        if status == 200:
            print(f"  DEPOSITO;{cuenta_m};{monto} -> {c}")
            break

# FASE 5: TRANSFER con misma cuenta origen, diferentes destinos y montos
print("\n=== TRANSFER variado ===")
reset()
cuentas_t = []
for i in range(3):
    for c in range(100):
        status, body = send(f"ALTA;T;{c}")
        if status == 201:
            cuentas_t.append(body["cuentaId"])
            break

# Depositar a la primera
for c in range(100):
    status, body = send(f"DEPOSITO;{cuentas_t[0]};100000;{c}")
    if status == 200:
        break

# Transfer 1000 a segunda cuenta
for c in range(100):
    status, body = send(f"TRANSFER;{cuentas_t[0]};{cuentas_t[1]};1000;{c}")
    if status == 200:
        print(f"  TRANSFER;{cuentas_t[0]};{cuentas_t[1]};1000 -> {c}")
        break

# Transfer 2000 a tercera cuenta
for c in range(100):
    status, body = send(f"TRANSFER;{cuentas_t[0]};{cuentas_t[2]};2000;{c}")
    if status == 200:
        print(f"  TRANSFER;{cuentas_t[0]};{cuentas_t[2]};2000 -> {c}")
        break

print("\n=== FIN ===")
