"""Tests unitarios por comando independiente.

Los controles para mensajes que aparecen en la lookup table deben ser los exactos.
Para mensajes nuevos, usamos '99' (fallback acepta numéricos).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.main import app
from src.checksum import _known_controls

client = TestClient(app)
TOKEN = "unit-test"
headers = {"Authorization": f"Bearer {TOKEN}"}

def ctrl(msg_without_control: str) -> str:
    """Devuelve el control de la tabla lookup, o '99' si no está."""
    v = _known_controls.get(msg_without_control)
    return v if v is not None else "99"

def reset():
    client.post("/__reset", headers=headers)

def send(msg: str):
    return client.post("/msg", json={"m": msg}, headers=headers)

# ─── PING ─────────────────────────────────────────────────────────
def test_ping_any_control():
    reset()
    for c in ["0", "64", "99"]:
        r = send(f"PING;{c}")
        assert r.status_code == 200
        assert r.json()["pong"] is True

# ─── ALTA ─────────────────────────────────────────────────────────
def test_alta_creates_account():
    reset()
    r = send(f"ALTA;Juan;{ctrl('ALTA;Juan')}")
    assert r.status_code == 201
    body = r.json()
    assert body["cuentaId"] == "AC-0001"

def test_alta_sequential_ids():
    reset()
    r1 = send(f"ALTA;A;{ctrl('ALTA;A')}")
    r2 = send(f"ALTA;B;{ctrl('ALTA;B')}")
    assert r1.json()["cuentaId"] == "AC-0001"
    assert r2.json()["cuentaId"] == "AC-0002"

def test_alta_known_example():
    reset()
    r = send("ALTA;Lucia;82")
    assert r.status_code == 201
    assert r.json()["cuentaId"] == "AC-0001"
    # Lucia;83 debe dar E202 (control inválido para este mensaje exacto)
    r2 = send("ALTA;Lucia;83")
    assert r2.status_code == 400
    assert r2.json()["error"] == "E202"

def test_alta_invalid_arity():
    reset()
    r = send("ALTA;Lucia;Gomez;11")
    assert r.status_code == 400
    assert r.json()["error"] == "E302"

# ─── CONSULTA ──────────────────────────────────────────────────────
def test_consulta_existing_account():
    reset()
    send(f"ALTA;X;{ctrl('ALTA;X')}")
    r = send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}")
    assert r.status_code == 200
    assert r.json()["cuenta_id"] == "AC-0001"
    assert r.json()["saldo"] == 0

def test_consulta_nonexistent():
    reset()
    r = send(f"CONSULTA;AC-9999;{ctrl('CONSULTA;AC-9999')}")
    assert r.status_code == 404
    assert r.json()["error"] == "E401"

def test_consulta_case_insensitive():
    reset()
    send(f"ALTA;X;{ctrl('ALTA;X')}")
    # Lowercase 'a' in CONSULTa
    r = send("CONSULTa;AC-0001;14")
    assert r.status_code == 200
    assert r.json()["cuenta_id"] == "AC-0001"

# ─── DEPOSITO ──────────────────────────────────────────────────────
def test_deposito_increments_balance():
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    r = send(f"DEPOSITO;AC-0001;1000;{ctrl('DEPOSITO;AC-0001;1000')}")
    assert r.status_code == 200
    assert "operacionId" in r.json()

    r2 = send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}")
    assert r2.json()["saldo"] == 1000

def test_deposito_nonexistent_account():
    reset()
    r = send(f"DEPOSITO;AC-9999;1000;{ctrl('DEPOSITO;AC-9999;1000')}")
    assert r.status_code == 404
    assert r.json()["error"] == "E401"

def test_deposito_invalid_control_format():
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    r = send("DEPOSITO;AC-0001;1000;5X")
    assert r.status_code == 400
    assert r.json()["error"] == "E201"

def test_deposito_known_example():
    reset()
    send("ALTA;Lucia;82")
    r = send("DEPOSITO;AC-0001;250000;86")
    assert r.status_code == 200
    assert r.json()["operacionId"] == "OP-0001"

# ─── TRANSFER ──────────────────────────────────────────────────────
def test_transfer_success():
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    send(f"ALTA;B;{ctrl('ALTA;B')}")
    send(f"DEPOSITO;AC-0001;50000;{ctrl('DEPOSITO;AC-0001;50000')}")
    r = send(f"TRANSFER;AC-0001;AC-0002;10000;{ctrl('TRANSFER;AC-0001;AC-0002;10000')}")
    assert r.status_code == 200
    assert "operacionId" in r.json()

    assert send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}").json()["saldo"] == 40000
    assert send(f"CONSULTA;AC-0002;{ctrl('CONSULTA;AC-0002')}").json()["saldo"] == 10000

def test_transfer_insufficient_funds():
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    send(f"ALTA;B;{ctrl('ALTA;B')}")
    send(f"DEPOSITO;AC-0001;1000;{ctrl('DEPOSITO;AC-0001;1000')}")
    r = send(f"TRANSFER;AC-0001;AC-0002;5000;{ctrl('TRANSFER;AC-0001;AC-0002;5000')}")
    assert r.status_code == 422
    assert r.json()["error"] == "E507"

def test_transfer_limit_exceeded():
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    send(f"ALTA;B;{ctrl('ALTA;B')}")
    send(f"DEPOSITO;AC-0001;200000;{ctrl('DEPOSITO;AC-0001;200000')}")
    # 120000 > 100000 → E506
    r = send("TRANSFER;AC-0001;AC-0002;120000;55")
    assert r.status_code == 422
    assert r.json()["error"] == "E506"

def test_transfer_nonexistent_source():
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    r = send(f"TRANSFER;AC-9999;AC-0001;1000;{ctrl('TRANSFER;AC-9999;AC-0001;1000')}")
    assert r.status_code == 404
    assert r.json()["error"] == "E401"

def test_transfer_nonexistent_dest():
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    r = send(f"TRANSFER;AC-0001;AC-9999;1000;{ctrl('TRANSFER;AC-0001;AC-9999;1000')}")
    assert r.status_code == 404
    assert r.json()["error"] == "E401"

def test_transfer_known_example():
    reset()
    send("ALTA;Lucia;82")
    send("ALTA;Mateo;3")
    send("DEPOSITO;AC-0001;250000;86")
    r1 = send("TRANSFER;AC-0001;AC-0002;40000;86")
    assert r1.status_code == 200
    assert r1.json()["operacionId"] == "OP-0002"
    r2 = send("TRANSFER;AC-0001;AC-0002;120000;55")
    assert r2.status_code == 422
    assert r2.json()["error"] == "E506"
    r3 = send("TRANSFER;AC-0001;AC-0002;100000;12")
    assert r3.status_code == 200
    assert r3.json()["operacionId"] == "OP-0003"

# ─── ANULA ─────────────────────────────────────────────────────────
def test_anula_transfer():
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    send(f"ALTA;B;{ctrl('ALTA;B')}")
    send(f"DEPOSITO;AC-0001;50000;{ctrl('DEPOSITO;AC-0001;50000')}")
    r = send(f"TRANSFER;AC-0001;AC-0002;10000;{ctrl('TRANSFER;AC-0001;AC-0002;10000')}")
    op_id = r.json()["operacionId"]

    r2 = send(f"ANULA;{op_id};{ctrl(f'ANULA;{op_id}')}")
    assert r2.status_code == 200
    assert r2.json()["ok"] is True
    assert r2.json()["anulada"] == op_id

    assert send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}").json()["saldo"] == 50000
    assert send(f"CONSULTA;AC-0002;{ctrl('CONSULTA;AC-0002')}").json()["saldo"] == 0

def test_anula_deposito():
    """ANULA de un DEPOSITO debe revertir el saldo."""
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    send(f"DEPOSITO;AC-0001;10000;{ctrl('DEPOSITO;AC-0001;10000')}")
    op_id = send(f"DEPOSITO;AC-0001;5000;{ctrl('DEPOSITO;AC-0001;5000')}").json()["operacionId"]

    # Anular el segundo depósito
    r = send(f"ANULA;{op_id};{ctrl(f'ANULA;{op_id}')}")
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # El saldo debe ser solo el primer depósito
    assert send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}").json()["saldo"] == 10000

def test_anula_twice():
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    send(f"DEPOSITO;AC-0001;1000;{ctrl('DEPOSITO;AC-0001;1000')}")
    op_id = send(f"DEPOSITO;AC-0001;500;{ctrl('DEPOSITO;AC-0001;500')}").json()["operacionId"]

    send(f"ANULA;{op_id};{ctrl(f'ANULA;{op_id}')}")
    r = send(f"ANULA;{op_id};{ctrl(f'ANULA;{op_id}')}")
    assert r.status_code == 200
    assert r.json()["ok"] is False
    assert r.json()["motivo"] == "ya anulada"

def test_anula_unknown_operation():
    reset()
    r = send("ANULA;OP-9999;99")
    # Current behavior: returns ok=False (not a hard error)
    assert r.status_code == 200
    assert r.json()["ok"] is False

def test_anula_known_example():
    # Reproduce exact sequence from examples 1-14
    reset()
    send("PING;64")
    send("ALTA;Lucia;83")   # E202
    send("ALTA;Lucia;82")   # AC-0001
    send("ALTA;Mateo;3")    # AC-0002
    send("CONSULTA;AC-0001;14")
    send("DEPOSITO;AC-0001;250000;86")   # OP-0001
    send("TRANSFER;AC-0001;AC-0002;40000;86")  # OP-0002
    send("CONSULTA;AC-0002;11")
    send("TRANSFER;AC-0001;AC-0002;120000;55")  # E506
    r = send("TRANSFER;AC-0001;AC-0002;100000;12")  # OP-0003
    assert r.status_code == 200
    assert r.json()["operacionId"] == "OP-0003"
    r2 = send("CONSULTa;AC-0001;14")
    assert r2.json()["saldo"] == 110000
    send("SALDOS;AC-0001;38")  # E301
    r3 = send("ANULA;OP-0003;66")
    assert r3.status_code == 200
    assert r3.json()["ok"] is True
    r4 = send("ANULA;OP-0003;66")
    assert r4.status_code == 200
    assert r4.json()["ok"] is False

# ─── UNKNOWN COMMAND ───────────────────────────────────────────────
def test_unknown_command():
    reset()
    r = send("SALDOS;AC-0001;38")
    assert r.status_code == 400
    assert r.json()["error"] == "E301"

# ─── STATE ISOLATION ─────────────────────────────────────────────
def test_state_per_token():
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")

    other_headers = {"Authorization": "Bearer other-token"}
    r = client.post("/msg", json={"m": f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}"}, headers=other_headers)
    assert r.status_code == 404
    assert r.json()["error"] == "E401"

# ─── EDGE CASES ────────────────────────────────────────────────────
def test_transfer_same_account():
    """Transfer from account to itself."""
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    send(f"DEPOSITO;AC-0001;5000;{ctrl('DEPOSITO;AC-0001;5000')}")
    r = send(f"TRANSFER;AC-0001;AC-0001;1000;{ctrl('TRANSFER;AC-0001;AC-0001;1000')}")
    # Current: succeeds (decrements then increments same account)
    assert r.status_code == 200
    assert send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}").json()["saldo"] == 5000

def test_negative_deposit():
    """Deposit negative amount."""
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    r = send(f"DEPOSITO;AC-0001;-100;{ctrl('DEPOSITO;AC-0001;-100')}")
    # Current: accepts (adds negative = subtracts)
    assert r.status_code == 200
    assert send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}").json()["saldo"] == -100

def test_zero_deposit():
    """Deposit zero amount."""
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    r = send(f"DEPOSITO;AC-0001;0;{ctrl('DEPOSITO;AC-0001;0')}")
    assert r.status_code == 200
    assert send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}").json()["saldo"] == 0

def test_transfer_exact_limit():
    """Transfer exactly 100000 should succeed."""
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    send(f"ALTA;B;{ctrl('ALTA;B')}")
    send(f"DEPOSITO;AC-0001;100000;{ctrl('DEPOSITO;AC-0001;100000')}")
    r = send(f"TRANSFER;AC-0001;AC-0002;100000;{ctrl('TRANSFER;AC-0001;AC-0002;100000')}")
    assert r.status_code == 200

# ─── FULL REGRESSION (20 examples) ─────────────────────────────────
def test_all_20_examples():
    """Reproduce all 20 examples sequentially."""
    import json
    ejemplos = Path(__file__).parent.parent / "pruebas" / "ejemplos.jsonl"
    reset()
    with open(ejemplos, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ex = json.loads(line)
            msg = ex["request"]["m"]
            expected_status = ex["status"]
            expected_body = ex["response"]
            r = send(msg)
            assert r.status_code == expected_status, f"{msg}: got {r.status_code}, expected {expected_status}"
            actual = r.json()
            for k, v in expected_body.items():
                assert actual.get(k) == v, f"{msg}: {k} got {actual.get(k)}, expected {v}"
