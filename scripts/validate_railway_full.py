#!/usr/bin/env python3
"""
BATERIA COMPLETA DE VALIDACION CONTRA RAILWAY
Ejecutar: python scripts/validate_railway_full.py
"""
import httpx, time, json, sys
from pathlib import Path

URL = "https://caja-negra-replacement-production.up.railway.app"
TOKEN = "cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs"
headers = {"Authorization": f"Bearer {TOKEN}"}
EJEMPLOS = Path("pruebas/ejemplos.jsonl")

passed = 0
failed = 0
server_errors = 0
log_lines = []

def log(msg):
    log_lines.append(msg)
    print(msg)

def send_raw(body=None, data=None, content_type=None):
    """Envia request crudo."""
    h = dict(headers)
    if content_type:
        h["Content-Type"] = content_type
    try:
        if data is not None:
            r = httpx.post(f"{URL}/msg", data=data, headers=h, timeout=15)
        else:
            r = httpx.post(f"{URL}/msg", json=body, headers=h, timeout=15)
        return r.status_code, r.text
    except Exception as e:
        return 999, str(e)

def send(msg_str):
    return send_raw(body={"m": msg_str})

def check(name, status, body_text, expected_status, expected_body_substr=None, check_fn=None):
    global passed, failed, server_errors
    try:
        body = json.loads(body_text) if body_text.startswith("{") else body_text
    except:
        body = body_text
    
    if status >= 500:
        server_errors += 1
        failed += 1
        log(f"  [FAIL] {name}")
        log(f"    SERVER ERROR {status}: {body_text[:200]}")
        return
    
    ok = status == expected_status
    if expected_body_substr:
        ok = ok and expected_body_substr in body_text
    if check_fn:
        try:
            ok = ok and check_fn(body)
        except:
            ok = False
    
    if ok:
        passed += 1
        log(f"  [OK]   {name} -> {status}")
    else:
        failed += 1
        log(f"  [FAIL] {name}")
        log(f"    Expected: {expected_status} {expected_body_substr or ''}")
        log(f"    Got:      {status} {body_text[:200]}")

# ============================================================
log("="*70)
log("BATERIA COMPLETA DE VALIDACION - RAILWAY")
log("URL: " + URL)
log("="*70)

# 1. Reset
log("\n[1] RESET")
st, txt = send_raw(body=None)
check("Reset sin body (debe fallar)", st, txt, 400)
time.sleep(0.5)
st, txt = httpx.post(f"{URL}/__reset", headers=headers, timeout=10).status_code, \
           httpx.post(f"{URL}/__reset", headers=headers, timeout=10).text
check("Reset correcto", st, txt, 200)

# 2. Body vacio / no JSON
log("\n[2] BODY VACIO / NO JSON")
time.sleep(0.5)
st, txt = send_raw(body={})
check("Body vacio {}", st, txt, 400, "E201")
time.sleep(0.5)
st, txt = send_raw(data="not-json", content_type="text/plain")
check("Body no-JSON", st, txt, 400, "E201")
time.sleep(0.5)
st, txt = send_raw(body=[])
check("Body array", st, txt, 400, "E201")
time.sleep(0.5)
st, txt = send_raw(body={"x": 1})
check("Body sin campo m", st, txt, 400, "E201")

