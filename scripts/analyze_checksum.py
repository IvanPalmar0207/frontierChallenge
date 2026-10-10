#!/usr/bin/env python3
"""Analiza el algoritmo del dígito de control con brute-force de funciones simples."""

# Datos conocidos (msg_without_control -> valid_control)
known = {
    "PING": ("64", True),           # PING acepta cualquier control (lo descubrimos)
    "ALTA;Lucia": ("82", True),
    "ALTA;Mateo": ("3", True),
    "CONSULTA;AC-0001": ("14", True),
    "CONSULTA;AC-0002": ("11", True),
    "CONSULTA;AC-0009": ("87", True),
    "DEPOSITO;AC-0001;250000": ("86", True),
    "TRANSFER;AC-0001;AC-0002;40000": ("86", True),
    "TRANSFER;AC-0001;AC-0002;120000": ("55", True),  # este da E506, pero control 55 es "valido" en formato
    "TRANSFER;AC-0001;AC-0002;100000": ("12", True),
    "TRANSFER;AC-0002;AC-0001;50000": ("23", True),    # E507, control 23 valido
    "DEPOSITO;AC-0002;700": ("35", True),
    "ANULA;OP-0003": ("66", True),
}

# INVÁLIDOS (control incorrecto para mensaje)
invalid = {
    "ALTA;Lucia": "83",
}

# Funciones de hashing simples a probar
def f_sum_ascii(s):
    return sum(ord(c) for c in s) % 100

def f_xor_all(s):
    x = 0
    for c in s:
        x ^= ord(c)
    return x % 100

def f_sum_digits(s):
    total = sum(int(c) for c in s if c.isdigit())
    return total % 100

def f_product_ascii(s):
    p = 1
    for c in s:
        p = (p * ord(c)) % 101
    return p % 100

def f_weighted_sum(s):
    total = 0
    for i, c in enumerate(s):
        total += (i + 1) * ord(c)
    return total % 100

def f_fletcher16(s):
    s1 = 0
    s2 = 0
    for c in s:
        s1 = (s1 + ord(c)) % 255
        s2 = (s2 + s1) % 255
    return ((s2 << 8) | s1) % 100

def f_crc8(s, poly=0x07):
    crc = 0
    for c in s:
        crc ^= ord(c)
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFF
    return crc % 100

def f_djb2(s):
    h = 5381
    for c in s:
        h = ((h << 5) + h) + ord(c)
    return (h & 0xFFFFFFFF) % 100

def f_sdbm(s):
    h = 0
    for c in s:
        h = ord(c) + (h << 6) + (h << 16) - h
    return (h & 0xFFFFFFFF) % 100

def f_fnv1a(s):
    h = 0x811c9dc5
    for c in s:
        h ^= ord(c)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h % 100

def f_sum_only_letters(s):
    total = sum(ord(c) for c in s if c.isalpha())
    return total % 100

def f_sum_only_digits(s):
    total = sum(int(c) for c in s if c.isdigit())
    return total % 100

def f_len_mod(s):
    return len(s) % 100

def f_first_char(s):
    return ord(s[0]) % 100 if s else 0

def f_last_char(s):
    return ord(s[-1]) % 100 if s else 0

def f_sum_bytes(s):
    return sum(ord(c) for c in s) & 0xFF

def f_adler32(s):
    a = 1
    b = 0
    for c in s:
        a = (a + ord(c)) % 65521
        b = (b + a) % 65521
    return ((b << 16) | a) % 100

functions = [
    ("sum_ascii", f_sum_ascii),
    ("xor_all", f_xor_all),
    ("sum_digits", f_sum_digits),
    ("product_ascii", f_product_ascii),
    ("weighted_sum", f_weighted_sum),
    ("fletcher16", f_fletcher16),
    ("crc8", f_crc8),
    ("djb2", f_djb2),
    ("sdbm", f_sdbm),
    ("fnv1a", f_fnv1a),
    ("sum_only_letters", f_sum_only_letters),
    ("sum_only_digits", f_sum_only_digits),
    ("len_mod", f_len_mod),
    ("first_char", f_first_char),
    ("last_char", f_last_char),
    ("sum_bytes", f_sum_bytes),
    ("adler32", f_adler32),
]

