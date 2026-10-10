#!/usr/bin/env python3
"""Simulacion hackathon REALISTA - 100 casos contra Railway."""
import httpx, time, json, random
from pathlib import Path

URL = "https://caja-negra-replacement-production.up.railway.app"
TOKEN = "cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs"
headers = {"Authorization": f"Bearer {TOKEN}"}

all_results = []

def reset():
    httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
    time.sleep(0.3)

def send(msg):
    try:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=10)
        return r.status_code, r.text
    except Exception as e:
        return 999, str(e)

def record(category, msg, status, body, note=""):
    all_results.append({"cat": category, "msg": msg, "status": status, "body": body[:200], "note": note})

print("="*70)
print("SIMULACION HACKATHON REALISTA - 100 CASOS")
print(f"URL: {URL}")
print("="*70)

# ========== 40 FACILES (tabla conocida + ejemplos exactos) ==========
print("\n### FACIL (40) - Datos conocidos, deben pasar casi todos ###")
reset()

facil = [
    # Los 20 ejemplos exactos
    ("PING;64", "200"),
    ("ALTA;Lucia;83", "400"),
    ("ALTA;Lucia;82", "201"),
    ("ALTA;Mateo;3", "201"),
    ("CONSULTA;AC-0001;14", "200"),
    ("DEPOSITO;AC-0001;250000;86", "200"),
    ("TRANSFER;AC-0001;AC-0002;40000;86", "200"),
    ("CONSULTA;AC-0002;11", "200"),
    ("TRANSFER;AC-0001;AC-0002;120000;55", "422"),
    ("TRANSFER;AC-0001;AC-0002;100000;12", "200"),
    ("CONSULTa;AC-0001;14", "200"),
    ("SALDOS;AC-0001;38", "400"),
    ("ANULA;OP-0003;66", "200"),
    ("ANULA;OP-0003;66", "200"),
    ("CONSULTA;AC-0009;87", "404"),
    ("TRANSFER;AC-0002;AC-0001;50000;23", "422"),
    ("DEPOSITO;AC-0002;700;5X", "400"),
    ("DEPOSITO;AC-0002;700;35", "200"),
    ("CONSULTA;AC-0002;11", "200"),
    ("ALTA;Lucia;Gomez;11", "400"),
    # 20 mas de tabla conocida
    ("PING;0", "200"),
    ("PING;99", "200"),
    ("CONSULTA;AC-0001;14", "200"),
    ("CONSULTA;AC-0002;11", "200"),
    ("CONSULTa;AC-0001;14", "200"),
    ("CONSULTA;AC-0009;87", "404"),
    ("ALTA;Lucia;82", "201"),
    ("ALTA;Mateo;3", "201"),
    ("DEPOSITO;AC-0001;250000;86", "200"),
    ("TRANSFER;AC-0001;AC-0002;40000;86", "200"),
    ("TRANSFER;AC-0001;AC-0002;120000;55", "422"),
    ("TRANSFER;AC-0001;AC-0002;100000;12", "200"),
    ("ANULA;OP-0003;66", "200"),
    ("ANULA;OP-0003;66", "200"),
    ("TRANSFER;AC-0002;AC-0001;50000;23", "422"),
    ("DEPOSITO;AC-0002;700;5X", "400"),
    ("DEPOSITO;AC-0002;700;35", "200"),
    ("SALDOS;AC-0001;38", "400"),
    ("ALTA;Lucia;83", "400"),
    ("ALTA;Lucia;Gomez;11", "400"),
]

facil_ok = 0
for msg, exp_status in facil:
    st, body = send(msg)
    ok = str(st) == exp_status
    if ok: facil_ok += 1
    record("FACIL", msg, st, body, "OK" if ok else f"FAIL(exp={exp_status})")
    print(f"  {'OK' if ok else 'XX'} FACIL {msg}")
    time.sleep(0.1)

# ========== 40 REGULARES (nombres/montos nuevos + controles aleatorios 1-2 digitos) ==========
print(f"\n### REGULAR (40) - Nombres/montos nuevos, control aleatorio ###")
reset()
# Primero creamos ALTA conocidas para tener estado
send("ALTA;Lucia;82")
send("ALTA;Mateo;3")
send("DEPOSITO;AC-0001;250000;86")
send("DEPOSITO;AC-0002;700;35")

