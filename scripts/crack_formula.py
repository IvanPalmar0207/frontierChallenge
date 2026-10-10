#!/usr/bin/env python3
"""Último intento: buscar fórmula del dígito de control con fuerza bruta."""

alta_data = {
    "ALTA;Lucia": 82, "ALTA;Mateo": 3, "ALTA;A": 62,
    "ALTA;B": 59, "ALTA;Test": 37,
}

def xor_all(s):
    x = 0
    for c in s: x ^= ord(c)
    return x

def sum_all(s):
    return sum(ord(c) for c in s) % 256

def sum_mod100(s):
    return sum(ord(c) for c in s) % 100

def first_char(s):
    return ord(s[0]) if s else 0

def last_char(s):
    return ord(s[-1]) if s else 0

def len_val(s):
    return len(s) % 256

def weighted_sum(s):
    return sum((i+1)*ord(c) for i,c in enumerate(s)) % 256

def crc8(s, poly=0x07):
    crc = 0
    for c in s:
        crc ^= ord(c)
        for _ in range(8):
            crc = ((crc << 1) ^ poly if crc & 0x80 else crc << 1) & 0xFF
    return crc

def fnv1a_8(s):
    h = 0x81
    for c in s:
        h = ((h ^ ord(c)) * 0x0103) & 0xFF
    return h

def djb2_8(s):
    h = 5381 & 0xFF
    for c in s:
        h = ((h << 5) + h + ord(c)) & 0xFF
    return h

def sdbm_8(s):
    h = 0
    for c in s:
        h = (ord(c) + (h << 6) + (h << 16) - h) & 0xFF
    return h

def fletcher_lo(s):
    s1 = s2 = 0
    for c in s:
        s1 = (s1 + ord(c)) % 255
        s2 = (s2 + s1) % 255
    return s1

def fletcher_hi(s):
    s1 = s2 = 0
    for c in s:
        s1 = (s1 + ord(c)) % 255
        s2 = (s2 + s1) % 255
    return s2

funcs = [
    ("xor", xor_all), ("sum", sum_all), ("sum%100", sum_mod100),
    ("first", first_char), ("last", last_char), ("len", len_val),
    ("weighted", weighted_sum), ("crc8", lambda s: crc8(s, 0x07)),
    ("crc8_31", lambda s: crc8(s, 0x31)), ("crc8_9B", lambda s: crc8(s, 0x9B)),
    ("crc8_D5", lambda s: crc8(s, 0xD5)), ("fnv1a", fnv1a_8),
    ("djb2", djb2_8), ("sdbm", sdbm_8), ("fletcher_lo", fletcher_lo),
    ("fletcher_hi", fletcher_hi),
]

print("=== Single functions ===")
for name, f in funcs:
    m = sum(1 for msg, ctrl in alta_data.items() if f(msg) % 100 == ctrl)
    if m > 0:
        print(f"  {name}: {m}/{len(alta_data)}")

print("\n=== Linear combos (a*f1 + b*f2 + c) % m ===")
best_score = -1
best = None
for i, (n1, f1) in enumerate(funcs):
    for j, (n2, f2) in enumerate(funcs):
        if i >= j: continue
        for a in range(-3, 4):
            for b in range(-3, 4):
                for c in range(-5, 6):
                    for m in [97, 100, 128, 256]:
                        score = sum(1 for msg, ctrl in alta_data.items()
                                    if ((a*f1(msg) + b*f2(msg) + c) % m) % 100 == ctrl)
                        if score > best_score:
                            best_score = score
                            best = (n1, n2, a, b, c, m)

print(f"  Best: {best[0]}*{best[2]} + {best[1]}*{best[3]} + {best[4]} % {best[5]}")
print(f"  Score: {best_score}/{len(alta_data)}")

print("\n=== XOR combos (f1 ^ f2) % m ===")
best_score = -1
best = None
for i, (n1, f1) in enumerate(funcs):
    for j, (n2, f2) in enumerate(funcs):
        if i >= j: continue
        for m in [97, 100, 128, 256]:
            score = sum(1 for msg, ctrl in alta_data.items()
                        if ((f1(msg) ^ f2(msg)) % m) % 100 == ctrl)
            if score > best_score:
                best_score = score
                best = (n1, n2, m)

print(f"  Best: {best[0]} XOR {best[1]} % {best[2]}")
print(f"  Score: {best_score}/{len(alta_data)}")

print("\n=== Product combos (f1 * f2) % m ===")
best_score = -1
best = None
for i, (n1, f1) in enumerate(funcs):
    for j, (n2, f2) in enumerate(funcs):
        if i >= j: continue
        for m in [97, 100, 128, 256]:
            score = sum(1 for msg, ctrl in alta_data.items()
                        if ((f1(msg) * f2(msg)) % m) % 100 == ctrl)
            if score > best_score:
                best_score = score
                best = (n1, n2, m)

print(f"  Best: {best[0]} * {best[1]} % {best[2]}")
print(f"  Score: {best_score}/{len(alta_data)}")

print("\n=== CONCLUSION ===")
print("  No se puede deducir la fórmula con los datos actuales.")
print("  Se necesitan ~50+ puntos de datos para una deducción confiable.")
print("  El rate limit del servicio original impide recolectar suficientes datos.")
