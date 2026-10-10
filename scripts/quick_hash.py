#!/usr/bin/env python3
"""Quick hash analysis - prueba funciones simples rápidamente."""

data = {
    "PING": "64",
    "ALTA;Lucia": "82",
    "ALTA;Mateo": "3",
    "CONSULTA;AC-0001": "14",
    "CONSULTA;AC-0002": "11",
    "CONSULTA;AC-0009": "87",
    "DEPOSITO;AC-0001;250000": "86",
    "TRANSFER;AC-0001;AC-0002;40000": "86",
    "TRANSFER;AC-0001;AC-0002;120000": "55",
    "TRANSFER;AC-0001;AC-0002;100000": "12",
    "TRANSFER;AC-0002;AC-0001;50000": "23",
    "DEPOSITO;AC-0002;700": "35",
    "ANULA;OP-0003": "66",
}

def xor_all(s):
    x = 0
    for c in s:
        x ^= ord(c)
    return x

def crc8(s, poly=0x07):
    crc = 0
    for c in s:
        crc ^= ord(c)
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc

def crc16(s, poly=0x8005):
    crc = 0xFFFF
    for c in s:
        crc ^= ord(c) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def sum_all(s):
    return sum(ord(c) for c in s)

def sum_bytes(s):
    return sum(ord(c) for c in s) & 0xFF

funcs = [
    ("xor_all", xor_all),
    ("crc8", crc8),
    ("crc16_lo", lambda s: crc16(s) & 0xFF),
    ("crc16_hi", lambda s: (crc16(s) >> 8) & 0xFF),
    ("sum_all", sum_all),
    ("sum_mod100", lambda s: sum_all(s) % 100),
    ("sum_bytes", sum_bytes),
    ("len", len),
    ("len_mod100", lambda s: len(s) % 100),
]

print("=== FUNCIONES SIMPLES ===")
for name, func in funcs:
    matches = 0
    total = 0
    for msg, ctrl in data.items():
        if msg == "PING":
            continue
        expected = int(ctrl)
        result = func(msg)
        if result == expected:
            matches += 1
            print(f"  MATCH {name}: {msg} -> {result} == {expected}")
        total += 1
    if matches > 0:
        print(f"  {name}: {matches}/{total} matches")

# Probar solo con argumentos (sin comando)
print("\n=== SOLO ARGUMENTOS ===")
for name, func in funcs:
    matches = 0
    total = 0
    for msg, ctrl in data.items():
        if msg == "PING":
            continue
        parts = msg.split(";")
        args = ";".join(parts[1:])
        expected = int(ctrl)
        result = func(args)
        if result == expected:
            matches += 1
            print(f"  MATCH {name}: {msg} args='{args}' -> {result} == {expected}")
        total += 1
    if matches > 0:
        print(f"  {name} (args): {matches}/{total} matches")

# Probar: suma ASCII de comando + suma ASCII de args
print("\n=== COMBINACIONES ===")
for msg, ctrl in data.items():
    if msg == "PING":
        continue
    parts = msg.split(";")
    cmd = parts[0]
    args = ";".join(parts[1:])
    cmd_sum = sum(ord(c) for c in cmd)
    args_sum = sum(ord(c) for c in args)
    print(f"  {msg}: cmd_sum={cmd_sum}, args_sum={args_sum}, ctrl={ctrl}")

# Hipótesis: ¿es XOR de bytes del mensaje completo, pero en UTF-8 bytes?
print("\n=== XOR EN BYTES UTF-8 ===")
for msg, ctrl in data.items():
    if msg == "PING":
        continue
    x = 0
    for b in msg.encode('utf-8'):
        x ^= b
    print(f"  {msg}: XOR_bytes={x}, ctrl={ctrl}")

# Hipótesis: ¿es alguna suma de dígitos con ponderación?
print("\n=== ANÁLISIS DE DÍGITOS ===")
for msg, ctrl in data.items():
    if msg == "PING":
        continue
    digits = [int(c) for c in msg if c.isdigit()]
    if digits:
        s = sum(digits)
        p = 1
        for d in digits:
            p *= d
        if p == 0:
            p = "N/A"
        print(f"  {msg}: digits={digits}, sum={s}, product={p}, ctrl={ctrl}")
