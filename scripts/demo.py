#!/usr/bin/env python3
"""
Demo interactiva del reemplazo Black Box.
Ejecuta una secuencia completa de operaciones mostrando requests y responses.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
TOKEN = "demo-token"
headers = {"Authorization": f"Bearer {TOKEN}"}

def call(name, msg, expected_status=None):
    r = client.post("/msg", json={"m": msg}, headers=headers)
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
    status = "[OK]" if expected_status is None or r.status_code == expected_status else "[FAIL]"
    print(f"\n  {status} {name}")
    print(f"     -> POST /msg  {{m: '{msg}'}}")
    print(f"     <- {r.status_code} {json.dumps(body, ensure_ascii=False)}")
    return r.status_code, body

def reset():
    r = client.post("/__reset", headers=headers)
    print(f"\n  [RESET]")
    print(f"     -> POST /__reset")
    print(f"     <- {r.status_code} {r.text}")

print("=" * 60)
print("  DEMO: Black Box Replacement")
print("=" * 60)

# 1. PING
reset()
call("PING", "PING;64", 200)

# 2. ALTA cuenta Lucia
call("ALTA Lucia", "ALTA;Lucia;82", 201)

# 3. ALTA cuenta Mateo
call("ALTA Mateo", "ALTA;Mateo;3", 201)

# 4. CONSULTA AC-0001 (debe tener 0)
call("CONSULTA AC-0001", "CONSULTA;AC-0001;14", 200)

# 5. DEPOSITO 250000 a AC-0001
call("DEPOSITO AC-0001", "DEPOSITO;AC-0001;250000;86", 200)

# 6. TRANSFER 40000 AC-0001 → AC-0002
call("TRANSFER 40K", "TRANSFER;AC-0001;AC-0002;40000;86", 200)

# 7. CONSULTA AC-0002 (debe tener 40000)
call("CONSULTA AC-0002", "CONSULTA;AC-0002;11", 200)

# 8. TRANSFER 120000 → debe fallar por límite
call("TRANSFER 120K (límite excedido)", "TRANSFER;AC-0001;AC-0002;120000;55", 422)

# 9. TRANSFER 100000 → debe pasar
call("TRANSFER 100K", "TRANSFER;AC-0001;AC-0002;100000;12", 200)

# 10. CONSULTA AC-0001 (debe tener 110000)
call("CONSULTA AC-0001 post-transfer", "CONSULTA;AC-0001;14", 200)

# 11. Case insensitive: CONSULTa
call("CONSULTa (case insensitive)", "CONSULTa;AC-0001;14", 200)

# 12. Comando desconocido: SALDOS
call("SALDOS (desconocido)", "SALDOS;AC-0001;38", 400)

# 13. ANULA OP-0003 (la transfer de 100K)
call("ANULA OP-0003", "ANULA;OP-0003;66", 200)

# 14. Doble ANULA → ya anulada
call("ANULA OP-0003 (doble)", "ANULA;OP-0003;66", 200)

# 15. Cuenta inexistente
call("CONSULTA inexistente", "CONSULTA;AC-0009;87", 404)

# 16. Saldo insuficiente
call("TRANSFER sin saldo", "TRANSFER;AC-0002;AC-0001;50000;23", 422)

# 17. Control mal formado
call("DEPOSITO control 5X", "DEPOSITO;AC-0002;700;5X", 400)

# 18. DEPOSITO válido
call("DEPOSITO AC-0002 700", "DEPOSITO;AC-0002;700;35", 200)

# 19. CONSULTA AC-0002 final
call("CONSULTA AC-0002 final", "CONSULTA;AC-0002;11", 200)

# 20. Aridad inválida
call("ALTA aridad inválida", "ALTA;Lucia;Gomez;11", 400)

print("\n" + "=" * 60)
print("  [OK] DEMO COMPLETA: 20/20 ejemplos ejecutados")
print("=" * 60)
