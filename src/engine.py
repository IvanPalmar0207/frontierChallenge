from typing import Tuple, Dict, Any
from src.state import get_state, Cuenta, Operacion
from src.errors import error_response
from src.checksum import validate_control, learn_control

def process_command(token: str, comando: str, args: list, control: str) -> Tuple[Dict[str, Any], int]:
    """
    Procesa un comando validado contra el estado del token.
    Retorna (body, status).
    """
    state = get_state(token)

    # Validar control
    if not validate_control(comando, args, control):
        body, status = error_response("E202")
        return body, status

    if comando == "PING":
        # PING accepts any numeric control; do not learn it
        return {"pong": True}, 200

    if comando == "ALTA":
        nombre = args[0]
        cuenta_id = f"AC-{state.next_cuenta:04d}"
        state.next_cuenta += 1
        state.cuentas[cuenta_id] = Cuenta(cuenta_id, nombre)
        learn_control(comando, args, control)
        return {"cuentaId": cuenta_id}, 201

    if comando == "CONSULTA":
        cuenta_id = args[0]
        if cuenta_id not in state.cuentas:
            body, status = error_response("E401")
            return body, status
        cuenta = state.cuentas[cuenta_id]
        learn_control(comando, args, control)
        return {"cuenta_id": cuenta.cuenta_id, "saldo": f"{cuenta.saldo / 100:.2f}"}, 200

    if comando == "DEPOSITO":
        cuenta_id = args[0]
        monto = int(args[1])
        if cuenta_id not in state.cuentas:
            body, status = error_response("E401")
            return body, status
        state.cuentas[cuenta_id].saldo += monto
        op_id = f"OP-{state.next_op:04d}"
        state.next_op += 1
        state.operaciones[op_id] = Operacion(op_id, "DEPOSITO", cuenta_id, "", monto)
        learn_control(comando, args, control)
        return {"status": "recieved", "operacionId": op_id}, 200

    if comando == "TRANSFER":
        origen = args[0]
        destino = args[1]
        monto = int(args[2])

        if origen not in state.cuentas or destino not in state.cuentas:
            body, status = error_response("E401")
            return body, status

        if state.cuentas[origen].saldo < monto:
            body, status = error_response("E507")
            return body, status

        if monto > 100000:
            body, status = error_response("E506")
            return body, status

        state.cuentas[origen].saldo -= monto
        state.cuentas[destino].saldo += monto
        op_id = f"OP-{state.next_op:04d}"
        state.next_op += 1
        state.operaciones[op_id] = Operacion(op_id, "TRANSFER", origen, destino, monto)
        learn_control(comando, args, control)
        return {"status": "recieved", "operacionId": op_id}, 200

    if comando == "ANULA":
        op_id = args[0]
        if op_id not in state.operaciones:
            # V2: ANULA siempre devuelve ok:false, incluso si op no existe o ya anulada
            # Pero SOLO revierte si la op existe y está activa
            return {"ok": False, "motivo": "ya anulada"}, 200
        op = state.operaciones[op_id]
        # V2: Siempre devuelve ok:false, pero revierte si está activa
        if op.activa:
            op.activa = False
            if op.tipo == "TRANSFER":
                state.cuentas[op.cuenta_origen].saldo += op.monto
                state.cuentas[op.cuenta_destino].saldo -= op.monto
            elif op.tipo == "DEPOSITO":
                state.cuentas[op.cuenta_origen].saldo -= op.monto
        learn_control(comando, args, control)
        return {"ok": False, "motivo": "ya anulada"}, 200

    return error_response("E301")
