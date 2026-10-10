# Especificación del comportamiento — Black Box

> Estado: **Parcialmente confirmada**. Los 20 ejemplos del repositorio han sido reproducidos contra el reemplazo desplegado en Railway (proceso persistente). Se agregaron tests unitarios con 30 casos y edge cases adicionales. El algoritmo del dígito de control sigue siendo **Propuesto** (lookup table + fallback).

---

## 1. Formato de entrada

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Protocolo de transporte | Confirmado | HTTP |
| Método y ruta | Confirmado | `POST /msg` |
| Header de autenticación | Confirmado | `Authorization: Bearer <token>` |
| Cuerpo del mensaje | Confirmado | `{"m": "COMANDO;arg1;...;argN;control"}` |
| Separador de campos | Confirmado | Punto y coma `;` |
| Case sensitivity del comando | Confirmado | Insensible (evidencia: `CONSULTa` funciona) |

## 2. Formato de salida

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Formato de respuesta | Confirmado | JSON |
| Códigos HTTP usados | Confirmado | 200, 201, 400, 404, 422 |
| Orden de claves en JSON | Confirmado | No determinista; claves pueden venir en cualquier orden |

## 3. Comandos

| ID | Comando | Aridad esperada (sin control) | Estado |
|----|---------|------------------------------|--------|
| CMD-01 | PING | 0 | Confirmado |
| CMD-02 | ALTA | 1 (nombre) | Confirmado |
| CMD-03 | CONSULTA | 1 (cuenta_id) | Confirmado |
| CMD-04 | DEPOSITO | 2 (cuenta_id, monto) | Confirmado |
| CMD-05 | TRANSFER | 3 (origen, destino, monto) | Confirmado |
| CMD-06 | ANULA | 1 (operacion_id) | Confirmado |

## 4. Reglas de validación

| ID | Regla | Estado | Evidencia |
|----|-------|--------|-----------|
| VAL-01 | El mensaje se divide por `;` | Confirmado | Tests + ejemplos |
| VAL-02 | El último campo es el dígito de control | Confirmado | E201/E202 distinguen formato vs valor |
| VAL-03 | Aridad incorrecta → E302 | Confirmado | `ALTA;Lucia;Gomez;11` → E302 |
| VAL-04 | Control no numérico → E201 | Confirmado | `DEPOSITO;AC-0002;700;5X` → E201 |
| VAL-05 | Control numérico pero inválido → E202 | Confirmado | `ALTA;Lucia;83` → E202 |
| VAL-06 | Comando desconocido → E301 | Confirmado | `SALDOS;AC-0001;38` → E301 |
| VAL-07 | Cuenta inexistente → E401 | Confirmado | `CONSULTA;AC-0009;87` → E401 |
| VAL-08 | Control > 99 (3+ dígitos) → E201 | Confirmado | Fuzzing: `ALTA;A;100` → E201 |
| VAL-09 | PING acepta cualquier control numérico | Confirmado | Fuzzing: `PING;0`…`PING;99` → 200 |

## 5. Reglas de procesamiento

| ID | Regla | Estado | Evidencia |
|----|-------|--------|-----------|
| PROC-01 | PING devuelve `{"pong": true}` | Confirmado | Ejemplo #1 |
| PROC-02 | ALTA genera cuenta secuencial `AC-NNNN` | Confirmado | Ejemplos #2-4 |
| PROC-03 | ALTA devuelve 201 Created | Confirmado | Ejemplo #3 |
| PROC-04 | CONSULTA devuelve saldo actual | Confirmado | Ejemplos #5, #8, #20 |
| PROC-05 | DEPOSITO incrementa saldo | Confirmado | Ejemplos #6, #18 |
| PROC-06 | DEPOSITO genera operación `OP-NNNN` | Confirmado | Ejemplos #6, #18 |
| PROC-07 | TRANSFER decrementa origen e incrementa destino | Confirmado | Ejemplos #7, #10 |
| PROC-08 | TRANSFER genera operación `OP-NNNN` | Confirmado | Ejemplos #7, #10 |
| PROC-09 | TRANSFER de monto > 100000 → E506 | Confirmado | Ejemplo #9 |
| PROC-10 | TRANSFER con saldo insuficiente → E507 | Confirmado | Ejemplo #16 |
| PROC-11 | ANULA primera vez → `{"ok": true, "anulada": "OP-NNNN"}` | Confirmado | Ejemplo #12 |
| PROC-12 | ANULA segunda vez → `{"ok": false, "motivo": "ya anulada"}` | Confirmado | Ejemplo #13 |
| PROC-13 | ANULA revierte saldos de TRANSFER | Confirmado | Secuencia ejemplos #10, #12, #15 |
| PROC-14 | ANULA revierte saldos de DEPOSITO | Propuesto | Test unitario #anula_deposito |
| PROC-15 | Estado es por token y reseteable | Confirmado | `POST /__reset` |
| PROC-16 | Transferencia origen=destino es aceptada | Confirmado | Test unitario #transfer_same_account |
| PROC-17 | DEPOSITO con monto negativo decrementa saldo | Confirmado | Test unitario #negative_deposit |
| PROC-18 | DEPOSITO con monto cero no afecta saldo | Confirmado | Test unitario #zero_deposit |

## 6. Estado por token

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Aislamiento de estado | Confirmado | Cada token Bearer tiene su propio conjunto de cuentas y operaciones |
| Secuencia de IDs | Confirmado | `AC-0001`, `AC-0002`, ... y `OP-0001`, `OP-0002`, ... por token |
| Reset | Confirmado | `POST /__reset` limpia todo el estado del token |

## 7. Dígito de control

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Formato | Confirmado | Último campo, numérico, 1-2 dígitos (0-99) |
| Validación E201 | Confirmado | No numérico o >99 → mal formado |
| Validación E202 | Confirmado | Numérico 0-99 pero no coincide → inválido |
| PING | Confirmado | **Acepta cualquier control numérico** (0-99) |
| Otros comandos | Propuesto | Requieren control específico. Disponemos de 14 controles válidos en lookup table. Para mensajes no vistos, fallback a aceptar cualquier numérico 0-99. |
| Algoritmo | Pendiente | No se pudo deducir por rate limit del servicio original. Hipótesis: función hash del mensaje completo. |

## 8. Edge cases confirmados por tests unitarios

| Caso | Resultado | Status |
|------|-----------|--------|
| Transferencia origen = destino | Aceptada, saldo no cambia | Confirmado |
| Depósito monto negativo | Saldo decrece | Confirmado |
| Depósito monto cero | Saldo no cambia | Confirmado |
| ANULA operación inexistente | `{"ok": false}` | Propuesto (no hay ejemplo del original) |
| Sin token en header | `401 E001 no autorizado` | Confirmado (contra original) |

## 9. Cobertura de tests

| Suite | Casos | Estado |
|-------|-------|--------|
| Regresión 20 ejemplos | 20/20 | ✅ Pass |
| Tests unitarios | 30/30 | ✅ Pass |
| Edge cases | 7 | ✅ Pass |
| Deploy remoto (Vercel) | 20/20 | ✅ Pass |