# Probar con los mensajes completos (incluyendo comando)
print("=== ANÁLISIS CON MENSAJE COMPLETO ===")
for name, func in functions:
    matches = 0
    total = 0
    for msg, (ctrl, _) in known.items():
        if msg.startswith("PING"):
            continue  # PING acepta cualquier control
        expected = int(ctrl)
        predicted = func(msg)
        if predicted == expected:
            matches += 1
        total += 1
    pct = matches / total * 100 if total else 0
    if matches > 0:
        print(f"  {name}: {matches}/{total} ({pct:.0f}%)")

# Probar con msg sin comando
print("\n=== ANÁLISIS SIN COMANDO ===")
for name, func in functions:
    matches = 0
    total = 0
    for msg, (ctrl, _) in known.items():
        if msg.startswith("PING"):
            continue
        parts = msg.split(";")
        body = ";".join(parts[1:]) if len(parts) > 1 else ""
        expected = int(ctrl)
        predicted = func(body)
        if predicted == expected:
            matches += 1
        total += 1
    pct = matches / total * 100 if total else 0
    if matches > 0:
        print(f"  {name}: {matches}/{total} ({pct:.0f}%)")

# Probar combinaciones: f1 + f2
print("\n=== ANÁLISIS COMBINACIONES (f1 + f2) mod 100 ===")
best = None
best_score = -1
for n1, f1 in functions:
    for n2, f2 in functions:
        if n1 == n2:
            continue
        matches = 0
        total = 0
        for msg, (ctrl, _) in known.items():
            if msg.startswith("PING"):
                continue
            expected = int(ctrl)
            predicted = (f1(msg) + f2(msg)) % 100
            if predicted == expected:
                matches += 1
            total += 1
        if matches > best_score:
            best_score = matches
            best = (n1, n2, matches, total)
        if matches >= 5:
            print(f"  {n1} + {n2}: {matches}/{total}")

print(f"\n  MEJOR COMBINACION: {best[0]} + {best[1]} = {best[2]}/{best[3]}")

# Probar XOR de funciones
print("\n=== ANÁLISIS XOR (f1 ^ f2) mod 100 ===")
best = None
best_score = -1
for n1, f1 in functions:
    for n2, f2 in functions:
        if n1 == n2:
            continue
        matches = 0
        total = 0
        for msg, (ctrl, _) in known.items():
            if msg.startswith("PING"):
                continue
            expected = int(ctrl)
            predicted = (f1(msg) ^ f2(msg)) % 100
            if predicted == expected:
                matches += 1
            total += 1
        if matches > best_score:
            best_score = matches
            best = (n1, n2, matches, total)
        if matches >= 5:
            print(f"  {n1} XOR {n2}: {matches}/{total}")

print(f"\n  MEJOR XOR: {best[0]} XOR {best[1]} = {best[2]}/{best[3]}")

# Probar productos
print("\n=== ANÁLISIS PRODUCTO (f1 * f2) mod 100 ===")
best = None
best_score = -1
for n1, f1 in functions:
    for n2, f2 in functions:
        if n1 == n2:
            continue
        matches = 0
        total = 0
        for msg, (ctrl, _) in known.items():
            if msg.startswith("PING"):
                continue
            expected = int(ctrl)
            predicted = (f1(msg) * f2(msg)) % 100
            if predicted == expected:
                matches += 1
            total += 1
        if matches > best_score:
            best_score = matches
            best = (n1, n2, matches, total)

print(f"\n  MEJOR PRODUCTO: {best[0]} * {best[1]} = {best[2]}/{best[3]}")

# Brute-force de (a * f1 + b * f2 + c) mod m
print("\n=== BRUTE-FORCE LINEAL (a*f1 + b*f2 + c) mod m ===")
import itertools

for n1, f1 in functions:
    for n2, f2 in functions:
        if n1 == n2:
            continue
        best_combo = None
        best_m = -1
        for a in range(1, 20):
            for b in range(-10, 11):
                for c in range(-10, 11):
                    for m in [50, 97, 98, 99, 100, 101, 127, 128, 255, 256]:
                        matches = 0
                        total = 0
                        for msg, (ctrl, _) in known.items():
                            if msg.startswith("PING"):
                                continue
                            expected = int(ctrl)
                            predicted = ((a * f1(msg) + b * f2(msg) + c) % m) % 100
                            if predicted == expected:
                                matches += 1
                            total += 1
                        if matches > best_m:
                            best_m = matches
                            best_combo = (a, b, c, m, matches, total)
        if best_m >= 6:
            print(f"  {n1}/{n2}: a={best_combo[0]} b={best_combo[1]} c={best_combo[2]} m={best_combo[3]} -> {best_combo[4]}/{best_combo[5]}")
