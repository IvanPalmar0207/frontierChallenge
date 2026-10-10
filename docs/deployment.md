# Despliegue y ejecución — Black Box

> **Provisional.** Las instrucciones exactas se completarán cuando se conozca el entorno de ejecución oficial.

## Requisitos (propuestos)

- Entorno capaz de ejecutar Python 3.12+ (confirmar contra README oficial).
- Framework web async (FastAPI/uvicorn propuesto).
- Sin dependencias de red al servicio original.

## Instalación

```
[Pendiente de confirmar]
# pip install -r requirements.txt
```

## Configuración

| Variable | Estado | Descripción |
|----------|--------|-------------|
| `PORT` | Propuesto | Puerto de escucha |
| `[TOKEN_CONFIG]` | Pendiente | Configuración específica del reto |

## Ejecución local

```
[Pendiente de confirmar]
# uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Ejecución de pruebas

```
[Pendiente de confirmar]
# pytest tests/
```

## Construcción y despliegue

```
[Pendiente de confirmar]
# Plataforma: Railway, Render, o según indique README oficial
```

## Verificación de salud

- `GET /health` debe responder `200 OK`.
- `POST /__reset` debe limpiar el estado sin error.

## Diagnóstico de fallos

- Logs en stdout/stderr.
- Estado del token imprimible para debugging (solo desarrollo, nunca en producción).

## Independencia del servicio original

> **Crítico.** El reemplazo debe poder iniciarse y funcionar en una máquina sin acceso a internet.
> Verificar con `iptables -A OUTPUT -d <ip-original> -j DROP` o equivalente.
