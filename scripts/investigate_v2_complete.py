#!/usr/bin/env python3
"""
Investigacion completa V2.
Usa controles V1 correctos donde se sabe, y prueba comportamientos clave.
"""
import httpx, time, json
from pathlib import Path

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}

def send(msg):
    time.sleep(0.15)
    try:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=15)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        return r.status_code, body
    except Exception as e:
        return -1, str(e)

def reset():
    time.sleep(0.15)
    httpx.post(f"{URL}/__reset", headers=headers, timeout=15)

print("=" * 60)
print("  INVESTIGACION V2 COMPLETA")
print("=" * 60)

# --- SECUENCIA 1: Basica ALTA -> DEPOSITO -> CONSULTA ---
print("\n--- SECUENCIA 1: Basica ---")
reset()
# Usar controles V1 conocidos
s1, b1 = send("ALTA;Lucia;82")  # Control V1 conocido
print(f"  ALTA;Lucia;82 -> {s1} {b1}")
s2, b2 = send("ALTA;Mateo;3")    # Control V1 conocido
print(f"  ALTA;Mateo;3 -> {s2} {b2}")

if s1 == 201 and s2 == 201:
    acc1 = b1["cuentaId"]
    acc2 = b2["cuentaId"]
    print(f"  Cuentas creadas: {acc1}, {acc2}")
    
    # DEPOSITO con control V1 conocido
    s3, b3 = send("DEPOSITO;AC-0001;250000;86")
    print(f"  DEPOSITO;AC-0001;250000;86 -> {s3} {b3}")
    
    # CONSULTA
    s4, b4 = send("CONSULTA;AC-0001;14")
    print(f"  CONSULTA;AC-0001;14 -> {s4} {b4}")
    
    # CONSULTA AC-0002 (debe tener 0)
    s5, b5 = send("CONSULTA;AC-0002;11")
    print(f"  CONSULTA;AC-0002;11 -> {s5} {b5}")

# --- SECUENCIA 2: TRANSFER ---
print("\n--- SECUENCIA 2: TRANSFER ---")
reset()
s1, b1 = send("ALTA;Lucia;82")
s2, b2 = send("ALTA;Mateo;3")
if s1 == 201 and s2 == 201:
    send("DEPOSITO;AC-0001;250000;86")
    
    # Transfer 40000 (control V1)
    s3, b3 = send("TRANSFER;AC-0001;AC-0002;40000;86")
    print(f"  TRANSFER 40000 -> {s3} {b3}")
    
    # Consultar saldos
    s4, b4 = send("CONSULTA;AC-0001;14")
    print(f"  CONSULTA AC-0001 post-transfer -> {s4} {b4}")
    s5, b5 = send("CONSULTA;AC-0002;11")
    print(f"  CONSULTA AC-0002 post-transfer -> {s5} {b5}")
    
    # Transfer 120000 (debe fallar E506)
    s6, b6 = send("TRANSFER;AC-0001;AC-0002;120000;55")
    print(f"  TRANSFER 120000 -> {s6} {b6}")
    
    # Transfer 100000 (debe pasar)
    s7, b7 = send("TRANSFER;AC-0001;AC-0002;100000;12")
    print(f"  TRANSFER 100000 -> {s7} {b7}")
    
    # Transfer sin saldo suficiente
    s8, b8 = send("TRANSFER;AC-0002;AC-0001;50000;23")
    print(f"  TRANSFER sin saldo -> {s8} {b8}")

