#!/usr/bin/env python3
"""
Busqueda sistematica del tercer cambio en V2.
Prueba todos los comandos conocidos y busca diferencias.
"""
import httpx, time, json

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}

def send(msg):
    time.sleep(0.12)
    try:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=15)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        return r.status_code, body
    except Exception as e:
        return -1, str(e)

def reset():
    time.sleep(0.12)
    httpx.post(f"{URL}/__reset", headers=headers, timeout=15)

def find_ctrl(prefix):
    for c in range(100):
        status, body = send(f"{prefix};{c}")
        if status < 400:
            return c, status, body
    return None, None, None

print("=" * 60)
print("  BUSQUEDA DEL TERCER CAMBIO V2")
print("=" * 60)

# --- Prueba 1: ANULA con control valido para op existente ---
print("\n--- Prueba 1: ANULA con control correcto ---")
reset()
s1, b1 = send("ALTA;Lucia;82")
s2, b2 = send("ALTA;Mateo;3")
if s1 == 201 and s2 == 201:
    send("DEPOSITO;AC-0001;250000;86")
    s3, b3 = send("TRANSFER;AC-0001;AC-0002;40000;86")
    print(f"  TRANSFER 40000 -> {s3} {b3}")
    if s3 == 200:
        op_id = b3["operacionId"]
        # Buscar control correcto para ANULA de esta op
        ctrl, _, _ = find_ctrl(f"ANULA;{op_id}")
        if ctrl is not None:
            print(f"  ANULA;{op_id} control V2 -> {ctrl}")
            # Primera anulacion con control correcto
            s4, b4 = send(f"ANULA;{op_id};{ctrl}")
            print(f"  ANULA 1ra (ctrl correcto) -> {s4} {b4}")
            # Segunda
            s5, b5 = send(f"ANULA;{op_id};{ctrl}")
            print(f"  ANULA 2da (ctrl correcto) -> {s5} {b5}")
            
            # Anular con mismo control pero op inexistente
            s6, b6 = send(f"ANULA;OP-9999;{ctrl}")
            print(f"  ANULA OP-9999 (ctrl valido, op inexistente) -> {s6} {b6}")
            
            # Verificar saldos
            s7, b7 = send("CONSULTA;AC-0001;14")
            print(f"  CONSULTA AC-0001 post-anula -> {s7} {b7}")
            s8, b8 = send("CONSULTA;AC-0002;11")
            print(f"  CONSULTA AC-0002 post-anula -> {s8} {b8}")

# --- Prueba 2: DEPOSITO con control correcto para montos variados ---
print("\n--- Prueba 2: DEPOSITO montos variados ---")
reset()
s1, b1 = send("ALTA;Lucia;82")
if s1 == 201:
    for monto in [1, 100, 1000, 10000]:
        acc = "AC-0001"
        ctrl, status, body = find_ctrl(f"DEPOSITO;{acc};{monto}")
        print(f"  DEPOSITO;{acc};{monto} ctrl={ctrl} -> {status} {body}")

# --- Prueba 3: TRANSFER con valores cercanos al limite ---
print("\n--- Prueba 3: TRANSFER limite exacto ---")
reset()
s1, b1 = send("ALTA;Lucia;82")
s2, b2 = send("ALTA;Mateo;3")
if s1 == 201 and s2 == 201:
    send("DEPOSITO;AC-0001;300000;86")
    # Probar 99999 (deberia pasar si nuevo limite es < 100000)
    s3, b3 = send("TRANSFER;AC-0001;AC-0002;99999;99")
    print(f"  TRANSFER 99999 ctrl=99 -> {s3} {b3}")
    ctrl, status, body = find_ctrl("TRANSFER;AC-0001;AC-0002;99999")
    print(f"  TRANSFER 99999 ctrl V2={ctrl} -> {status} {body}")
    # Probar 100000
    ctrl2, status2, body2 = find_ctrl("TRANSFER;AC-0001;AC-0002;100000")
    print(f"  TRANSFER 100000 ctrl V2={ctrl2} -> {status2} {body2}")
    # Probar 50000
    ctrl3, status3, body3 = find_ctrl("TRANSFER;AC-0001;AC-0002;50000")
    print(f"  TRANSFER 50000 ctrl V2={ctrl3} -> {status3} {body3}")

# --- Prueba 4: ANULA DEPOSITO con control correcto ---
print("\n--- Prueba 4: ANULA DEPOSITO ---")
reset()
s1, b1 = send("ALTA;Lucia;82")
if s1 == 201:
    ctrl, status, body = find_ctrl("DEPOSITO;AC-0001;1000")
    print(f"  DEPOSITO 1000 ctrl={ctrl} -> {status} {body}")
    if status == 200:
        op_id = body["operacionId"]
        ctrl2, _, _ = find_ctrl(f"ANULA;{op_id}")
        print(f"  ANULA;{op_id} ctrl={ctrl2} -> ", end="")
        s2, b2 = send(f"ANULA;{op_id};{ctrl2}")
        print(f"{s2} {b2}")
        # Verificar saldo post-anula
        s3, b3 = send("CONSULTA;AC-0001;14")
        print(f"  CONSULTA post-anula -> {s3} {b3}")

# --- Prueba 5: Nuevos comandos o comportamientos ---
print("\n--- Prueba 5: Posibles nuevos comandos ---")
for cmd in ["BALANCE", "SALDO", "LIST", "OP", "OPS", "HIST", "HISTORIAL", "ESTADO", "INFO"]:
    s, b = send(f"{cmd};AC-0001;99")
    print(f"  {cmd} -> {s} {b}")

# --- Prueba 6: Comportamientos con texto vacio ---
print("\n--- Prueba 6: Edge case strings ---")
s, b = send("")
print(f"  msg vacio -> {s} {b}")
s, b = send("PING")
print(f"  PING sin control -> {s} {b}")

print("\n" + "=" * 60)
print("  FIN")
print("=" * 60)
