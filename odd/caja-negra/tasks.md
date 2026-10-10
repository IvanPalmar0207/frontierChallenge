# ODD Task Mirror — caja-negra

> Feature: Reverse-engineer y reemplazo del servicio "La caja negra"
> Branch: feat/caja-negra (se creará cuando empecemos a escribir código)

## Tareas

### [T1] Bootstrap del proyecto y endpoints base
- Crear estructura src/, requirements.txt, Procfile
- Implementar GET /health y POST /__reset
- Deploy inicial a Railway (smoke test)
- Status: pending
- Commit: —

### [T2] Parser de mensajes y validador de aridad
- Implementar split por ;, case-insensitive en comando
- Validar número de argumentos por comando
- Mapear comandos conocidos: PING, ALTA, CONSULTA, DEPOSITO, TRANSFER, ANULA
- Status: pending
- Commit: —

### [T3] Reverse engineering del dígito de control
- Analizar los 20 ejemplos para inferir fórmula
- Fuzzear variaciones de control contra el original
- Documentar resultado en experimentos.jsonl
- Status: pending
- Commit: —

### [T4] Comandos sin estado: PING
- Implementar PING → {pong: true}
- Validar que no depende de estado del token
- Status: pending
- Commit: —

### [T5] Comandos con estado: ALTA y CONSULTA
- ALTA crea cuenta con ID autoincremental AC-NNNN
- CONSULTA devuelve cuenta_id + saldo (inicial 0)
- Manejar errores E401 (cuenta inexistente)
- Status: pending
- Commit: —

### [T6] Comandos con estado: DEPOSITO y TRANSFER
- DEPOSITO acredita saldo y genera OP-NNNN
- TRANSFER verifica saldo y límite, debita/acredita, genera OP-NNNN
- Manejar errores E506 (límite excedido), E507 (saldo insuficiente)
- Status: pending
- Commit: —

### [T7] Comando ANULA
- ANULA revierte operación activa por OP-NNNN
- Marcar operación como anulada
- Manejar "ya anulada"
- Status: pending
- Commit: —

### [T8] Manejo de errores exactos
- Replicar status y body exacto de cada error del original
- E201, E202, E301, E302, E401, E506, E507
- Orden de evaluación de errores (¿control antes que aridad? ¿comando antes que todo?)
- Status: pending
- Commit: —

### [T9] Tests de regresión contra ejemplos
- Script que reproduce los 20 ejemplos exactos tras reset
- Comparar status y body byte a byte
- Status: pending
- Commit: —

### [T10] Fuzzing extendido y descubrimiento
- Probar edge cases: valores límite, caracteres especiales, secuencias inválidas
- Loguear en experimentos.jsonl con hipótesis
- Detectar cambios en el servicio original
- Status: pending
- Commit: —

### [T11] Documentación: especificación
- Completar docs/spec.md con las 7 secciones requeridas
- Citar líneas de experimentos.jsonl como evidencia
- Clasificar comportamientos en confirmado / probable / supuesto
- Status: pending
- Commit: —

### [T12] Deploy final y validación
- Deploy a Railway con entrypoint estable
- Validar en /evento/resultados
- Ajustes finales si hay tests fallidos
- Status: pending
- Commit: —
