#!/usr/bin/env python3
"""
Test visual contra el deploy remoto (Vercel).
Ejecuta los 20 ejemplos y muestra resultados en vivo.
"""
import httpx, json, sys
from pathlib import Path

URL = "https://caja-negra-replacement.vercel.app"
TOKEN = "test-visual"
headers = {"Authorization": f"Bearer {TOKEN}"}

EJEMPLOS = Path(__file__).parent.parent / "pruebas" / "ejemplos.jsonl"

def run():
    # Reset inicial
    r = httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
    if r.status_code != 200:
        print(f"[FATAL] Reset failed: {r.status_code} {r.text}")
        sys.exit(1)

    print("=" * 70)
    print("  PRUEBA VISUAL CONTRA DEPLOY REMOTO")
    print(f"  URL: {URL}")
    print("=" * 70)

    passed = 0
    failed = 0

    with open(EJEMPLOS, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            ex = json.loads(line)
            msg = ex["request"]["m"]
            expected_status = ex["status"]
            expected_body = ex["response"]

            try:
                r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=10)
                actual_status = r.status_code
                try:
                    actual_body = r.json()
                except:
                    actual_body = r.text
            except Exception as e:
                actual_status = -1
                actual_body = str(e)

            # Comparar
            match = (actual_status == expected_status)
            if isinstance(actual_body, dict) and isinstance(expected_body, dict):
                match = match and (set(actual_body.keys()) == set(expected_body.keys()))
                if match:
                    match = all(actual_body.get(k) == expected_body.get(k) for k in expected_body)

            status_icon = "[OK]" if match else "[FAIL]"
            if match:
                passed += 1
                print(f"  {status_icon} Ejemplo {i:2d}: {msg[:50]}")
            else:
                failed += 1
                print(f"  {status_icon} Ejemplo {i:2d}: {msg[:50]}")
                print(f"       Esperado: {expected_status} {json.dumps(expected_body, ensure_ascii=False)}")
                print(f"       Actual:   {actual_status} {json.dumps(actual_body, ensure_ascii=False)}")

    print("=" * 70)
    print(f"  RESULTADO: {passed} OK / {failed} FAIL  ({passed}/{passed+failed})")
    print("=" * 70)

    # Bonus: mostrar algunos requests manuales
    print("\n--- PRUEBAS MANUALES ---")

    # Health
    r = httpx.get(f"{URL}/health", timeout=10)
    print(f"  GET /health -> {r.status_code} {r.text}")

    # Reset
    r = httpx.post(f"{URL}/__reset", headers=headers, timeout=10)
    print(f"  POST /__reset -> {r.status_code} {r.text}")

    # Secuencia manual
    seq = [
        ("ALTA Juan", "ALTA;Juan;99", 201),
        ("DEPOSITO 5000", "DEPOSITO;AC-0001;5000;99", 200),
        ("CONSULTA", "CONSULTA;AC-0001;99", 200),
        ("TRANSFER fail (sin saldo)", "TRANSFER;AC-0001;AC-9999;1000;99", 404),
        ("Aridad inválida", "ALTA;A;B;C;99", 400),
        ("Comando desconocido", "SALDO;AC-0001;99", 400),
    ]

    for name, msg, expected in seq:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=10)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        ok = "[OK]" if r.status_code == expected else "[FAIL]"
        print(f"  {ok} {name}: {r.status_code} {json.dumps(body, ensure_ascii=False)}")

    print("\n--- FIN DE PRUEBAS ---")

if __name__ == "__main__":
    run()
