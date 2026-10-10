# System Design — Black Box

> Estado: **Propuesto** — sujeto a confirmación tras ingeniería inversa.

## 1. Visión general

Sistema de reemplazo de un servicio heredado sin documentación. El reemplazo debe comportarse exactamente igual que el original, incluyendo errores y casos límite.

## 2. Principios de diseño

- **Separación de investigación y ejecución**: el entorno de fuzzing nunca forma parte del reemplazo desplegado.
- **Trazabilidad**: cada regla de comportamiento se vincula con evidencia experimental.
- **Reproducibilidad**: las secuencias de prueba pueden repetirse desde un estado conocido.
- **Independencia**: el reemplazo funciona sin contacto con el servicio original.

## 3. Componentes lógicos

### Entorno de investigación

| Componente | Responsabilidad |
|-----------|----------------|
| Ejecutor de experimentos | Envía entradas controladas al servicio original |
| Capturador | Registra request/response/status exactos |
| Generador de casos | Crea mutaciones sistemáticas de entradas conocidas |
| Analizador de diferencias | Compara respuestas para inferir reglas |
| Registro | Persiste experimentos en `experimentos.jsonl` |

### Entorno de reemplazo

| Componente | Responsabilidad |
|-----------|----------------|
| Adaptador de entrada | Parsea y normaliza el mensaje según el protocolo descubierto |
| Validador | Verifica formato, aridad y checksum si aplica |
| Motor de reglas | Ejecuta la lógica de negocio derivada de la especificación |
| Estado interno | Mantiene memoria entre requests por token |
| Adaptador de salida | Formatea la respuesta conforme al contrato observado |
| Manejo de errores | Replica status y cuerpo exacto de errores del original |

## 4. Flujo de procesamiento

```
Request → Adaptador de entrada → Validador → Motor de reglas → Estado → Adaptador de salida → Response
                                      ↓
                              Manejo de errores → Error response exacto
```

## 5. Estado interno (propuesta)

El servicio original parece mantener estado por token de autorización. El reemplazo propone:

- Diccionario `dict[token, TokenState]` en memoria.
- `TokenState` contiene: cuentas, operaciones, contadores de ID, operaciones anuladas.
- `POST /__reset` limpia el estado del token a cero.

> **Pendiente de validar:** confirmar con experimentos que el estado es por token y no global.

## 6. Decisions pending

| ID | Decisión | Estado |
|----|----------|--------|
| ADR-01 | Formato exacto del protocolo (HTTP/JSON, TCP, etc.) | Pendiente |
| ADR-02 | Algoritmo de validación del campo de control | Pendiente |
| ADR-03 | Estrategia de generación de IDs (AC-NNNN, OP-NNNN) | Propuesto: secuencial |
| ADR-04 | Límite de transferencia y su valor exacto | Pendiente |
| ADR-05 | Política de saldos negativos | Pendiente |
