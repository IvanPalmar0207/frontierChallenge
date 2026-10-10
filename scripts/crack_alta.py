"""Crack formula ALTA con datos conocidos."""

data = [
    ("Lucia", "82"),
    ("Mateo", "3"),
    ("A", "62"),
    ("B", "59"),
    ("C", "56"),
    ("D", "53"),
    ("E", "50"),
]

# Observaciones
# A-E: control decrece 3 por cada letra
# A=62, B=59, C=56, D=53, E=50
# Diferencia: -3 por cada paso
# Si extrapolamos: F=47, G=44, ... Z=?

# Matematicamente:
# control = 62 - 3*(ord(letra) - ord('A'))
# Para A: 62 - 3*0 = 62 OK
# Para E: 62 - 3*4 = 62 - 12 = 50 OK
# Si Lucia/Mateo siguen la misma formula con algo del nombre completo...

# Probemos: control = (suma_ascii + len*C) mod M
# O: control = suma_ascii mod M
# O: control = XOR de los chars

def ascii_sum(s):
    return sum(ord(c) for c in s)

def xor_all(s):
    x = 0
    for c in s:
        x ^= ord(c)
    return x

# Probar combinaciones lineales simples
print("=== Datos ALTA ===")
for nombre, ctrl in data:
    s = ascii_sum(nombre)
    x = xor_all(nombre)
    l = len(nombre)
    print(f"  {nombre:6s} ctrl={ctrl:2s} ascii_sum={s:4d} xor={x:3d} len={l}")

# Ahora buscar patron con Lucia y Mateo
# Si es lineal: control = a*sum_ascii + b*len + c mod M
# o: control = (sum_ascii XOR algo) mod M
# o: control = producto de digitos mod M

# Veamos si hay relacion entre sum_ascii y control
print("\n=== Relacion suma ASCII vs control ===")
for nombre, ctrl_s in data:
    ctrl = int(ctrl_s)
    s = ascii_sum(nombre)
    print(f"  {nombre:6s}: sum={s:4d} ctrl={ctrl:2d} diff={s-ctrl:4d}")

# Diferencias:
# A: 65 - 62 = 3
# B: 66 - 59 = 7
# C: 67 - 56 = 11
# D: 68 - 53 = 15
# E: 69 - 50 = 19
# Lucia: sum no relacionada directamente

# Quizas: control = (sum_ascii * K) mod M
# O: control = sum_ascii mod M con M variable
# O: control = suma de digitos de sum_ascii

# Probemos CRC, MD5, etc. con combinaciones simples
import hashlib

def md5_last2(s):
    h = hashlib.md5(s.encode()).hexdigest()
    return int(h[-2:], 16)

def md5_first2(s):
    h = hashlib.md5(s.encode()).hexdigest()
    return int(h[:2], 16)

def md5_mod(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % 100

print("\n=== Hash functions ===")
for nombre, ctrl in data:
    m2 = md5_mod(nombre)
    mf = md5_first2(nombre)
    print(f"  {nombre:6s}: md5_mod={m2:2d} md5_first2={mf:2d} expected={ctrl}")

# Intentar encontrar M tal que: control = ascii_sum mod M
print("\n=== Buscar M para letras A-E ===")
for M in range(50, 200):
    ok = True
    for nombre, ctrl_s in data:
        if len(nombre) > 1:
            continue
        expected = int(ctrl_s)
        actual = ascii_sum(nombre) % M
        if actual != expected:
            ok = False
            break
    if ok:
        print(f"  FOUND: ascii_sum mod {M} = control (para A-E)")

# Intentar: control = (ascii_sum + K) mod M
print("\n=== Buscar (ascii_sum + K) mod M para A-E ===")
for M in range(50, 200):
    for K in range(-20, 21):
        ok = True
        for nombre, ctrl_s in data:
            if len(nombre) > 1:
                continue
            expected = int(ctrl_s)
            actual = (ascii_sum(nombre) + K) % M
            if actual != expected:
                ok = False
                break
        if ok:
            print(f"  FOUND: (ascii_sum + {K}) mod {M} = control (para A-E)")

# Intentar con toda la data incluyendo Lucia y Mateo
# Quizas es: control = (ascii_sum * a + len * b + c) mod M
print("\n=== Buscar formula lineal general ===")
for M in range(50, 200):
    for a in range(-10, 11):
        for b in range(-10, 11):
            for c in range(-10, 11):
                ok = True
                for nombre, ctrl_s in data:
                    expected = int(ctrl_s)
                    actual = (a * ascii_sum(nombre) + b * len(nombre) + c) % M
                    if actual != expected:
                        ok = False
                        break
                if ok:
                    print(f"  FOUND: ({a}*sum + {b}*len + {c}) mod {M} = control")

print("\nHecho.")
