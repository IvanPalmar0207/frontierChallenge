from typing import Tuple, List, Optional

# Aridad esperada por comando (sin contar el control)
ARITY = {
    "PING": 0,
    "ALTA": 1,      # nombre;control
    "CONSULTA": 1,  # cuenta_id;control
    "DEPOSITO": 2,  # cuenta_id;monto;control
    "TRANSFER": 3,  # origen;destino;monto;control
    "ANULA": 1,     # op_id;control
}

def parse_message(msg: str) -> Tuple[Optional[str], Optional[List[str]], Optional[str]]:
    """
    Parsea el mensaje del formato COMANDO;arg1;...;control
    Retorna: (comando_upper, args_sin_control, control)
    En caso de error retorna (None, None, error_code)
    """
    if not msg:
        return None, None, "E201"

    parts = msg.split(";")
    if len(parts) < 1:
        return None, None, "E201"

    comando = parts[0].upper()
    control = parts[-1]
    args = parts[1:-1]

    # Comando desconocido
    if comando not in ARITY:
        return None, None, "E301"

    # Aridad inválida
    expected = ARITY[comando]
    if len(args) != expected:
        return None, None, "E302"

    # Control mal formado (no numérico)
    if not control.isdigit():
        return None, None, "E201"

    return comando, args, control
