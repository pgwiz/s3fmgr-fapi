
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Content-Security-Policy can be complex to configure.
        # This is a basic policy. You should tailor it to your needs.
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'"
        # HTTP Strict Transport Security (HSTS)
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
