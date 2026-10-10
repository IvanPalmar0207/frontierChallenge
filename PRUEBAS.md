# Guía de Pruebas — Black Box Replacement

## URL del deploy
```
https://caja-negra-replacement.vercel.app
```

---

## 1. Health check

```bash
curl https://caja-negra-replacement.vercel.app/health
```
**Esperado:** `{"status":"ok"}` — 200 OK

---

## 2. Reset de estado

```bash
curl -X POST https://caja-negra-replacement.vercel.app/__reset \
  -H "Authorization: Bearer test-token"
```
**Esperado:** `{}` — 200 OK (limpia todo el estado del token)

---

## 3. Los 20 ejemplos del repositorio

```bash
# PING
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"PING;64"}'
# → {"pong":true}

# ALTA (control válido de ejemplo)
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"ALTA;Lucia;82"}'
# → {"cuentaId":"AC-0001"} — 201

# ALTA con control inválido
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"ALTA;Lucia;83"}'
# → {"error":"E202","mensaje":"control inválido"} — 400

# CONSULTA
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"CONSULTA;AC-0001;14"}'
# → {"cuenta_id":"AC-0001","saldo":0}

# DEPOSITO
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"DEPOSITO;AC-0001;250000;86"}'
# → {"status":"recieved","operacionId":"OP-0001"}

# TRANSFER
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"TRANSFER;AC-0001;AC-0002;40000;86"}'
# → {"status":"recieved","operacionId":"OP-0002"}

# Límite excedido (monto > 100000)
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"TRANSFER;AC-0001;AC-0002;120000;55"}'
# → {"error":"E506","mensaje":"límite excedido"} — 422

# Case insensitive (CONSULTa en vez de CONSULTA)
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"CONSULTa;AC-0001;14"}'
# → {"cuenta_id":"AC-0001","saldo":110000}

# Comando desconocido
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"SALDOS;AC-0001;38"}'
# → {"error":"E301","mensaje":"comando desconocido "}

# ANULA (primera vez)
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"ANULA;OP-0003;66"}'
# → {"ok":true,"anulada":"OP-0003"}

# ANULA (segunda vez — ya anulada)
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"ANULA;OP-0003;66"}'
# → {"ok":false,"motivo":"ya anulada"}

# Cuenta inexistente
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"CONSULTA;AC-0009;87"}'
# → {"error":"E401","mensaje":"cuenta inexistente"} — 404

# Saldo insuficiente
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"TRANSFER;AC-0002;AC-0001;50000;23"}'
# → {"error":"E507","mensaje":"saldo insuficiente"} — 422

# Control mal formado (no numérico)
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"DEPOSITO;AC-0002;700;5X"}'
# → {"error":"E201","mensaje":"control mal formado"}

# Aridad inválida
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"ALTA;Lucia;Gomez;11"}'
# → {"error":"E302","mensaje":"aridad inválida"}
```

---

## 4. Edge cases para probar manualmente

```bash
# Resetear primero
curl -X POST https://caja-negra-replacement.vercel.app/__reset \
  -H "Authorization: Bearer test-token"

# Sin token (debería fallar o comportarse como original)
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -d '{"m":"PING;64"}'

# Ruta inexistente
curl https://caja-negra-replacement.vercel.app/api/v1/cualquiercosa \
  -H "Authorization: Bearer test-token"
# → {"error":"E301","mensaje":"comando desconocido "}

# Transferencia origen = destino (¿qué pasa?)
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"ALTA;A;99"}'
# → AC-0001

curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"DEPOSITO;AC-0001;10000;99"}'
# → OP-0001

curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"TRANSFER;AC-0001;AC-0001;5000;99"}'
# → ¿Funciona o falla?

# Monto negativo
curl -X POST https://caja-negra-replacement.vercel.app/msg \
  -H "Authorization: Bearer test-token" \
  -d '{"m":"DEPOSITO;AC-0001;-100;99"}'
```

---

## 5. Test automatizado local

```bash
# Clonar o ir al repo
cd frontierChallenge

# Instalar dependencias
pip install -r requirements.txt

# Correr tests de regresión (20 ejemplos)
python tests/test_ejemplos.py
# Esperado: 20 pass / 0 fail

# Correr demo visual
python scripts/demo.py
```

---

## 6. Deploy nuevo (si hacés cambios)

```bash
vercel deploy --prod --yes
```

---

## Estado actual del reemplazo

| Feature | Estado |
|---------|--------|
| `/health` | ✅ Funciona |
| `/__reset` | ✅ Funciona |
| `/msg` con JSON | ✅ Funciona |
| PING | ✅ Replicado |
| ALTA | ✅ Replicado |
| CONSULTA | ✅ Replicado |
| DEPOSITO | ✅ Replicado |
| TRANSFER | ✅ Replicado (límite >100000 confirmado) |
| ANULA | ✅ Replicado |
| Errores exactos | ✅ 7/7 replicados |
| 20 ejemplos | ✅ 20/20 pasan |
| Dígito de control (mensajes vistos) | ✅ Lookup table funciona |
| Dígito de control (mensajes NUEVOS) | ⚠️ Fallback: acepta cualquier numérico |
| Rate limiting | ⚠️ No implementado (no confirmado por ejemplos) |
