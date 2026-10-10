"""
crack_deep.py
Prueba hash + extracción de dígitos, y combinaciones lineales.
"""
import hashlib, itertools, json
from pathlib import Path

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

def make_msg(comando, args, include_control=None):
    if include_control:
        return ";".join([comando] + args + [include_control])
    return ";".join([comando] + args)

def md5_digits(s):
    h = hashlib.md5(s.encode()).hexdigest()
    return int(h[:2])

def sha1_digits(s):
    h = hashlib.sha1(s.encode()).hexdigest()
    return int(h[:2])

def md5_last2(s):
    h = hashlib.md5(s.encode()).hexdigest()
    return int(h[-2:], 16)

def sha1_last2(s):
    h = hashlib.sha1(s.encode()).hexdigest()
    return int(h[-2:], 16)

def md5_mod(s):
    h = hashlib.md5(s.encode()).hexdigest()
    return int(h, 16) % 100

def sha1_mod(s):
    h = hashlib.sha1(s.encode()).hexdigest()
    return int(h, 16) % 100

def asciisum(s):
    return sum(ord(c) for c in s)

def xor_bytes(s):
    x = 0
    for c in s:
        x ^= ord(c)
    return x

def product(s):
    p = 1
    for c in s:
        p *= ord(c)
    return p

def crc8(s):
    crc = 0xFF
    for c in s.encode():
        crc ^= c
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x31
            else:
                crc <<= 1
        crc &= 0xFF
    return crc

# ---- Prueba todas las combinaciones de combinaciones lineales ----
def test_all():
    hash_funcs = [
        ("asciisum", asciisum),
        ("xor", xor_bytes),
        ("product", product),
        ("crc8", crc8),
        ("md5_d2", md5_digits),
        ("sha1_d2", sha1_digits),
        ("md5_last2", md5_last2),
        ("sha1_last2", sha1_last2),
        ("md5_mod100", md5_mod),
        ("sha1_mod100", sha1_mod),
        ("len", len),
    ]
    
    ops = [
        ("mod100", lambda x: x % 100),
        ("mod97", lambda x: x % 97 + 1),
        ("mod99", lambda x: x % 99 + 1),
        ("mod89", lambda x: x % 89 + 1),
        ("ident", lambda x: x),
        ("div10", lambda x: x // 10),
        ("div100", lambda x: x // 100),
    ]
    
    # Para cada combinación de tipo de input
    for input_type in ["msg", "args_joined", "args_separated", "comando+args"]:
        for h_name, h_fn in hash_funcs:
            for op_name, op_fn in ops:
                ok = True
                for comando, args, control in data:
                    if input_type == "msg":
                        s = make_msg(comando, args)
                    elif input_type == "args_joined":
                        s = ";".join(args)
                    elif input_type == "args_separated":
                        s = "".join(args)
                    elif input_type == "comando+args":
                        s = ";".join([comando] + args)
                    else:
                        ok = False
                        break
                    
                    try:
                        val = op_fn(h_fn(s))
                    except:
                        ok = False
                        break
                    
                    if val != int(control):
                        ok = False
                        break
                
                if ok:
                    print(f"MATCH: {input_type} -> {h_name} -> {op_name}")

    # ---- Prueba combinaciones lineales de varias features ----
    print("\nProbando combinaciones lineales de features por argumento...")
    for comando_filter in [None, "ALTA", "CONSULTA", "DEPOSITO", "TRANSFER", "ANULA"]:
        subset = [d for d in data if comando_filter is None or d[0] == comando_filter]
        if len(subset) < 2:
            continue
        
        for base_fn_name, base_fn in [
            ("sum_ascii", asciisum),
            ("xor", xor_bytes),
            ("crc8", crc8),
            ("product", product),
        ]:
            for coef_a in range(-5, 6):
                for coef_b in range(-5, 6):
                    for mod_base in [97, 89, 101, 100, 99]:
                        ok = True
                        for comando, args, control in subset:
                            msg = make_msg(comando, args)
                            val = base_fn(msg)
                            result = ((val * coef_a) + (len(msg) * coef_b)) % mod_base
                            if result != int(control):
                                ok = False
                                break
                        if ok:
                            print(f"  LINEAR MATCH [{comando_filter or 'ALL'}]: {base_fn_name}*{coef_a} + len*{coef_b} mod {mod_base}")

test_all()
print("\nHecho.")
