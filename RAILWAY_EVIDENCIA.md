# Evidencia Final - Railway Deployment

**Fecha:** Ejecucion en vivo
**URL:** https://caja-negra-replacement-production.up.railway.app
**Resultado:** 20/20 ejemplos pasan
**Errores de servidor:** 0

---

## Resultado de los 20 ejemplos originales

| # |Mensaje|Status|Body|Resultado|
|---|-------|------|----|---------|
|01|PING;64|200|{"pong": true}|OK|
|02|ALTA;Lucia;83|400|{"error": "E202"}|OK (control invalido)|
|03|ALTA;Lucia;82|201|{"cuentaId": "AC-0001"}|OK|
|04|ALTA;Mateo;3|201|{"cuentaId": "AC-0002"}|OK|
|05|CONSULTA;AC-0001;14|200|{"saldo": 0}|OK|
|06|DEPOSITO;AC-0001;250000;86|200|{"operacionId": "OP-0001"}|OK|
|07|TRANSFER;AC-0001;AC-0002;40000;86|200|{"operacionId": "OP-0002"}|OK|
|08|CONSULTA;AC-0002;11|200|{"saldo": 40000}|OK|
|09|TRANSFER;AC-0001;AC-0002;120000;55|422|{"error": "E506"}|OK (limite excedido)|
|10|TRANSFER;AC-0001;AC-0002;100000;12|200|{"operacionId": "OP-0003"}|OK|
|11|CONSULTa;AC-0001;14|200|{"saldo": 110000}|OK (case insensitive)|
|12|SALDOS;AC-0001;38|400|{"error": "E301"}|OK (comando desconocido)|
|13|ANULA;OP-0003;66|200|{"ok": true}|OK|
|14|ANULA;OP-0003;66|200|{"ok": false}|OK (ya anulada)|
|15|CONSULTA;AC-0009;87|404|{"error": "E401"}|OK (cuenta inexistente)|
|16|TRANSFER;AC-0002;AC-0001;50000;23|422|{"error": "E507"}|OK (saldo insuficiente)|
|17|DEPOSITO;AC-0002;700;5X|400|{"error": "E201"}|OK (control mal formado)|
|18|DEPOSITO;AC-0002;700;35|200|{"operacionId": "OP-0004"}|OK|
|19|CONSULTA;AC-0002;11|200|{"saldo": 40700}|OK|
|20|ALTA;Lucia;Gomez;11|400|{"error": "E302"}|OK (aridad invalida)|

---

## Significado de los status HTTP que ves en los logs

### APISONADORES - Son respuestas CORRECTAS de tu API:
- **200 OK** - Todo bien (PING, CONSULTA, TRANSFER, DEPOSITO, ANULA ok)
- **201 Created** - ALTA exitosa, cuenta creada
- **400 Bad Request** - Error de cliente (control mal formado, aridad mala, comando desconocido)
- **404 Not Found** - Cuenta inexistente
- **422 Unprocessable Content** - Negocio (limite excedido E506, saldo insuf E507)

### DESASTROSAS - Si ves alguna de estas, hay problema:
- **500 Internal Server Error** - Servidor roto (NO APARECE)
- **502 Bad Gateway** - Railway caido (NO APARECE)
- **504 Gateway Timeout** - Timeout (NO APARECE)
- **422 con body `{"detail": [{"type": "missing"}]}`** - Bug de FastAPI (YA ARREGLADO)

---

## Fixes aplicados

1. **Body vacio/no-JSON** -> Antes daba 422 de Pydantic. Ahora da 400 E201.
2. **Formato de saldo** -> Antes string "2500.00". Ahora entero 250000.
3. **ANULA primera vez** -> Antes ok:false. Ahora ok:true (igual que V1).

---

## Comando para ver logs en vivo

```bash
railway logs --tail 20
```

Filtrar solo errores de servidor:
```bash
railway logs --tail 50 | grep -E "(500|502|504|ERROR|Traceback)"
```
(Si no devuelve nada, todo bien.)
