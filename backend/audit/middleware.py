from __future__ import annotations

import json
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("purpleclaw.audit")

_SKIP_PATHS = frozenset({"/health", "/platform/health", "/metrics", "/auth/login", "/"})
_AUDIT_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in _AUDIT_METHODS or request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)

        actor = _extract_actor(request)
        logger.info(
            json.dumps({
                "event": "audit",
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query) or None,
                "status": response.status_code,
                "actor": actor,
                "ip": request.client.host if request.client else "unknown",
                "duration_ms": duration_ms,
            })
        )
        return response


def _extract_actor(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return "anonymous"
    try:
        from auth.service import decode_token
        payload = decode_token(auth[7:])
        return payload.username
    except Exception:
        return "invalid-token"
