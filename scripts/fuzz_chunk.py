#!/usr/bin/env python3
"""Fuzzing por chunks con guardado de progreso."""
import httpx, time, json, sys
from pathlib import Path

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}

PROGRESS_FILE = Path(__file__).parent.parent / "fuzz_progress.json"

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"controls": {}, "done_batches": []}

def save_progress(p):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2, ensure_ascii=False)

def send(msg):
    time.sleep(0.25)
    try:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=12)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        return r.status_code, body
    except Exception as e:
        print(f"    ERR: {e}", file=sys.stderr)
        return -1, str(e)

def reset():
    time.sleep(0.25)
    try:
        httpx.post(f"{URL}/__reset", headers=headers, timeout=12)
    except:
        pass

def find_ctrl(prefix):
    for c in range(100):
        status, body = send(f"{prefix};{c}")
        if status < 400:
            return c, status, body
        if status == -1:
            print(f"    Connection error at {c}, retrying...")
            time.sleep(1)
    return None, None, None

p = load_progress()

# ─── Chunk 1: ALTA common names ────────────────────────────────────
if "alta_common" not in p["done_batches"]:
    print("=== Chunk: ALTA common names ===")
    reset()
    names = ["Juan", "Maria", "Pedro", "Ana", "Luis", "Carlos", "Sofia", "Diego", "Laura"]
    for name in names:
        if f"ALTA;{name}" in p["controls"]:
            print(f"  ALTA;{name} -> {p['controls'][f'ALTA;{name}']} (cached)")
            continue
        print(f"  Finding ALTA;{name}...")
        ctrl, status, body = find_ctrl(f"ALTA;{name}")
        if ctrl is not None:
            print(f"    -> {ctrl}")
            p["controls"][f"ALTA;{name}"] = ctrl
            save_progress(p)
        else:
            print(f"    -> NOT FOUND")
    p["done_batches"].append("alta_common")
    save_progress(p)

# ─── Chunk 2: ALTA short names ────────────────────────────────────
if "alta_short" not in p["done_batches"]:
    print("\n=== Chunk: ALTA short names ===")
    reset()
    names = ["X", "Y", "Z", "Jo", "Al", "Bo", "Ca"]
    for name in names:
        if f"ALTA;{name}" in p["controls"]:
            print(f"  ALTA;{name} -> {p['controls'][f'ALTA;{name}']} (cached)")
            continue
        print(f"  Finding ALTA;{name}...")
        ctrl, status, body = find_ctrl(f"ALTA;{name}")
        if ctrl is not None:
            print(f"    -> {ctrl}")
            p["controls"][f"ALTA;{name}"] = ctrl
            save_progress(p)
        else:
            print(f"    -> NOT FOUND")
    p["done_batches"].append("alta_short")
    save_progress(p)

# ─── Chunk 3: CONSULTA for first 3 accounts ──────────────────────
if "consulta_3" not in p["done_batches"]:
    print("\n=== Chunk: CONSULTA 3 accounts ===")
    reset()
    accounts = []
    for name in ["A", "B", "C"]:
        ctrl = p["controls"].get(f"ALTA;{name}")
        if ctrl is not None:
            _, body = send(f"ALTA;{name};{ctrl}")
            if isinstance(body, dict) and "cuentaId" in body:
                accounts.append(body["cuentaId"])
    for acc in accounts:
        if f"CONSULTA;{acc}" in p["controls"]:
            print(f"  CONSULTA;{acc} -> {p['controls'][f'CONSULTA;{acc}']} (cached)")
            continue
        print(f"  Finding CONSULTA;{acc}...")
        ctrl, _, _ = find_ctrl(f"CONSULTA;{acc}")
        if ctrl is not None:
            print(f"    -> {ctrl}")
            p["controls"][f"CONSULTA;{acc}"] = ctrl
            save_progress(p)
    p["done_batches"].append("consulta_3")
    save_progress(p)

# ─── Chunk 4: DEPOSITO 3 amounts ─────────────────────────────────
if "deposito_3" not in p["done_batches"]:
    print("\n=== Chunk: DEPOSITO 3 amounts ===")
    reset()
    ctrl_a = p["controls"].get("ALTA;A")
    if ctrl_a is not None:
        _, body = send(f"ALTA;A;{ctrl_a}")
        if isinstance(body, dict) and "cuentaId" in body:
            acc = body["cuentaId"]
            for amount in [100, 1000, 10000]:
                key = f"DEPOSITO;{acc};{amount}"
                if key in p["controls"]:
                    print(f"  {key} -> {p['controls'][key]} (cached)")
                    continue
                print(f"  Finding {key}...")
                ctrl, _, _ = find_ctrl(key)
                if ctrl is not None:
                    print(f"    -> {ctrl}")
                    p["controls"][key] = ctrl
                    save_progress(p)
    p["done_batches"].append("deposito_3")
    save_progress(p)

# ─── Chunk 5: TRANSFER 3 amounts ──────────────────────────────────
if "transfer_3" not in p["done_batches"]:
    print("\n=== Chunk: TRANSFER 3 amounts ===")
    reset()
    ctrl_a = p["controls"].get("ALTA;A")
    ctrl_b = p["controls"].get("ALTA;B")
    if ctrl_a and ctrl_b:
        _, b1 = send(f"ALTA;A;{ctrl_a}")
        _, b2 = send(f"ALTA;B;{ctrl_b}")
        if isinstance(b1, dict) and isinstance(b2, dict):
            acc1 = b1["cuentaId"]
            acc2 = b2["cuentaId"]
            # Deposit to acc1
            ctrl_d = p["controls"].get(f"DEPOSITO;{acc1};100000")
            if ctrl_d:
                send(f"DEPOSITO;{acc1};100000;{ctrl_d}")
            else:
                find_ctrl(f"DEPOSITO;{acc1};100000")
            for amount in [100, 1000, 10000]:
                key = f"TRANSFER;{acc1};{acc2};{amount}"
                if key in p["controls"]:
                    print(f"  {key} -> {p['controls'][key]} (cached)")
                    continue
                print(f"  Finding {key}...")
                ctrl, _, _ = find_ctrl(key)
                if ctrl is not None:
                    print(f"    -> {ctrl}")
                    p["controls"][key] = ctrl
                    save_progress(p)
    p["done_batches"].append("transfer_3")
    save_progress(p)

print(f"\n=== TOTAL CONTROLS: {len(p['controls'])} ===")
for k, v in sorted(p["controls"].items()):
    print(f"  {k} -> {v}")
