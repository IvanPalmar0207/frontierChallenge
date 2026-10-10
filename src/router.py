from fastapi import APIRouter, Header, Request, Body
from fastapi.responses import JSONResponse
from typing import Optional
from src.parser import parse_message
from src.engine import process_command
from src.state import reset_state
from src.errors import error_response

router = APIRouter()


def _extract_token(auth_header: Optional[str]) -> str:
    if not auth_header:
        return ""
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return auth_header


def _auth_error():
    body, status = error_response("E001")
    return JSONResponse(content=body, status_code=status)


@router.get("/health")
def health(authorization: Optional[str] = Header(None)):
    if not _extract_token(authorization):
        return _auth_error()
    return {"ok": True}


@router.post("/__reset")
def reset(authorization: Optional[str] = Header(None)):
    token = _extract_token(authorization)
    if not token:
        return _auth_error()
    reset_state(token)
    return {"ok": True}


@router.post("/msg")
def msg_endpoint(body: dict = Body(...), authorization: Optional[str] = Header(None)):
    token = _extract_token(authorization)
    if not token:
        return _auth_error()

    msg = body.get("m", "")
    comando, args, control_or_error = parse_message(msg)
    if comando is None:
        body, status = error_response(control_or_error)
        return JSONResponse(content=body, status_code=status)

    result, status = process_command(token, comando, args, control_or_error)
    return JSONResponse(content=result, status_code=status)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
def catch_all(path: str, request: Request):
    body, status = error_response("E404")
    return JSONResponse(content=body, status_code=status)
