from typing import Dict, List

class Cuenta:
    def __init__(self, cuenta_id: str, nombre: str):
        self.cuenta_id = cuenta_id
        self.nombre = nombre
        self.saldo = 0

class Operacion:
    def __init__(self, op_id: str, tipo: str, cuenta_origen: str, cuenta_destino: str,
                 monto: int, activa: bool = True):
        self.op_id = op_id
        self.tipo = tipo  # DEPOSITO, TRANSFER
        self.cuenta_origen = cuenta_origen
        self.cuenta_destino = cuenta_destino
        self.monto = monto
        self.activa = activa

class TokenState:
    def __init__(self):
        self.cuentas: Dict[str, Cuenta] = {}
        self.operaciones: Dict[str, Operacion] = {}
        self.next_cuenta = 1
        self.next_op = 1

    def reset(self):
        self.cuentas.clear()
        self.operaciones.clear()
        self.next_cuenta = 1
        self.next_op = 1

# Global in-memory state per token
state_store: Dict[str, TokenState] = {}

def get_state(token: str) -> TokenState:
    if token not in state_store:
        state_store[token] = TokenState()
    return state_store[token]

def reset_state(token: str):
    if token in state_store:
        state_store[token].reset()