# 3. Los 20 ejemplos originales
log("\n[3] 20 EJEMPLOS ORIGINALES")
time.sleep(0.5)
httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
time.sleep(0.5)
with open(EJEMPLOS, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip(): continue
        ex = json.loads(line)
        msg = ex["request"]["m"]
        exp_status = ex["status"]
        exp_body = ex["response"]
        st, txt = send(msg)
        check(f"Ejemplo: {msg}", st, txt, exp_status, check_fn=lambda b, e=exp_body: 
              isinstance(b, dict) and isinstance(e, dict) and all(b.get(k) == v for k, v in e.items()))
        time.sleep(0.3)

# 4. CONSULTA formula exacta
log("\n[4] CONSULTA FORMULA EXACTA")
time.sleep(0.5)
httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
time.sleep(0.5)
# AC-0001 -> 14
check("CONSULTA AC-0001 correcto (14)", *send("CONSULTA;AC-0001;14"), 400, check_fn=lambda b: b.get("error") == "E401")
time.sleep(0.3)
# AC-0001 -> control incorrecto
check("CONSULTA AC-0001 incorrecto (99)", *send("CONSULTA;AC-0001;99"), 400, "E202")
time.sleep(0.3)
# AC-0002 -> control correcto 11
check("CONSULTA AC-0002 correcto (11)", *send("CONSULTA;AC-0002;11"), 400, "E401")
time.sleep(0.3)
# AC-0002 -> control incorrecto
check("CONSULTA AC-0002 incorrecto (99)", *send("CONSULTA;AC-0002;99"), 400, "E202")
time.sleep(0.3)
# AC-0009 -> control correcto 87 (por tabla o formula?)
check("CONSULTA AC-0009 correcto (87)", *send("CONSULTA;AC-0009;87"), 400, "E401")
time.sleep(0.3)

# 5. ALTA secuencial
log("\n[5] ALTA SECUENCIAL")
time.sleep(0.5)
httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
time.sleep(0.5)
check("ALTA A", *send("ALTA;A;62"), 201, check_fn=lambda b: b.get("cuentaId") == "AC-0001")
time.sleep(0.3)
check("ALTA B", *send("ALTA;B;59"), 201, check_fn=lambda b: b.get("cuentaId") == "AC-0002")
time.sleep(0.3)
check("ALTA C", *send("ALTA;C;56"), 201, check_fn=lambda b: b.get("cuentaId") == "AC-0003")
time.sleep(0.3)
check("ALTA control incorrecto", *send("ALTA;A;99"), 400, "E202")
time.sleep(0.3)

# 6. TRANSFER limites
log("\n[6] TRANSFER LIMITES")
time.sleep(0.5)
httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
time.sleep(0.5)
send("ALTA;A;62")
time.sleep(0.3)
send("ALTA;B;59")
time.sleep(0.3)
send("DEPOSITO;AC-0001;200000;86")
time.sleep(0.3)
check("TRANSFER limite exacto (100000)", *send("TRANSFER;AC-0001;AC-0002;100000;12"), 200)
time.sleep(0.3)
check("TRANSFER excede limite (120000)", *send("TRANSFER;AC-0001;AC-0002;120000;55"), 422, "E506")
time.sleep(0.3)
check("TRANSFER sin saldo", *send("TRANSFER;AC-0002;AC-0001;50000;23"), 422, "E507")

# 7. ANULA idempotencia
log("\n[7] ANULA IDEMPOTENCIA")
time.sleep(0.5)
httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
time.sleep(0.5)
send("ALTA;A;62")
time.sleep(0.3)
send("DEPOSITO;AC-0001;1000;35")
time.sleep(0.3)
check("ANULA OK primera vez", *send("ANULA;OP-0001;69"), 200, check_fn=lambda b: b.get("ok") is True)
time.sleep(0.3)
check("ANULA OK segunda vez", *send("ANULA;OP-0001;69"), 200, check_fn=lambda b: b.get("ok") is False)
time.sleep(0.3)
check("ANULA desconocida", *send("ANULA;OP-9999;99"), 200, check_fn=lambda b: b.get("ok") is False)

# 8. PING
log("\n[8] PING")
for c in ["0", "64", "99", "12345"]:
    time.sleep(0.3)
    check(f"PING;{c}", *send(f"PING;{c}"), 200)

# 9. Auth
log("\n[9] AUTH")
time.sleep(0.3)
r = httpx.post(f"{URL}/msg", json={"m": "PING;64"}, timeout=10)
check("Sin auth", r.status_code, r.text, 401)
time.sleep(0.3)
r = httpx.get(f"{URL}/health", timeout=10)
check("Health sin auth", r.status_code, r.text, 401)
time.sleep(0.3)
r = httpx.get(f"{URL}/health", headers=headers, timeout=10)
check("Health con auth", r.status_code, r.text, 200)

# 10. Case insensitive
log("\n[10] CASE INSENSITIVE")
time.sleep(0.5)
httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
time.sleep(0.3)
send("ALTA;Test;99")
time.sleep(0.3)
check("CONSULTa lower", *send("CONSULTa;AC-0001;14"), 200, check_fn=lambda b: b.get("cuenta_id") == "AC-0001")

# ============================================================
log("\n" + "="*70)
log(f"RESULTADO FINAL: {passed} OK / {failed} FAIL / {server_errors} ERRORES SERVIDOR")
log("="*70)
if server_errors == 0 and failed == 0:
    log("ESTADO: PERFECTO. Todo pasa.")
elif server_errors == 0:
    log("ESTADO: El servidor funciona. Revisar fallos de logica.")
else:
    log("ESTADO: HAY ERRORES DE SERVIDOR. Revisar URGENTE.")

# Guardar log
Path("scripts/validation_log.txt").write_text("\n".join(log_lines), encoding="utf-8")
log("\nLog guardado en: scripts/validation_log.txt")
