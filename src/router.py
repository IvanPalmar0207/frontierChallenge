from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from typing import Optional
from src.models import MsgRequest
from src.parser import parse_message
from src.engine import process_command
from src.state import reset_state
from src.errors import error_response
# Rate limiting disabled for now — not confirmed by examples
# from src.ratelimit import check_rate

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/__reset")
def reset(authorization: Optional[str] = Header(None)):
    token = _extract_token(authorization)
    reset_state(token)
    return {}

@router.post("/msg")
def msg_endpoint(request: MsgRequest, authorization: Optional[str] = Header(None)):
    token = _extract_token(authorization)
    if not token:
        # Comportamiento sin token: replicar como el original
        return JSONResponse(content={"error": "E401", "mensaje": "token requerido"}, status_code=401)

    comando, args, control_or_error = parse_message(request.m)
    if comando is None:
        body, status = error_response(control_or_error)
        return JSONResponse(content=body, status_code=status)

    body, status = process_command(token, comando, args, control_or_error)
    return JSONResponse(content=body, status_code=status)

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
def catch_all(path: str, request: Request, authorization: Optional[str] = Header(None)):
    """Cualquier otra ruta: replicar comportamiento del original."""
    return JSONResponse(content={"error": "E301", "mensaje": "comando desconocido "}, status_code=400)

def _extract_token(auth_header: Optional[str]) -> str:
    if not auth_header:
        return ""
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return auth_header
