#!/usr/bin/env python3
"""
Fuzzer experimental contra el servicio original.
Descubre el algoritmo del dígito de control.
"""
import json
import os
import time
import httpx
from pathlib import Path

TOKEN = os.environ.get("BLACK_BOX_TOKEN", "")
if not TOKEN:
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "token" in line.lower() and "=" in line:
                TOKEN = line.split("=", 1)[1].strip()
                break

BASE_URL = "https://caja-negra-production-c64f.up.railway.app"
EXPERIMENTOS_PATH = Path(__file__).parent.parent / "experimentos.jsonl"
EJEMPLOS_PATH = Path(__file__).parent.parent / "pruebas" / "ejemplos.jsonl"

headers = {"Authorization": f"Bearer {TOKEN}"}

def send(msg: str, seq: str = "fuzz", hipotesis: str = "", x_req: int = 0):
    """Envía un request al original y loguea el experimento."""
    time.sleep(0.12)  # rate limit: ~8 req/s
    try:
        r = httpx.post(f"{BASE_URL}/msg", json={"m": msg}, headers=headers, timeout=5)
        resp_body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        log = {
            "id": _next_id(),
            "seq": seq,
            "x_req": x_req,
            "hipotesis": hipotesis,
            "request": {"m": msg},
            "status": r.status_code,
            "response": resp_body,
            "conclusion": ""
        }
        _append_log(log)
        return r.status_code, resp_body
    except Exception as e:
        print(f"ERROR: {e}")
        return None, None

def reset():
    httpx.post(f"{BASE_URL}/__reset", headers=headers, timeout=5)
    time.sleep(0.12)

_log_counter = 0
def _next_id():
    global _log_counter
    _log_counter += 1
    return _log_counter

def _append_log(entry):
    with open(EXPERIMENTOS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def fuzz_control_digit():
    """Fuzzea el dígito de control para descubrir la fórmula."""
    # Cargar ejemplos conocidos
    known = []
    with open(EJEMPLOS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                known.append(json.loads(line))

    # Fase 1: reproducir ejemplos exactos para confirmar determinismo
    reset()
    print("=== Fase 1: Reproducción exacta ===")
    for ex in known:
        status, resp = send(ex["request"]["m"], seq="s1",
                            hipotesis=f"Reproducir ejemplo {ex['id']}")
        print(f"  {ex['request']['m']} -> {status} | esperado {ex['status']}")

    # Fase 2: variar control en ejemplos válidos
    print("\n=== Fase 2: Variaciones de control ===")
    reset()
    for ex in known:
        msg = ex["request"]["m"]
        parts = msg.split(";")
        if len(parts) < 2:
            continue
        control_str = parts[-1]
        if not control_str.isdigit():
            continue
        control = int(control_str)

        # Probar control +1
        mod_msg = ";".join(parts[:-1] + [str(control + 1)])
        status, resp = send(mod_msg, seq="s2",
                            hipotesis=f"{msg} con control +1")
        print(f"  {mod_msg} -> {status}")

        # Probar control -1
        if control > 0:
            mod_msg = ";".join(parts[:-1] + [str(control - 1)])
            status, resp = send(mod_msg, seq="s2",
                                hipotesis=f"{msg} con control -1")
            print(f"  {mod_msg} -> {status}")

        # Si es ALTA, probar control 0-99
        if parts[0].upper() == "ALTA" and control < 100:
            for c in range(100):
                if c == control:
                    continue
                mod_msg = ";".join(parts[:-1] + [str(c)])
                status, resp = send(mod_msg, seq="s3",
                                    hipotesis=f"ALTA brute-force control {c}")
                if status == 201:
                    print(f"  !!! {mod_msg} -> {status} (control válido alternativo?)")
                if _log_counter > 500:
                    break
            if _log_counter > 500:
                break

    print(f"\n=== Total experimentos: {_log_counter} ===")
    print(f"Log guardado en: {EXPERIMENTOS_PATH}")

if __name__ == "__main__":
    fuzz_control_digit()
