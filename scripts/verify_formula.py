"""
verify_formula.py
Prueba la formula exacta de CONSULTA en todos los datos.
Formula encontrada: (3 * (len(msg) - asciisum(msg))) % 97
"""
data = [
    ("ALTA", ["Lucia"], "82"),
    ("ALTA", ["Mateo"], "3"),
    ("ALTA", ["A"], "62"),
    ("ALTA", ["B"], "59"),
    ("ALTA", ["C"], "56"),
    ("ALTA", ["D"], "53"),
    ("ALTA", ["E"], "50"),
    ("CONSULTA", ["AC-0001"], "14"),
    ("CONSULTA", ["AC-0002"], "11"),
    ("CONSULTA", ["AC-0009"], "87"),
    ("DEPOSITO", ["AC-0001", "250000"], "86"),
    ("DEPOSITO", ["AC-0001", "1000"], "35"),
    ("DEPOSITO", ["AC-0001", "1"], "28"),
    ("DEPOSITO", ["AC-0001", "100"], "82"),
    ("DEPOSITO", ["AC-0002", "700"], "35"),
    ("TRANSFER", ["AC-0001", "AC-0002", "40000"], "86"),
    ("TRANSFER", ["AC-0001", "AC-0002", "120000"], "55"),
    ("TRANSFER", ["AC-0001", "AC-0002", "100000"], "12"),
    ("TRANSFER", ["AC-0002", "AC-0001", "50000"], "23"),
    ("ANULA", ["OP-0003"], "69"),
]

def asciisum(s):
    return sum(ord(c) for c in s)

def test_formula(msg_type="msg"):
    print(f"\n=== Probando mensaje tipo: {msg_type} ===")
    ok_all = True
    for comando, args, control in data:
        if msg_type == "msg":
            s = ";".join([comando] + args)
        elif msg_type == "args":
            s = ";".join(args)
        elif msg_type == "args_joined":
            s = "".join(args)
        elif msg_type == "no_semicolon":
            s = comando + ";".join(args)
        else:
            continue
        
        val = (3 * (len(s) - asciisum(s))) % 97
        expected = int(control)
        status = "OK" if val == expected else "FAIL"
        if val != expected:
            ok_all = False
        print(f"  {comando:12s} {args} -> expected {expected:2d}, got {val:2d} [{status}]")
    return ok_all

test_formula("msg")
test_formula("args")
test_formula("args_joined")

# Probar variantes de coeficientes
print("\n=== Buscando formula general mod 97... ===")
for a in range(-10, 11):
    for b in range(-10, 11):
        ok_all = True
        for comando, args, control in data:
            s = ";".join([comando] + args)
            val = (a * asciisum(s) + b * len(s)) % 97
            expected = int(control)
            if val != expected:
                ok_all = False
                break
        if ok_all:
            print(f"  MATCH: control = ({a} * sum + {b} * len) % 97")

# Probar formulas separadas por comando
for target_cmd in ["ALTA", "CONSULTA", "DEPOSITO", "TRANSFER", "ANULA"]:
    subset = [d for d in data if d[0] == target_cmd]
    if len(subset) < 2:
        continue
    print(f"\nBuscando formula para {target_cmd}...")
    for a in range(-10, 11):
        for b in range(-10, 11):
            ok_all = True
            for comando, args, control in subset:
                s = ";".join([comando] + args)
                val = (a * asciisum(s) + b * len(s)) % 97
                expected = int(control)
                if val != expected:
                    ok_all = False
                    break
            if ok_all:
                print(f"  MATCH [{target_cmd}]: ({a} * sum + {b} * len) % 97")
