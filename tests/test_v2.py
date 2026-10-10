#!/usr/bin/env python3
"""
Tests para la Version 2 del servicio.
Valida los 3 cambios confirmados contra el servicio original.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.main import app
from src.checksum import _known_controls

client = TestClient(app)
TOKEN = "test-v2"
headers = {"Authorization": f"Bearer {TOKEN}"}

def ctrl(msg_without_control: str) -> str:
    v = _known_controls.get(msg_without_control)
    return v if v is not None else "99"

def reset():
    client.post("/__reset", headers=headers)

def send(msg: str):
    return client.post("/msg", json={"m": msg}, headers=headers)


# ─── CAMBIO 1: Saldo formato monetario string ─────────────────────
def test_consulta_saldo_formato_v2():
    """V2: saldo devuelto como string con 2 decimales, dividido por 100."""
    reset()
    send(f"ALTA;Test;{ctrl('ALTA;Test')}")
    r = send(f"DEPOSITO;AC-0001;250000;{ctrl('DEPOSITO;AC-0001;250000')}")
    assert r.status_code == 200
    r2 = send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}")
    assert r2.status_code == 200
    body = r2.json()
    assert body["cuenta_id"] == "AC-0001"
    # V2: saldo es string "2500.00" = 250000/100
    assert body["saldo"] == "2500.00"

def test_saldo_despues_transfer_v2():
    """V2: transferencia afecta saldos mostrados en formato monetario."""
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    send(f"ALTA;B;{ctrl('ALTA;B')}")
    send(f"DEPOSITO;AC-0001;250000;{ctrl('DEPOSITO;AC-0001;250000')}")
    send(f"TRANSFER;AC-0001;AC-0002;40000;{ctrl('TRANSFER;AC-0001;AC-0002;40000')}")
    r1 = send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}")
    r2 = send(f"CONSULTA;AC-0002;{ctrl('CONSULTA;AC-0002')}")
    assert r1.json()["saldo"] == "2100.00"  # (250000-40000)/100
    assert r2.json()["saldo"] == "400.00"   # 40000/100


# ─── CAMBIO 2: ANULA siempre devuelve ok:false ────────────────────
def test_anula_primera_vez_ok_false_v2():
    """V2: ANULA primera vez devuelve ok:false pero revierte la operacion."""
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    send(f"ALTA;B;{ctrl('ALTA;B')}")
    send(f"DEPOSITO;AC-0001;250000;{ctrl('DEPOSITO;AC-0001;250000')}")
    r = send(f"TRANSFER;AC-0001;AC-0002;40000;{ctrl('TRANSFER;AC-0001;AC-0002;40000')}")
    assert r.status_code == 200
    op_id = r.json()["operacionId"]
    # Anular primera vez
    r2 = send(f"ANULA;{op_id};{ctrl(f'ANULA;{op_id}')}")
    assert r2.status_code == 200
    body = r2.json()
    # V2: siempre ok:false
    assert body["ok"] is False
    assert body["motivo"] == "ya anulada"
    # Pero los saldos se revirtieron
    r3 = send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}")
    r4 = send(f"CONSULTA;AC-0002;{ctrl('CONSULTA;AC-0002')}")
    assert r3.json()["saldo"] == "2500.00"  # Volvio al valor pre-transfer
    assert r4.json()["saldo"] == "0.00"

def test_anula_deposito_v2():
    """V2: ANULA de DEPOSITO devuelve ok:false pero revierte."""
    reset()
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    r = send(f"DEPOSITO;AC-0001;10000;{ctrl('DEPOSITO;AC-0001;10000')}")
    assert r.status_code == 200
    op_id = r.json()["operacionId"]
    # Anular
    r2 = send(f"ANULA;{op_id};{ctrl(f'ANULA;{op_id}')}")
    assert r2.status_code == 200
    assert r2.json()["ok"] is False
    # Saldo revertido
    r3 = send(f"CONSULTA;AC-0001;{ctrl('CONSULTA;AC-0001')}")
    assert r3.json()["saldo"] == "0.00"


# ─── CAMBIO 3: Errores y validaciones ──────────────────────────────
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
    send(f"ALTA;A;{ctrl('ALTA;A')}")
    r = send("DEPOSITO;AC-0001;700;5X")
    assert r.status_code == 400
    assert r.json()["error"] == "E201"


# ─── Regresión: comportamientos que siguen igual ───────────────────
def test_ping_v2():
    reset()
    for c in ["64", "0", "99"]:
        r = send(f"PING;{c}")
        assert r.status_code == 200
        assert r.json()["pong"] is True

def test_alta_secuencial_v2():
    reset()
    r1 = send(f"ALTA;A;{ctrl('ALTA;A')}")
    r2 = send(f"ALTA;B;{ctrl('ALTA;B')}")
    assert r1.json()["cuentaId"] == "AC-0001"
    assert r2.json()["cuentaId"] == "AC-0002"

def test_case_insensitive_v2():
    reset()
    send(f"ALTA;Test;{ctrl('ALTA;Test')}")
    r = send("CONSULTa;AC-0001;14")
    assert r.status_code == 200
    assert r.json()["cuenta_id"] == "AC-0001"

def test_auth_v2():
    r = client.post("/__reset")
    assert r.status_code == 401
    r2 = client.get("/health")
    assert r2.status_code == 401


# ─── Regresión: 20 ejemplos originales (adaptados a V2) ─────────────
def test_ejemplos_originales_v2():
    """Reproduce los 20 ejemplos originales adaptando saldos a formato V2."""
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

            # Adaptar saldo de V1 a V2
            if isinstance(expected_body, dict) and "saldo" in expected_body:
                expected_saldo = expected_body["saldo"]
                # V2: saldo como string monetario
                if isinstance(expected_saldo, int):
                    expected_body = dict(expected_body)
                    expected_body["saldo"] = f"{expected_saldo / 100:.2f}"

            # Adaptar ANULA de V1 a V2
            if isinstance(expected_body, dict) and expected_body.get("ok") is True:
                expected_body = dict(expected_body)
                expected_body["ok"] = False
                if "anulada" in expected_body:
                    del expected_body["anulada"]
                expected_body["motivo"] = "ya anulada"

            match = actual_status == expected_status
            if isinstance(actual_body, dict) and isinstance(expected_body, dict):
                match = match and all(actual_body.get(k) == v for k, v in expected_body.items())

            assert match, f"{msg}: status={actual_status} body={actual_body} expected={expected_body}"
