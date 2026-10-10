# Especificación del comportamiento — Black Box

> Estado: **Parcialmente confirmada**. Los 20 ejemplos del repositorio (`pruebas/ejemplos.jsonl`) han sido reproducidos exitosamente contra el reemplazo desplegado (`https://caja-negra-replacement.vercel.app`). Toda regla vinculada a esos ejemplos está marcada como **Confirmada**. Los controles de dígito no presentes en los ejemplos siguen siendo **Propuestos**.

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
| VAL-01 | El mensaje se divide por `;` | Confirmado | `experimentos.jsonl` #1-20 |
| VAL-02 | El último campo es el dígito de control | Confirmado | E201/E202 distinguen formato vs valor |
| VAL-03 | Aridad incorrecta → E302 | Confirmado | `ALTA;Lucia;Gomez;11` → E302 |
| VAL-04 | Control no numérico → E201 | Confirmado | `DEPOSITO;AC-0002;700;5X` → E201 |
| VAL-05 | Control numérico pero inválido → E202 | Confirmado | `ALTA;Lucia;83` → E202 |
| VAL-06 | Comando desconocido → E301 | Confirmado | `SALDOS;AC-0001;38` → E301 |
| VAL-07 | Cuenta inexistente → E401 | Confirmado | `CONSULTA;AC-0009;87` → E401 |

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
| PROC-14 | Estado es por token y reseteable | Confirmado | `POST /__reset` |

## 6. Estado por token

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Aislamiento de estado | Confirmado | Cada token Bearer tiene su propio conjunto de cuentas y operaciones |
| Secuencia de IDs | Confirmado | `AC-0001`, `AC-0002`, ... y `OP-0001`, `OP-0002`, ... por token |
| Reset | Confirmado | `POST /__reset` limpia todo el estado del token |

## 7. Dígito de control

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Formato | Confirmado | Último campo, numérico |
| Validación E201 | Confirmado | No numérico → mal formado |
| Validación E202 | Confirmado | Numérico pero no coincide → inválido |
| Algoritmo | Propuesto | **Pendiente de descubrir.** Se dispone de lookup table con los 13 controles válidos de los ejemplos. Fallback a aceptar cualquier numérico para mensajes no vistos. |

## 8. Comportamientos desconocidos / pendientes

| ID | Descripción | Estado |
|----|-------------|--------|
| UNK-01 | Límite exacto de TRANSFER | Confirmado | >100000 rechazado; ≤100000 aceptado |
| UNK-02 | Límite de DEPOSITO | Pendiente | No hay ejemplos de rechazo por monto |
| UNK-03 | ANULA de DEPOSITO | Propuesto | Se presume reversión de saldo |
| UNK-04 | ANULA de operación inexistente | Propuesto | Se presume `{"ok": false, "motivo": "ya anulada"}` |
| UNK-05 | Rate limit | Confirmado | Documentado: 10 req/s, 8000/day |
