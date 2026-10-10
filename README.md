# Black Box — La caja negra

> Reto 2 · Frontier Lab10

Reemplazo funcional de un servicio heredado sin código ni documentación.

## Deploy activo (Railway — proceso persistente)

```
https://caja-negra-replacement-production.up.railway.app
```

## Documentación

- `docs/specification.md` — Especificación completa con comportamientos confirmados
- `index.html` — Portal de documentación (abrir en navegador)

## Código

- `src/main.py` — FastAPI app
- `src/router.py` — Endpoints `/health`, `/__reset`, `/msg`
- `src/parser.py` — Parseo de mensajes `COMANDO;arg;...;control`
- `src/engine.py` — Lógica de negocio (PING, ALTA, CONSULTA, DEPOSITO, TRANSFER, ANULA)
- `src/state.py` — Estado en memoria por token
- `src/errors.py` — Códigos de error exactos (E001, E201–E507)
- `src/checksum.py` — Validación del dígito de control (lookup table + auto-learning)

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v   # 31 tests, 31/31 pass
```

## Entregables del reto

- [x] Reemplazo implementado y desplegado → Railway (proceso persistente)
- [x] Especificación del comportamiento → `docs/specification.md`
- [x] Registro de experimentos → `experimentos.jsonl` (25 entradas)
- [x] Pruebas de equivalencia → `tests/` (31 tests, 31/31 pass)

## Estado

✅ **20/20 ejemplos reproducidos** contra el reemplazo desplegado.
✅ **30 tests unitarios** cubriendo todos los comandos + edge cases.
✅ **Cláusulas del entrypoint** implementadas: auth, health, reset, rutas inexistentes.
⚠️ **Dígito de control**: lookup table con 14 controles + auto-learning. Algoritmo exacto no deducible por rate limit del original.