nombres = ["Juan","Pedro","Maria","Ana","Luis","Carmen","Jose","Diana",
           "Raul","Sofia","Diego","Elena","Pablo","Natalia","Andres","Laura",
           "Carlos","Marta","Jorge","Lina","Fernando","Valentina","Sebastian","Camila"]
montos = ["100","500","1000","5000","10000","50000","75000","99000","100","250","500","1000"]

random.seed(42)
regular = []

# 8 ALTA con nombres nuevos (control aleatorio 1-2 digitos)
for n in nombres[:8]:
    c = str(random.randint(0, 99))
    regular.append((f"ALTA;{n};{c}", "unk"))

# 8 DEPOSITO con montos nuevos sobre AC-0001 (control aleatorio)
for m in montos[:8]:
    c = str(random.randint(0, 99))
    regular.append((f"DEPOSITO;AC-0001;{m};{c}", "unk"))

# 8 TRANSFER con montos nuevos (control aleatorio)
for m in ["1000","5000","10000","20000","30000","40000","50000","60000"]:
    c = str(random.randint(0, 99))
    regular.append((f"TRANSFER;AC-0001;AC-0002;{m};{c}", "unk"))

# 8 CONSULTA a cuentas nuevas (no existen pero formula exacta valida)
for cid in ["AC-0003","AC-0004","AC-0005","AC-0010","AC-0011","AC-0020","AC-0100","AC-0999"]:
    # Formula CONSULTA: (3*(len - asciisum)) % 97
    msg_base = f"CONSULTA;{cid}"
    c = str((3 * (len(msg_base) - sum(ord(ch) for ch in msg_base))) % 97)
    regular.append((f"CONSULTA;{cid};{c}", "404"))  # cuenta no existe (solo AC-0001/2 creadas)

# 8 variaciones conocidas
regular.extend([
    ("PING;0", "200"),
    ("PING;1", "200"),
    ("CONSULTA;AC-0001;14", "200"),
    ("CONSULTA;AC-0002;11", "200"),
    ("TRANSFER;AC-0001;AC-0002;120000;55", "422"),
    ("TRANSFER;AC-0002;AC-0001;50000;23", "422"),
    ("ANULA;OP-0003;66", "200"),
    ("ANULA;OP-0003;66", "200"),
])

regular_ok = 0
for msg, exp_status in regular:
    st, body = send(msg)
    # Para mensajes "unk" aceptamos lo que sea (estamos midiendo comportamiento)
    if exp_status == "unk":
        ok = True  # No sabemos qué esperar, solo registramos
        note = f"GOT_{st}"
    else:
        ok = str(st) == exp_status
        note = "OK" if ok else f"FAIL(exp={exp_status})"
    if ok: regular_ok += 1
    record("REGULAR", msg, st, body, note)
    print(f"  {'OK' if ok else 'XX' if exp_status != 'unk' else '??'} REGULAR {msg} -> {st}")
    time.sleep(0.1)

# ========== 20 DIFICILES ==========
print(f"\n### DIFICIL (20) - Edge cases y secuencias ###")
reset()

# 10 edge cases individuales
edge_cases = [
    (None, "400", "no body"),
    ({}, "400", "body vacio"),
    ({"x": 1}, "400", "sin campo m"),
    ({"m": ""}, "400", "m vacio"),
    ({"m": None}, "400", "m null"),
    ("DEPOSITO;AC-0001;abc;86", "400", "monto abc"),
    ("TRANSFER;AC-0001;AC-0002;abc;12", "400", "monto abc"),
    ("ALTA;Lucia;123", "400", "control >2 digitos"),
    ("CONSULTA;AC-0001;99", "400", "CONSULTA control mal"),
    ("SALDOS;AC-0001;38", "400", "comando desconocido"),
]

