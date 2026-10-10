#!/usr/bin/env python3
"""
Buscar patrones en los datos de control ya recolectados.
Probamos funciones hash simples para encontrar el algoritmo.
"""

# Datos conocidos ALTA V2
alta_data = {
    "A": 62, "B": 59, "C": 56, "D": 53, "E": 50,
    "Test": 37, "Lucia": 82, "Mateo": 3,
}

# CONSULTA
consulta_data = {
    "AC-0001": 14, "AC-0002": 11,
}

# DEPOSITO (cuenta, monto) -> ctrl
deposito_data = {
    ("AC-0001", 250000): 86,  # V1, V2 tambien valido
    ("AC-0001", 1000): 35,    # V2 descubierto
    ("AC-0001", 1): 28,       # V2 descubierto
    ("AC-0001", 100): 82,     # V2 descubierto
}

def xor_all(s):
    x = 0
    for c in s:
        x ^= ord(c)
    return x

def sum_ascii(s):
    return sum(ord(c) for c in s)

def sum_bytes(s):
    return sum(ord(c) for c in s) & 0xFF

def crc8(s, poly=0x07):
    crc = 0
    for c in s:
        crc ^= ord(c)
        for _ in range(8):
            crc = ((crc << 1) ^ poly if crc & 0x80 else crc << 1) & 0xFF
    return crc

def fnv1a(s):
    h = 0x811c9dc5
    for c in s:
        h ^= ord(c)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h

def djb2(s):
    h = 5381
    for c in s:
        h = ((h << 5) + h) + ord(c)
    return h & 0xFFFFFFFF

def sdbm(s):
    h = 0
    for c in s:
        h = (ord(c) + (h << 6) + (h << 16) - h) & 0xFFFFFFFF
    return h

funcs = [
    ("sum_ascii", sum_ascii),
    ("sum_bytes", sum_bytes),
    ("xor_all", xor_all),
    ("crc8", lambda s: crc8(s, 0x07)),
    ("crc8_31", lambda s: crc8(s, 0x31)),
    ("crc8_9B", lambda s: crc8(s, 0x9B)),
    ("fnv1a", fnv1a),
    ("djb2", djb2),
    ("sdbm", sdbm),
]

print("=== BUSQUEDA DE PATRON ALTA ===")
for name, func in funcs:
    matches = 0
    for msg, ctrl in alta_data.items():
        full_msg = f"ALTA;{msg}"
        for m in range(1, 300):
            if func(full_msg) % m == ctrl:
                matches += 1
                break
    if matches > 0:
        print(f"  {name}: {matches}/{len(alta_data)} matches (algun modulo)")

# Probar combinaciones lineales: a*f1 + b*f2 + c (mod m)
print("\n=== COMBINACIONES LINEALES ALTA ===")
best = None
best_score = -1
for n1, f1 in funcs:
    for n2, f2 in funcs:
        if n1 == n2: continue
        for a in range(-5, 6):
            for b in range(-5, 6):
                for c in range(-10, 11):
                    for m in range(50, 256):
                        score = 0
                        for msg, ctrl in alta_data.items():
                            full_msg = f"ALTA;{msg}"
                            predicted = ((a * f1(full_msg) + b * f2(full_msg) + c) % m) % 100
                            if predicted == ctrl:
                                score += 1
                        if score > best_score:
                            best_score = score
                            best = (n1, n2, a, b, c, m)

print(f"  Mejor: {best[0]}*{best[2]} + {best[1]}*{best[3]} + {best[4]} mod {best[5]}")
print(f"  Score: {best_score}/{len(alta_data)}")

# Si encontramos formula perfecta, probarla
if best_score == len(alta_data):
    n1, n2, a, b, c, m = best
    print("\n  === FORMULA PERFECTA ===")
    print(f"  ctrl = ({a} * {n1}(msg) + {b} * {n2}(msg) + {c}) mod {m} mod 100")
    
    # Probar con CONSULTA
    print("\n  --- Probando CONSULTA ---")
    for acc, ctrl in consulta_data.items():
        full_msg = f"CONSULTA;{acc}"
        pred = ((a * eval(n1)(full_msg) + b * eval(n2)(full_msg) + c) % m) % 100
        print(f"    CONSULTA;{acc}: esperado={ctrl}, predicho={pred} {'OK' if pred == ctrl else 'FAIL'}")
    
    # Probar con DEPOSITO
    print("\n  --- Probando DEPOSITO ---")
    for (acc, monto), ctrl in deposito_data.items():
        full_msg = f"DEPOSITO;{acc};{monto}"
        pred = ((a * eval(n1)(full_msg) + b * eval(n2)(full_msg) + c) % m) % 100
        print(f"    DEPOSITO;{acc};{monto}: esperado={ctrl}, predicho={pred} {'OK' if pred == ctrl else 'FAIL'}")

# Buscar: ¿es suma ASCII de args (sin comando) mod algo?
print("\n=== SOLO ARGS (sin comando) ===")
for name, func in funcs:
    for m in range(50, 256):
        matches = 0
        for msg, ctrl in alta_data.items():
            predicted = func(msg) % m % 100
            if predicted == ctrl:
                matches += 1
        if matches == len(alta_data):
            print(f"  {name}(nombre) mod {m} mod 100 -> PERFECTO para ALTA")
            break

# CONSULTA: args = "AC-0001"
print("\n=== CONSULTA pattern ===")
for acc, ctrl in consulta_data.items():
    num = int(acc.split("-")[1])
    ascii_sum = sum_ascii(acc)
    xor_val = xor_all(acc)
    print(f"  {acc}: ctrl={ctrl}, num={num}, num%100={num%100}, ascii_sum={ascii_sum}, xor={xor_val}")

# DEPOSITO: analizar montos
print("\n=== DEPOSITO pattern ===")
for (acc, monto), ctrl in deposito_data.items():
    full = f"DEPOSITO;{acc};{monto}"
    for name, func in funcs:
        for m in range(50, 256):
            if func(full) % m % 100 == ctrl:
                print(f"  DEPOSITO;{acc};{monto} ctrl={ctrl}: {name}(full) mod {m} -> match")
                break
        else:
            continue
        break

print("\n=== FIN ===")
