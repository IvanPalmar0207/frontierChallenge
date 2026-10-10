#!/usr/bin/env python3
"""
Fuzzing rapido de V2 para descubrir el algoritmo del control.
Rate limit: ~6 req/s -> delay 0.17s
"""
import httpx, time, json

TOKEN = 'cn-p-abh_bog_atuq_j6wv-3kmzrJhII3wxzcmcRaldFs'
URL = 'https://caja-negra-production-c64f.up.railway.app'
headers = {"Authorization": f"Bearer {TOKEN}"}

def send(msg):
    time.sleep(0.15)
    try:
        r = httpx.post(f"{URL}/msg", json={"m": msg}, headers=headers, timeout=12)
        body = r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
        return r.status_code, body
    except Exception as e:
        return -1, str(e)

def reset():
    time.sleep(0.15)
    httpx.post(f"{URL}/__reset", headers=headers, timeout=12)

def find_ctrl(prefix):
    for c in range(100):
        status, body = send(f"{prefix};{c}")
        if status < 400:
            return c, status, body
    return None, None, None

data = []

print("=== FUZZ RAPIDO V2 ===")

# ALTA con nombres variados
print("\n--- ALTA nombres ---")
reset()
for name in ["A","B","C","D","E","X","AA","AB","BA","Test","Lucia","Mateo","John","Juan","Ana","Z"]:
    ctrl, status, body = find_ctrl(f"ALTA;{name}")
    if ctrl is not None:
        ascii_sum = sum(ord(c) for c in name)
        xor_all = 0
        for c in name:
            xor_all ^= ord(c)
        len_n = len(name)
        print(f"  ALTA;{name} -> ctrl={ctrl:2d} | len={len_n} | ascii_sum={ascii_sum:3d} | xor={xor_all:2d} | sum%100={ascii_sum%100:2d} | sum%50={ascii_sum%50:2d} | xor%100={xor_all%100:2d}")
        data.append(("ALTA", name, ctrl, ascii_sum, xor_all, len_n))

# ALTA con mismo nombre, secuencial
print("\n--- ALTA secuencial (A-Z) ---")
reset()
for i in range(65, 91):  # A-Z
    name = chr(i)
    ctrl, _, _ = find_ctrl(f"ALTA;{name}")
    if ctrl is not None:
        print(f"  ALTA;{name} -> ctrl={ctrl:2d}")

# CONSULTA para varias cuentas
print("\n--- CONSULTA varias cuentas ---")
reset()
accounts = []
for name in ["A","B","C","D","E"]:
    ctrl, _, body = find_ctrl(f"ALTA;{name}")
    if isinstance(body, dict) and "cuentaId" in body:
        accounts.append(body["cuentaId"])

for acc in accounts:
    ctrl, _, _ = find_ctrl(f"CONSULTA;{acc}")
    if ctrl is not None:
        num = int(acc.split("-")[1])
        print(f"  CONSULTA;{acc} -> ctrl={ctrl:2d} | num={num:4d} | num%100={num%100:2d}")

# DEPOSITO varios montos
print("\n--- DEPOSITO montos variados ---")
reset()
find_ctrl("ALTA;D")
acc = "AC-0001"
for monto in [1, 10, 100, 1000, 1234, 5000, 10000, 12345, 250000]:
    ctrl, _, _ = find_ctrl(f"DEPOSITO;{acc};{monto}")
    if ctrl is not None:
        print(f"  DEPOSITO;{acc};{monto} -> ctrl={ctrl:2d} | monto%100={monto%100:2d} | monto%50={monto%50:2d}")

# TRANSFER varios montos
print("\n--- TRANSFER varios montos ---")
reset()
find_ctrl("ALTA;A")
find_ctrl("ALTA;B")
find_ctrl("DEPOSITO;AC-0001;100000")
for monto in [1, 10, 100, 1000, 5000, 10000, 40000, 50000, 100000]:
    ctrl, _, _ = find_ctrl(f"TRANSFER;AC-0001;AC-0002;{monto}")
    if ctrl is not None:
        print(f"  TRANSFER {monto} -> ctrl={ctrl:2d} | monto%100={monto%100:2d}")

# ANULA para 2 operaciones
print("\n--- ANULA controles ---")
reset()
find_ctrl("ALTA;A")
find_ctrl("ALTA;B")
find_ctrl("DEPOSITO;AC-0001;50000")
_, _, body = find_ctrl("TRANSFER;AC-0001;AC-0002;1000")
if isinstance(body, dict) and "operacionId" in body:
    op1 = body["operacionId"]
    ctrl1, _, _ = find_ctrl(f"ANULA;{op1}")
    print(f"  ANULA;{op1} -> ctrl={ctrl1}")
    
    _, _, body2 = find_ctrl("TRANSFER;AC-0001;AC-0002;2000")
    if isinstance(body2, dict) and "operacionId" in body2:
        op2 = body2["operacionId"]
        ctrl2, _, _ = find_ctrl(f"ANULA;{op2}")
        print(f"  ANULA;{op2} -> ctrl={ctrl2}")

# PING: confirmar que acepta cualquier
print("\n--- PING ---")
for c in [0, 1, 50, 99]:
    s, b = send(f"PING;{c}")
    print(f"  PING;{c} -> {s}")

# Guardar datos
with open("fuzz_data_v2.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("\nDatos guardados en fuzz_data_v2.json")
