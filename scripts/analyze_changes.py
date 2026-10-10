#!/usr/bin/env python3
"""Analisis de los 3 cambios V2 vs V1."""

# Cambio 1: Saldo en formato string monetario
print("=== CAMBIO 1: Formato de saldo ===")
print("V1: {'saldo': 0}          (int)")
print("V2: {'saldo': '2500.00'}   (string con 2 decimales)")
print("Relacion: saldo_V2 = saldo_real / 100")
print("Ejemplo: DEPOSITO 250000 -> saldo '2500.00' (250000/100)")
print("         TRANSFER 40000  -> origen '2100.00' (210000/100)")
print()

# Cambio 2: ANULA requiere control valido (no acepta cualquiera)
print("=== CAMBIO 2: ANULA requiere control valido ===")
print("V1: ANULA con cualquier control numérico funcionaba (si op existe)")
print("V2: ANULA con control invalido -> E202")
print("Observado: ANULA OP-9999 con control valido -> E202 (control invalido para ese mensaje)")
print()

# Cambio 3: El control del checksum cambió (algoritmo diferente o valores diferentes)
print("=== CAMBIO 3: Dígito de control diferente ===")
print("V1: DEPOSITO;AC-0001;1000 -> ctrl 86")
print("V2: DEPOSITO;AC-0001;1000 -> ctrl=35 (descubierto por fuzzing)")
print("V1: TRANSFER;AC-0001;AC-0002;40000 -> ctrl 86")
print("V2: mismo mensaje -> E202 con ctrl V1, ctrl correcto aun por determinar")
print("PERO: Los controles ALTA V1 siguen funcionando (82, 3, 62)")
print()

print("=== RESUMEN ===")
print("1. Saldo en formato monetario string (dividido por 100)")
print("2. ANULA ahora valida control estrictamente (no fallback)")
print("3. Algoritmo de control cambió para algunos comandos")
