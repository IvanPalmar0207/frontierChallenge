"""
crack_intensive.py
Intenta encontrar la formula exacta del control V2.
Prueba miles de combinaciones de funciones hash.
"""
import hashlib, zlib, itertools, math, sys

# ====== DATOS CONOCIDOS ======
data = [
    ("ALTA", ["Lucia"], "82"),
    ("ALTA", ["Mateo"], "3"),
    ("ALTA", ["A"], "62"),
    ("ALTA", ["B"], "59"),
    ("ALTA", ["C"], "56"),
    ("ALTA", ["D"], "53"),
    ("ALTA", ["E"], "50"),
    ("ALTA", ["Test"], "37"),
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

def make_msg(comando, args, control=None):
    if control is None:
        return ";".join([comando] + args)
    return ";".join([comando] + args + [control])

def asciisum(s):
    return sum(ord(c) for c in s)

def asciiproduct(s):
    p = 1
    for c in s:
        p *= ord(c)
    return p

def xor_bytes(s):
    x = 0
    for c in s:
        x ^= ord(c)
    return x

def djb2(s):
    h = 5381
    for c in s:
        h = ((h << 5) + h) + ord(c)
    return h & 0xFFFFFFFF

def sdbm(s):
    h = 0
    for c in s:
        h = ord(c) + (h << 6) + (h << 16) - h
    return h & 0xFFFFFFFF

def fnv1a(s):
    h = 0x811c9dc5
    for c in s:
        h ^= ord(c)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h

def adler32(s):
    return zlib.adler32(s.encode()) & 0xFFFFFFFF

def crc32(s):
    return zlib.crc32(s.encode()) & 0xFFFFFFFF

def md5int(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16)

def sha1int(s):
    return int(hashlib.sha1(s.encode()).hexdigest(), 16)

def mod97(n):
    return (n % 97) + 1  # 1-97

def mod100(n):
    return n % 100

def mod97mod100(n):
    return n % 97 % 100

def transforms():
    """Genera todas las funciones candidato."""
    names = ["ALTA", "CONSULTA", "DEPOSITO", "TRANSFER", "ANULA"]
    
    for msg_type in ["full_msg", "args_only", "args_parts", "comando_args"]:
        for hash_fn_name, hash_fn in [
            ("asciisum", asciisum),
            ("xor", xor_bytes),
            ("djb2", djb2),
            ("sdbm", sdbm),
            ("fnv1a", fnv1a),
            ("adler32", adler32),
            ("crc32", crc32),
            ("md5", md5int),
            ("sha1", sha1int),
            ("len", len),
            ("asciisum+len", lambda s: asciisum(s) + len(s)),
            ("asciisum*len", lambda s: asciisum(s) * len(s)),
            ("asciisum^2", lambda s: asciisum(s) ** 2),
            ("xor+len", lambda s: xor_bytes(s) + len(s)),
            ("djb2+len", lambda s: djb2(s) + len(s)),
            ("djb2*len", lambda s: djb2(s) * len(s)),
            ("crc32+len", lambda s: crc32(s) + len(s)),
            ("asciisum*17", lambda s: asciisum(s) * 17),
            ("asciisum*31", lambda s: asciisum(s) * 31),
            ("djb2/100", lambda s: djb2(s) // 100),
            ("djb2/1000", lambda s: djb2(s) // 1000),
            ("adler32/100000", lambda s: adler32(s) // 100000),
            ("adler32/1000000", lambda s: adler32(s) // 1000000),
            ("crc32/1000000", lambda s: crc32(s) // 1000000),
            ("crc32/1000", lambda s: crc32(s) // 1000),
            ("crc32/10000", lambda s: crc32(s) // 10000),
            ("ascii_sum_mod100", lambda s: asciisum(s) % 100),
            ("ascii_sum_mod97", lambda s: asciisum(s) % 97),
            ("ascii_sum_mod97_1", lambda s: (asciisum(s) % 97) + 1),
            ("xor_mod97_1", lambda s: (xor_bytes(s) % 97) + 1),
            ("djb2_mod100", lambda s: djb2(s) % 100),
            ("djb2_mod97", lambda s: djb2(s) % 97),
            ("sdbm_mod100", lambda s: sdbm(s) % 100),
            ("sdbm_mod97", lambda s: sdbm(s) % 97),
            ("fnv1a_mod100", lambda s: fnv1a(s) % 100),
            ("fnv1a_mod97", lambda s: fnv1a(s) % 97),
            ("adler32_mod100", lambda s: adler32(s) % 100),
            ("crc32_mod100", lambda s: crc32(s) % 100),
            ("md5_mod100", lambda s: md5int(s) % 100),
            ("sha1_mod100", lambda s: sha1int(s) % 100),
        ]:
            for mod_fn_name, mod_fn in [
                ("mod100", mod100),
                ("mod97", mod97),
                ("mod97mod100", mod97mod100),
                ("mod99", lambda n: n % 99),
                ("mod100k", lambda n: n % 1000),
                ("ident", lambda n: n),
            ]:
                for include_control in [False, True]:
                    yield (
                        f"{msg_type}|{hash_fn_name}|{mod_fn_name}|ctrl={include_control}",
                        msg_type,
                        hash_fn,
                        mod_fn,
                        include_control,
                    )

def extract_string(comando, args, include_control, control):
    if control is None:
        return ";".join([comando] + args)
    if include_control:
        return ";".join([comando] + args + [control])
    return ";".join([comando] + args)

def test_candidate(name, msg_type, hash_fn, mod_fn, include_control, verbose=False):
    ok = 0
    for comando, args, control in data:
        if msg_type == "full_msg":
            s = extract_string(comando, args, include_control, control)
        elif msg_type == "args_only":
            s = ";".join(args)
        elif msg_type == "comando_args":
            s = ";".join([comando] + args)
        elif msg_type == "args_parts":
            s = "".join(args)
        else:
            return False
        
        try:
            h = hash_fn(s)
            val = mod_fn(h)
        except Exception:
            return False
        
        # Resultado esperado
        expected = int(control)
        if val != expected:
            if verbose:
                print(f"  FAIL {comando} {args}: expected {expected}, got {val} (hash={h}, s='{s}')")
            return False
        ok += 1
    return True

def main():
    print(f"Buscando formula exacta para {len(data)} ejemplos...")
    found = []
    total = 0
    for name, msg_type, hash_fn, mod_fn, include_ctrl in transforms():
        total += 1
        if test_candidate(name, msg_type, hash_fn, mod_fn, include_ctrl):
            print(f"\n  MATCH: {name}")
            found.append(name)
    
    print(f"\nTotal probados: {total}")
    if found:
        print(f"\n{'='*60}")
        print(f"ENCONTRO {len(found)} FORMULAS:")
        for f in found:
            print(f"  - {f}")
    else:
        print("\nNo se encontro formula exacta con esta bateria.")
        print("Pasando a fuzzing remoto ultra-selectivo...")

if __name__ == "__main__":
    main()