# --- SECUENCIA 3: ANULA ---
print("\n--- SECUENCIA 3: ANULA ---")
reset()
s1, b1 = send("ALTA;Lucia;82")
s2, b2 = send("ALTA;Mateo;3")
if s1 == 201 and s2 == 201:
    send("DEPOSITO;AC-0001;250000;86")
    s3, b3 = send("TRANSFER;AC-0001;AC-0002;100000;12")
    print(f"  TRANSFER 100000 -> {s3} {b3}")
    
    if s3 == 200:
        op_id = b3["operacionId"]
        
        # Anular primera vez
        s4, b4 = send(f"ANULA;{op_id};66")
        print(f"  ANULA 1ra -> {s4} {b4}")
        
        # Anular segunda vez
        s5, b5 = send(f"ANULA;{op_id};66")
        print(f"  ANULA 2da -> {s5} {b5}")
        
        # Verificar saldos post-anulacion
        s6, b6 = send("CONSULTA;AC-0001;14")
        print(f"  CONSULTA AC-0001 post-anula -> {s6} {b6}")
        s7, b7 = send("CONSULTA;AC-0002;11")
        print(f"  CONSULTA AC-0002 post-anula -> {s7} {b7}")

# --- SECUENCIA 4: ANULA DEPOSITO ---
print("\n--- SECUENCIA 4: ANULA DEPOSITO ---")
reset()
s1, b1 = send("ALTA;Lucia;82")
if s1 == 201:
    s2, b2 = send("DEPOSITO;AC-0001;10000;86")
    print(f"  DEPOSITO 10000 -> {s2} {b2}")
    
    if s2 == 200:
        op_id = b2["operacionId"]
        s3, b3 = send("CONSULTA;AC-0001;14")
        print(f"  CONSULTA pre-anula -> {s3} {b3}")
        
        s4, b4 = send(f"ANULA;{op_id};66")
        print(f"  ANULA DEPOSITO -> {s4} {b4}")
        
        s5, b5 = send("CONSULTA;AC-0001;14")
        print(f"  CONSULTA post-anula -> {s5} {b5}")

# --- SECUENCIA 5: Edge cases ---
print("\n--- SECUENCIA 5: Edge cases ---")

# Case insensitive
reset()
s1, b1 = send("ALTA;Lucia;82")
if s1 == 201:
    s2, b2 = send("CONSULTa;AC-0001;14")
    print(f"  CONSULTa (lowercase a) -> {s2} {b2}")

# Transfer origen = destino
reset()
s1, b1 = send("ALTA;Lucia;82")
if s1 == 201:
    send("DEPOSITO;AC-0001;10000;86")
    s2, b2 = send("TRANSFER;AC-0001;AC-0001;5000;99")
    print(f"  TRANSFER origen=destino -> {s2} {b2}")
    s3, b3 = send("CONSULTA;AC-0001;14")
    print(f"  CONSULTA post self-transfer -> {s3} {b3}")

# Deposito negativo
reset()
s1, b1 = send("ALTA;Lucia;82")
if s1 == 201:
    s2, b2 = send("DEPOSITO;AC-0001;-100;99")
    print(f"  DEPOSITO -100 -> {s2} {b2}")
    if s2 < 400:
        s3, b3 = send("CONSULTA;AC-0001;14")
        print(f"  CONSULTA post negativo -> {s3} {b3}")

# --- SECUENCIA 6: Nuevos controles V2 vs V1 ---
print("\n--- SECUENCIA 6: Comparacion controles ---")
reset()
# ALTA con control V1 correcto
s1, b1 = send("ALTA;Lucia;82")
print(f"  ALTA;Lucia;82 (V1 ctrl) -> {s1} {b1}")
# ALTA con control incorrecto
s2, b2 = send("ALTA;Lucia;83")
print(f"  ALTA;Lucia;83 (+1) -> {s2} {b2}")

# --- SECUENCIA 7: ANULA inexistente ---
print("\n--- SECUENCIA 7: ANULA inexistente ---")
reset()
s1, b1 = send("ALTA;Lucia;82")
if s1 == 201:
    s2, b2 = send("ANULA;OP-9999;99")
    print(f"  ANULA OP-9999 (inexistente) -> {s2} {b2}")

# --- SECUENCIA 8: Ruta inexistente ---
print("\n--- SECUENCIA 8: Rutas ---")
r = httpx.get(f"{URL}/api/v1/test", headers=headers, timeout=15)
print(f"  GET /api/v1/test -> {r.status_code} {r.text}")

print("\n" + "=" * 60)
print("  FIN")
print("=" * 60)
