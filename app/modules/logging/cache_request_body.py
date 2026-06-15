from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class CacheRequestBodyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if "application/json" in request.headers.get("content-type", ""):
            body = await request.body()
            request.state.body = body
        return await call_next(request)