#!/usr/bin/env python3
"""Tests para la Version 2 del servicio - datos conocidos solamente."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.main import app
from src.checksum import _known_controls, compute_control_consulta

client = TestClient(app)
TOKEN = "test-v2"
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


def test_consulta_saldo_formato_v2():
    reset()
    send("ALTA;Lucia;82")
    send("DEPOSITO;AC-0001;250000;86")
    r = send("CONSULTA;AC-0001;14")
    assert r.status_code == 200
    assert r.json()["cuenta_id"] == "AC-0001"
    assert r.json()["saldo"] == 250000


def test_saldo_despues_transfer_v2():
    reset()
    send("ALTA;Lucia;82")
    send("ALTA;Mateo;3")
    send("DEPOSITO;AC-0001;250000;86")
    send("TRANSFER;AC-0001;AC-0002;40000;86")
    r1 = send("CONSULTA;AC-0001;14")
    r2 = send("CONSULTA;AC-0002;11")
    assert r1.json()["saldo"] == 210000
    assert r2.json()["saldo"] == 40000


def test_comandos_desconocido_v2():
    reset()
    r = send("SALDOS;AC-0001;38")
    assert r.status_code == 400
    assert r.json()["error"] == "E301"


def test_cuenta_inexistente_v2():
    reset()
    r = send(f"CONSULTA;AC-9999;{ctrl('CONSULTA;AC-9999')}")
    assert r.status_code == 404
    assert r.json()["error"] == "E401"


def test_aridad_invalida_v2():
    reset()
    r = send("ALTA;Lucia;Gomez;11")
    assert r.status_code == 400
    assert r.json()["error"] == "E302"


def test_control_mal_formado_v2():
    reset()
    r = send("DEPOSITO;AC-0001;250000;5X")
    assert r.status_code == 400
    assert r.json()["error"] == "E201"


def test_ping_v2():
    reset()
    for c in ["64", "0", "99"]:
        r = send(f"PING;{c}")
        assert r.status_code == 200
        assert r.json()["pong"] is True


def test_alta_secuencial_v2():
    reset()
    r1 = send("ALTA;Lucia;82")
    r2 = send("ALTA;Mateo;3")
    assert r1.json()["cuentaId"] == "AC-0001"
    assert r2.json()["cuentaId"] == "AC-0002"


def test_case_insensitive_v2():
    reset()
    send("ALTA;Lucia;82")
    r = send("CONSULTa;AC-0001;14")
    assert r.status_code == 200
    assert r.json()["cuenta_id"] == "AC-0001"


def test_auth_v2():
    r = client.post("/__reset")
    assert r.status_code == 401
    r2 = client.get("/health")
    assert r2.status_code == 401


def test_ejemplos_originales_v2():
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
            actual_status = r.status_code
            actual_body = r.json()
            match = actual_status == expected_status
            if isinstance(actual_body, dict) and isinstance(expected_body, dict):
                match = match and all(actual_body.get(k) == v for k, v in expected_body.items())
            assert match, f"{msg}: {actual_status} {actual_body} expected={expected_body}"
