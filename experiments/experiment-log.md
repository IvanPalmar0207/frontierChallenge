# Registro de Experimentos — Black Box

> Estado: plantilla inicial. Los experimentos reales se registrarán aquí durante la fase de ingeniería inversa.

---

## Formato de registro por experimento

Cada entrada debe contener los siguientes campos:

| Campo | Descripción |
|-------|-------------|
| **ID** | Identificador único del experimento (ej: `EXP-001`) |
| **Fecha/Hora** | Timestamp ISO 8601 |
| **Objetivo** | Qué se intenta descubrir o validar |
| **Hipótesis** | Suposición previa al experimento |
| **Entrada enviada** | Request exacto al servicio original |
| **Condiciones** | Estado previo, token utilizado, secuencia |
| **Respuesta exacta** | Status + body completo de la respuesta |
| **Error observado** | Si aplica, descripción del error |
| **Interpretación** | Análisis de qué indica la respuesta |
| **Conclusión** | Validación o refutación de la hipótesis |
| **Próximo experimento** | Qué probar a continuación |
| **Regla relacionada** | ID de la regla en `docs/specification.md` |

---

## Tabla de resumen

| ID | Objetivo | Estado | Conclusión | Regla |
|----|----------|--------|------------|-------|
| — | — | `[Pendiente]` | — | — |

---

## Notas importantes

- **No inventar resultados.** Toda entrada en este log debe corresponder a un experimento real contra el servicio original.
- Distinguir claramente entre **datos capturados** (respuesta exacta) y **conclusiones del investigador** (interpretación).
- Un experimento que refuta una hipótesis es tan valioso como uno que la confirma.
- Registrar también experimentos fallidos, timeouts y comportamientos inesperados.
