#!/usr/bin/env python3
"""
Investiga la versión 2 del servicio original.
Compara comportamientos contra V1 conocidos.
"""
import httpx, time, json
from pathlib import Path

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}

EXPERIMENTOS = Path(__file__).parent.parent / "experimentos.jsonl"

def send(msg, seq="v2", hip="", req_n=0):
    time.sleep(0.2)
    try:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=15)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        return r.status_code, body
    except Exception as e:
        return -1, str(e)

def reset():
    time.sleep(0.2)
    httpx.post(f"{URL}/__reset", headers=headers, timeout=15)

def log(seq, x_req, hip, request, status, response, conclusion=""):
    # Append to experimentos.jsonl
    with open(EXPERIMENTOS, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    last_id = json.loads(lines[-1])["id"] if lines else 0
    entry = {
        "id": last_id + 1,
        "seq": seq,
        "x_req": x_req,
        "hipotesis": hip,
        "request": request,
        "status": status,
        "response": response,
        "conclusion": conclusion
    }
    with open(EXPERIMENTOS, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  [{last_id+1}] {hip} -> {status} {json.dumps(response, ensure_ascii=False)}")

print("=" * 60)
print("  INVESTIGACION V2 — Comparativa contra V1")
print("=" * 60)

# 1. Health + auth
print("\n--- 1. Health / Auth ---")
r = httpx.get(f"{URL}/health", headers=headers, timeout=15)
print(f"  GET /health (con token): {r.status_code} {r.text}")
r = httpx.get(f"{URL}/health", timeout=15)
print(f"  GET /health (sin token): {r.status_code} {r.text}")
r = httpx.post(f"{URL}/__reset", headers=headers, timeout=15)
print(f"  POST /__reset: {r.status_code} {r.text}")

# 2. PING
print("\n--- 2. PING ---")
for ctrl in ["64", "0", "99"]:
    status, body = send(f"PING;{ctrl}")
    print(f"  PING;{ctrl}: {status} {body}")

# 3. ALTA (probemos varios nombres)
print("\n--- 3. ALTA ---")
reset()
for name in ["Lucia", "Mateo", "Test"]:
    status, body = send(f"ALTA;{name};99")
    print(f"  ALTA;{name};99: {status} {body}")

# 4. ALTA con control correcto de V1
print("\n--- 4. ALTA con controles V1 ---")
reset()
for msg in ["ALTA;Lucia;82", "ALTA;Mateo;3"]:
    status, body = send(msg)
    print(f"  {msg}: {status} {body}")

# 5. CONSULTA
print("\n--- 5. CONSULTA ---")
reset()
# Crear cuenta
status, body = send("ALTA;Test;99")
print(f"  ALTA;Test;99 -> {status} {body}")
if status == 201:
    cuenta = body.get("cuentaId", "AC-0001")
    # CONSULTA
    for ctrl in ["14", "99", "0"]:
        status2, body2 = send(f"CONSULTA;{cuenta};{ctrl}")
        print(f"  CONSULTA;{cuenta};{ctrl}: {status2} {body2}")

# 6. DEPOSITO
print("\n--- 6. DEPOSITO ---")
reset()
status, body = send("ALTA;Test;99")
if status == 201:
    cuenta = body.get("cuentaId", "AC-0001")
    for msg in [f"DEPOSITO;{cuenta};1000;99", f"DEPOSITO;{cuenta};250000;86"]:
        status2, body2 = send(msg)
        print(f"  {msg}: {status2} {body2}")

# 7. TRANSFER
print("\n--- 7. TRANSFER ---")
reset()
status1, body1 = send("ALTA;A;99")
status2, body2 = send("ALTA;B;99")
if status1 == 201 and status2 == 201:
    acc1 = body1["cuentaId"]
    acc2 = body2["cuentaId"]
    # Depositar
    send(f"DEPOSITO;{acc1};50000;99")
    # Transfer
    for msg in [f"TRANSFER;{acc1};{acc2};40000;99", f"TRANSFER;{acc1};{acc2};120000;99"]:
        status3, body3 = send(msg)
        print(f"  {msg}: {status3} {body3}")

# 8. ANULA
print("\n--- 8. ANULA ---")
reset()
status1, body1 = send("ALTA;A;99")
status2, body2 = send("ALTA;B;99")
if status1 == 201 and status2 == 201:
    acc1 = body1["cuentaId"]
    acc2 = body2["cuentaId"]
    send(f"DEPOSITO;{acc1};10000;99")
    status3, body3 = send(f"TRANSFER;{acc1};{acc2};5000;99")
    if status3 == 200:
        op_id = body3.get("operacionId", "OP-0001")
        # Anular
        status4, body4 = send(f"ANULA;{op_id};99")
        print(f"  ANULA;{op_id};99 (1ra): {status4} {body4}")
        # Anular de nuevo
        status5, body5 = send(f"ANULA;{op_id};99")
        print(f"  ANULA;{op_id};99 (2da): {status5} {body5}")

# 9. Errores conocidos
print("\n--- 9. Errores ---")
tests = [
    ("ALTA;Lucia;Gomez;11", "Aridad invalida"),
    ("DEPOSITO;AC-0001;700;5X", "Control mal formado"),
    ("CONSULTA;AC-9999;99", "Cuenta inexistente"),
    ("SALDOS;AC-0001;38", "Comando desconocido"),
]
for msg, desc in tests:
    status, body = send(msg)
    print(f"  {desc} ({msg}): {status} {body}")

# 10. Nuevos comportamientos a explorar
print("\n--- 10. Nuevos comportamientos a explorar ---")
# TRANSFER con monto exacto 100000
reset()
s1, b1 = send("ALTA;A;99")
s2, b2 = send("ALTA;B;99")
if s1 == 201 and s2 == 201:
    acc1 = b1["cuentaId"]
    acc2 = b2["cuentaId"]
    send(f"DEPOSITO;{acc1};100000;99")
    s3, b3 = send(f"TRANSFER;{acc1};{acc2};100000;99")
    print(f"  TRANSFER exacto 100000: {s3} {b3}")

# DEPOSITO con monto negativo
reset()
s1, b1 = send("ALTA;A;99")
if s1 == 201:
    acc = b1["cuentaId"]
    s2, b2 = send(f"DEPOSITO;{acc};-100;99")
    print(f"  DEPOSITO negativo: {s2} {b2}")

# ANULA operacion inexistente
reset()
s1, b1 = send("ALTA;A;99")
if s1 == 201:
    s2, b2 = send("ANULA;OP-9999;99")
    print(f"  ANULA inexistente: {s2} {b2}")

print("\n" + "=" * 60)
print("  FIN DE INVESTIGACION")
print("=" * 60)
