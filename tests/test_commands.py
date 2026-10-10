"""Tests unitarios por comando - datos conocidos solamente."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.main import app
from src.checksum import _known_controls, compute_control_consulta

client = TestClient(app)
TOKEN = "unit-test"
headers = {"Authorization": f"Bearer {TOKEN}"}


def ctrl(msg_without_control: str) -> str:
    v = _known_controls.get(msg_without_control)
    if v is not None:
        return v
    if msg_without_control.upper().startswith("CONSULTA;"):
        return compute_control_consulta(msg_without_control.upper())
    raise ValueError(f"Control desconocido para {msg_without_control}")


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
    r = send("ALTA;Lucia;82")
    assert r.status_code == 201
    assert r.json()["cuentaId"] == "AC-0001"


def test_alta_sequential_ids():
    reset()
    r1 = send("ALTA;Lucia;82")
    r2 = send("ALTA;Mateo;3")
    assert r1.json()["cuentaId"] == "AC-0001"
    assert r2.json()["cuentaId"] == "AC-0002"


def test_alta_known_example():
    reset()
    r = send("ALTA;Lucia;82")
    assert r.status_code == 201
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
    send("ALTA;Lucia;82")
    r = send("CONSULTA;AC-0001;14")
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
    send("ALTA;Lucia;82")
    r = send("CONSULTa;AC-0001;14")
    assert r.status_code == 200
    assert r.json()["cuenta_id"] == "AC-0001"


# ─── DEPOSITO ──────────────────────────────────────────────────────
def test_deposito_increments_balance():
    reset()
    send("ALTA;Lucia;82")
    send("DEPOSITO;AC-0001;250000;86")
    r = send("CONSULTA;AC-0001;14")
    assert r.json()["saldo"] == 250000


def test_deposito_nonexistent_account():
    reset()
    r = send("DEPOSITO;AC-9999;1000;99")
    assert r.status_code == 400
    assert r.json()["error"] == "E202"


def test_deposito_invalid_control_format():
    reset()
    send("ALTA;Lucia;82")
    r = send("DEPOSITO;AC-0001;250000;5X")
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
    send("ALTA;Lucia;82")
    send("ALTA;Mateo;3")
    send("DEPOSITO;AC-0001;250000;86")
    r = send("TRANSFER;AC-0001;AC-0002;40000;86")
    assert r.status_code == 200
    assert r.json()["operacionId"] == "OP-0002"
    assert send("CONSULTA;AC-0001;14").json()["saldo"] == 210000
    assert send("CONSULTA;AC-0002;11").json()["saldo"] == 40000


def test_transfer_insufficient_funds():
    reset()
    send("ALTA;Lucia;82")
    send("ALTA;Mateo;3")
    send("DEPOSITO;AC-0001;250000;86")
    send("TRANSFER;AC-0001;AC-0002;40000;86")
    r = send("TRANSFER;AC-0002;AC-0001;50000;23")
    assert r.status_code == 422
    assert r.json()["error"] == "E507"


def test_transfer_limit_exceeded():
    reset()
    send("ALTA;Lucia;82")
    send("ALTA;Mateo;3")
    send("DEPOSITO;AC-0001;250000;86")
    r = send("TRANSFER;AC-0001;AC-0002;120000;55")
    assert r.status_code == 422
    assert r.json()["error"] == "E506"


def test_transfer_nonexistent_source():
    reset()
    send("ALTA;Lucia;82")
    r = send("TRANSFER;AC-9999;AC-0001;1000;99")
    assert r.status_code == 400
    assert r.json()["error"] == "E202"


def test_transfer_nonexistent_dest():
    reset()
    send("ALTA;Lucia;82")
    r = send("TRANSFER;AC-0001;AC-9999;1000;99")
    assert r.status_code == 400
    assert r.json()["error"] == "E202"


def test_transfer_known_example():
    reset()
    send("ALTA;Lucia;82")
    send("ALTA;Mateo;3")
    send("DEPOSITO;AC-0001;250000;86")
    r1 = send("TRANSFER;AC-0001;AC-0002;40000;86")
    assert r1.json()["operacionId"] == "OP-0002"
    r2 = send("TRANSFER;AC-0001;AC-0002;120000;55")
    assert r2.status_code == 422
    assert r2.json()["error"] == "E506"
    r3 = send("TRANSFER;AC-0001;AC-0002;100000;12")
    assert r3.status_code == 200
    assert r3.json()["operacionId"] == "OP-0003"


# ─── ANULA ─────────────────────────────────────────────────────────
def test_anula_known_example():
    reset()
    send("PING;64")
    assert send("ALTA;Lucia;83").status_code == 400
    send("ALTA;Lucia;82")
    send("ALTA;Mateo;3")
    send("CONSULTA;AC-0001;14")
    send("DEPOSITO;AC-0001;250000;86")
    send("TRANSFER;AC-0001;AC-0002;40000;86")
    send("CONSULTA;AC-0002;11")
    assert send("TRANSFER;AC-0001;AC-0002;120000;55").status_code == 422
    r = send("TRANSFER;AC-0001;AC-0002;100000;12")
    assert r.status_code == 200
    assert r.json()["operacionId"] == "OP-0003"
    assert send("CONSULTa;AC-0001;14").json()["saldo"] == 110000
    assert send("SALDOS;AC-0001;38").status_code == 400
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
    send("ALTA;Lucia;82")
    other = {"Authorization": "Bearer other-token"}
    r = client.post("/msg", json={"m": "CONSULTA;AC-0001;14"}, headers=other)
    assert r.status_code == 404
    assert r.json()["error"] == "E401"


# ─── FULL REGRESSION (20 examples) ─────────────────────────────────
def test_all_20_examples():
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
            assert r.status_code == expected_status, f"{msg}: {r.status_code}"
            actual = r.json()
            for k, v in expected_body.items():
                assert actual.get(k) == v, f"{msg}: {k}={actual.get(k)} expected={v}"
