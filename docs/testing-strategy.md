# Estrategia de pruebas — Black Box

## Categorías de pruebas

### 1. Pruebas de referencia

Reproducir exactamente los 20 ejemplos del material oficial.
- Secuencia completa tras `POST /__reset`.
- Comparar: status HTTP, body JSON (claves pueden estar en cualquier orden si ambos son JSON).
- Si alguno falla, hay un bug en el reemplazo o en nuestra comprensión.

### 2. Pruebas de equivalencia diferencial

Dada una secuencia de requests:
- Ejecutarla contra el original → capturar respuestas.
- Ejecutarla contra el reemplazo → capturar respuestas.
- Comparar diff byte a byte.
- Automatizar con script.

### 3. Pruebas de regresión

Conjunto de secuencias que pasaron en versiones anteriores del reemplazo.
- Se ejecutan en CI o antes de cada commit.
- Garantizan que el refactor no rompió comportamiento conocido.

### 4. Pruebas de casos límite

Basadas en hallazgos del fuzzing:
- Monto cero, negativo, muy grande.
- Nombres vacíos, con espacios, con unicode.
- Transferencia entre misma cuenta.
- Anulación de operación ya anulada.

### 5. Pruebas de errores

Cada código de error (E201-E507) debe tener al menos un test que lo dispare.
- Verificar status exacto.
- Verificar body exacto (incluyendo espacios y puntuación).

### 6. Pruebas de entradas malformadas

- JSON sin campo `m`.
- Campo `m` vacío.
- Caracteres no-ASCII en comando.
- Separadores faltantes o extra.

### 7. Pruebas de independencia

- Ejecutar reemplazo sin conectividad de red.
- Verificar que no hace requests salientes (inspección de tráfico, mock de socket).

### 8. Pruebas de despliegue

- `GET /health` responde 200.
- `POST /__reset` limpia estado.
- Reemplazo responde en < 5 segundos por request.

## Política de comparación

| Tipo de dato | Política |
|-------------|----------|
| Ambos JSON | Claves en cualquier orden, arrays en orden, strings/numbers idénticos |
| Alguno no es JSON | Comparación carácter por carácter exacta |
| Status HTTP | Debe ser idéntico |
| Headers | No se comparan en evaluación oficial |

## Cobertura conceptual

No presentamos porcentajes ficticios. La cobertura se mide en:

- Número de comandos distintos testeados / comandos conocidos.
- Número de códigos de error disparados / códigos conocidos.
- Número de secuencias de estado testeadas / comportamientos de estado identificados.

Inicialmente: **0% confirmada**. La cobertura crece con cada experimento.
