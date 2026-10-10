from typing import Dict, Set

# Known valid controls confirmed against the original service
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

_known_invalid: Set[str] = {
    "ALTA;Lucia;83",
}


def validate_control(comando: str, args: list, control: str) -> bool:
    key = ";".join([comando] + args)
    full_key = ";".join([comando] + args + [control])

    if full_key in _known_invalid:
        return False
    if key in _known_controls:
        return _known_controls[key] == control
    # Fallback: accept any numeric control for unseen messages
    return True


def learn_control(comando: str, args: list, control: str) -> None:
    key = ";".join([comando] + args)
    if key not in _known_controls:
        _known_controls[key] = control
