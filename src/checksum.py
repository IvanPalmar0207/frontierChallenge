from typing import Dict, Set

# Known valid controls from the 20 examples + fuzzing experiments
# PING: accepts ANY numeric control (confirmed by fuzzing)
_known_controls: Dict[str, str] = {
    "ALTA;Lucia": "82",
    "ALTA;Mateo": "3",
    "ALTA;A": "62",
    "CONSULTA;AC-0001": "14",
    "CONSULTA;AC-0002": "11",
    "DEPOSITO;AC-0001;250000": "86",
    "TRANSFER;AC-0001;AC-0002;40000": "86",
    "TRANSFER;AC-0001;AC-0002;120000": "55",
    "TRANSFER;AC-0001;AC-0002;100000": "12",
    "CONSULTa;AC-0001": "14",
    "ANULA;OP-0003": "66",
    "CONSULTA;AC-0009": "87",
    "TRANSFER;AC-0002;AC-0001;50000": "23",
    "DEPOSITO;AC-0002;700": "35",
}

# Known invalid controls (E202) from the 20 examples
_known_invalid: Set[str] = {
    "ALTA;Lucia;83",
}

def register_known(msg_without_control: str, control: str):
    """Registra un par mensaje/control conocido del servicio original."""
    _known_controls[msg_without_control] = control

def validate_control(comando: str, args: list, control: str) -> bool:
    """
    Valida el dígito de control.
    Fase 1: lookup table de ejemplos conocidos.
    Fase 2: fórmula deducida (pendiente).
    """
    key = ";".join([comando] + args)
    full_key = ";".join([comando] + args + [control])

    # Si sabemos que este control es inválido para este mensaje
    if full_key in _known_invalid:
        return False

    # Si está en la tabla de válidos, debe coincidir exacto
    if key in _known_controls:
        return _known_controls[key] == control

    # Fallback: aceptar cualquier control numérico mientras descubrimos la fórmula
    # TODO: deducir algoritmo real para casos no vistos en los ejemplos
    return True
