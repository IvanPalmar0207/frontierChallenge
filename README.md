# Black Box — La caja negra

> Reto 2 · Frontier Lab10

Reemplazo funcional de un servicio heredado sin código ni documentación. El objetivo es que responda exactamente igual — errores incluidos.

## Deploy activo

```
https://caja-negra-replacement.vercel.app
```

## Documentación

Abre **`index.html`** en un navegador para acceder al portal completo de documentación, o visita el deploy para la versión estática.

### Estructura

- `docs/system-design.md` — Visión general del sistema y principios de diseño
- `docs/architecture.md` — Diagramas de arquitectura y componentes
- `docs/specification.md` — Especificación completa con comportamientos confirmados
- `docs/reverse-engineering-strategy.md` — Estrategia de ingeniería inversa por fases
- `docs/testing-strategy.md` — Categorías de pruebas y políticas de comparación
- `docs/deployment.md` — Instrucciones de despliegue
- `PRUEBAS.md` — Guía de pruebas manuales con `curl`

## Código

- `src/main.py` — FastAPI app
- `src/parser.py` — Parseo de mensajes `COMANDO;arg;...;control`
- `src/checksum.py` — Validación del dígito de control (lookup table)
- `src/engine.py` — Lógica de negocio (PING, ALTA, CONSULTA, DEPOSITO, TRANSFER, ANULA)
- `src/errors.py` — Códigos de error exactos (E201–E507)
- `src/state.py` — Estado en memoria por token
- `src/router.py` — Endpoints `/health`, `/__reset`, `/msg`

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests/test_commands.py -v   # 30 tests unitarios
python -m pytest tests/test_ejemplos.py -v   # 20 tests de regresión
python scripts/test_remoto.py                 # Validación contra deploy
python scripts/demo.py                        # Demo visual local
```

## Entregables del reto

- [x] Reemplazo implementado y desplegado → `https://caja-negra-replacement.vercel.app`
- [x] Especificación del comportamiento → `docs/specification.md`
- [x] Registro de experimentos → `experimentos.jsonl` (25 entradas)
- [x] Pruebas de equivalencia → `tests/` (50 tests, 50/50 pass)

## Estado

✅ **20/20 ejemplos reproducidos** contra el reemplazo desplegado.
✅ **30 tests unitarios** cubriendo PING, ALTA, CONSULTA, DEPOSITO, TRANSFER, ANULA.
✅ **Edge cases** validados: transfer origen=destino, monto negativo, monto cero, ANULA inexistente, state por token.
⚠️ **Dígito de control**: lookup table con 14 controles conocidos + fallback para mensajes no vistos. El algoritmo exacto no fue deducible por rate limit del servicio original.
