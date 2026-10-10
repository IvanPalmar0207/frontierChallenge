ERROR_CODES = {
    "E201": (400, "control mal formado"),
    "E202": (400, "control inválido"),
    "E301": (400, "comando desconocido "),
    "E302": (400, "aridad inválida"),
    "E401": (404, "cuenta inexistente"),
    "E506": (422, "límite excedido"),
    "E507": (422, "saldo insuficiente"),
}

def error_response(code: str):
    status, mensaje = ERROR_CODES[code]
    return {"error": code, "mensaje": mensaje}, status