# 10 secuencias complejas
dificil_ok = 0
for req, exp, desc in edge_cases:
    if req is None:
        r = httpx.post(f"{URL}/msg", headers=headers, timeout=10)
        st, body = r.status_code, r.text
    elif isinstance(req, dict):
        r = httpx.post(f"{URL}/msg", json=req, headers=headers, timeout=10)
        st, body = r.status_code, r.text
    else:
        st, body = send(req)
    ok = str(st) == exp
    if ok: dificil_ok += 1
    record("DIFICIL", desc, st, body, "OK" if ok else f"FAIL(exp={exp})")
    print(f"  {'OK' if ok else 'XX'} DIFICIL {desc}: {st}")
    time.sleep(0.1)

# Secuencia larga (10 pasos)
reset()
seq = [
    ("ALTA;Lucia;82", "201"),
    ("ALTA;Mateo;3", "201"),
    ("DEPOSITO;AC-0001;250000;86", "200"),
    ("CONSULTA;AC-0001;14", "200"),
    ("TRANSFER;AC-0001;AC-0002;40000;86", "200"),
    ("CONSULTA;AC-0002;11", "200"),
    ("TRANSFER;AC-0001;AC-0002;120000;55", "422"),
    ("TRANSFER;AC-0001;AC-0002;100000;12", "200"),
    ("ANULA;OP-0003;66", "200"),
    ("CONSULTa;AC-0001;14", "200"),
]
seq_ok = True
for msg, exp in seq:
    st, body = send(msg)
    if str(st) != exp:
        seq_ok = False
        record("DIFICIL", f"SEQ_FAIL:{msg}", st, body, f"FAIL(exp={exp})")
        print(f"  XX DIFICIL SEQ {msg}: {st} (exp {exp})")
        break
    time.sleep(0.1)
if seq_ok:
    record("DIFICIL", "SEQ_10_OK", 200, "", "OK")
    print(f"  OK DIFICIL SECUENCIA 10 pasos")
    dificil_ok += 1

# Estado aislado
reset()
send("ALTA;Lucia;82")
r = httpx.post(f"{URL}/msg", json={"m": "CONSULTA;AC-0001;14"},
               headers={"Authorization": "Bearer otro-token"}, timeout=10)
ok = r.status_code == 404
if ok: dificil_ok += 1
record("DIFICIL", "ESTADO_AISLADO", r.status_code, r.text, "OK" if ok else "FAIL")
print(f"  {'OK' if ok else 'XX'} DIFICIL Estado aislado: {r.status_code}")

time.sleep(0.1)

# Auth
r = httpx.post(f"{URL}/__reset", timeout=10)
ok = r.status_code == 401
if ok: dificil_ok += 1
record("DIFICIL", "AUTH", r.status_code, r.text, "OK" if ok else "FAIL")
print(f"  {'OK' if ok else 'XX'} DIFICIL Auth: {r.status_code}")

# Cierre con tabla conocida
reset()
final = [
    ("PING;64", "200"),
    ("ALTA;Lucia;82", "201"),
    ("ALTA;Mateo;3", "201"),
    ("DEPOSITO;AC-0001;250000;86", "200"),
    ("DEPOSITO;AC-0002;700;35", "200"),
    ("TRANSFER;AC-0001;AC-0002;40000;86", "200"),
    ("TRANSFER;AC-0001;AC-0002;100000;12", "200"),
]
for msg, exp in final:
    st, body = send(msg)
    ok = str(st) == exp
    if ok: dificil_ok += 1
    record("DIFICIL", msg, st, body, "OK" if ok else f"FAIL(exp={exp})")
    print(f"  {'OK' if ok else 'XX'} DIFICIL {msg}: {st}")
    time.sleep(0.1)

# ========== RESUMEN ==========
print("\n" + "="*70)
print("RESUMEN")
print("="*70)
print(f"  FACIL:    {facil_ok}/40")
print(f"  REGULAR:  {regular_ok}/40 (incluye {sum(1 for r in regular if r[1]=='unk')} casos 'unknown')")
print(f"  DIFICIL:  {dificil_ok}/20")
print(f"  TOTAL:    {facil_ok + regular_ok + dificil_ok}/100")
print("="*70)

# Guardar
out = Path("scripts/simulacion_realista.json")
out.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nDetalles guardados en: {out}")
