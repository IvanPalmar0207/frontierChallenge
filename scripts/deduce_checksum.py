#!/usr/bin/env python3
"""Analiza los ejemplos para deducir el algoritmo del dígito de control."""
import json
from pathlib import Path

EJEMPLOS = Path(__file__).parent.parent / "pruebas" / "ejemplos.jsonl"

examples = []
with open(EJEMPLOS, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            examples.append(json.loads(line))

# Separa válidos e inválidos
valid = []
invalid_control = []  # E202
invalid_format = []   # E201
for ex in examples:
    msg = ex["request"]["m"]
    parts = msg.split(";")
    cmd = parts[0].upper()
    control = parts[-1]
    body = ex["response"]
    status = ex["status"]
    
    if isinstance(body, dict) and body.get("error") == "E202":
        invalid_control.append((cmd, parts[1:-1], control))
    elif isinstance(body, dict) and body.get("error") == "E201":
        invalid_format.append((cmd, parts[1:-1], control))
    elif status < 400:
        valid.append((cmd, parts[1:-1], control))

print("=== VÁLIDOS ===")
for v in valid:
    print(f"  {v[0]} args={v[1]} control={v[2]}")

print("\n=== INVÁLIDOS (E202) ===")
for v in invalid_control:
    print(f"  {v[0]} args={v[1]} control={v[2]}")

def try_checksum(msg_without_control: str) -> int:
    """Prueba varios algoritmos. Retorna el mejor candidato."""
    data = msg_without_control.encode('utf-8')
    
    # 1. Suma ASCII simple mod 100
    s = sum(data) % 100
    
    # 2. Suma ASCII de solo letras mod 100
    letters = [b for b in data if 65 <= b <= 90 or 97 <= b <= 122]
    s_letters = sum(letters) % 100 if letters else -1
    
    # 3. XOR de todos los bytes mod 100
    x = 0
    for b in data:
        x ^= b
    x = x % 100
    
    # 4. Suma ponderada (posición * valor) mod 100
    wp = sum((i+1) * b for i, b in enumerate(data)) % 100
    
    # 5. CRC8 (polynomial 0x07)
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07
            else:
                crc <<= 1
            crc &= 0xFF
    crc = crc % 100
    
    # 6. Fletcher-16 mod 100
    sum1 = 0
    sum2 = 0
    for b in data:
        sum1 = (sum1 + b) % 255
        sum2 = (sum2 + sum1) % 255
    fletcher = ((sum2 << 8) | sum1) % 100
    
    # 7. Suma de todos los dígitos en el mensaje (como números) mod 100
    digits = [int(c) for c in msg_without_control if c.isdigit()]
    sd = sum(digits) % 100 if digits else -1
    
    return {
        "sum_ascii": s,
        "sum_letters": s_letters,
        "xor": x,
        "weighted": wp,
        "crc8": crc,
        "fletcher": fletcher,
        "sum_digits": sd,
    }

print("\n=== PRUEBA DE ALGORITMOS ===")
for cmd, args, control in valid:
    msg = ";".join([cmd] + args)
    ctrl = int(control)
    results = try_checksum(msg)
    matches = {k: v for k, v in results.items() if v == ctrl}
    if matches:
        print(f"MATCH {msg} -> {control}: {matches}")
    else:
        print(f"NO MATCH {msg} -> {control}: {results}")

# Ahora probemos: ¿el control depende solo del mensaje completo?
print("\n=== ANÁLISIS DE COLISIONES ===")
msgs = {}
for cmd, args, control in valid:
    msg = ";".join([cmd] + args)
    if msg in msgs:
        print(f"  COLISIÓN: {msg} → {msgs[msg]} y {control}")
    else:
        msgs[msg] = control

# Probar hipótesis: ¿el control es una función simple del mensaje?
# Veamos si dos mensajes diferentes tienen mismo control
print("\n=== CONTROLES REPETIDOS ===")
from collections import defaultdict
by_control = defaultdict(list)
for cmd, args, control in valid:
    by_control[control].append(";".join([cmd] + args))
for ctrl, msgs in by_control.items():
    if len(msgs) > 1:
        print(f"  Control {ctrl} usado en:")
        for m in msgs:
            print(f"    {m}")
