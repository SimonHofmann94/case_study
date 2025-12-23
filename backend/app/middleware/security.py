"""
Security Headers Middleware.

This middleware adds security-related HTTP headers to all responses
to protect against common web vulnerabilities.

Headers added:
- X-Content-Type-Options: Prevents MIME-type sniffing attacks
- X-Frame-Options: Prevents clickjacking by blocking iframe embedding
- X-XSS-Protection: Legacy XSS filter (for older browsers)
- Referrer-Policy: Controls how much referrer info is sent
- Permissions-Policy: Restricts browser features (camera, mic, etc.)
- Cache-Control: Prevents caching of sensitive data on API responses

Note: Strict-Transport-Security (HSTS) should be added at the
reverse proxy level (nginx/Caddy) when HTTPS is enabled.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all HTTP responses.

    These headers provide defense-in-depth against common web attacks
    even if other security measures fail.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME-type sniffing
        # Why: Stops browsers from interpreting files as different MIME types,
        # which could allow attackers to execute malicious scripts
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        # Why: Stops the page from being embedded in iframes on other sites,
        # preventing attackers from tricking users into clicking hidden elements
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection (for older browsers)
        # Why: Enables browser's built-in XSS filter. Modern browsers have
        # better protections, but this helps older browser versions
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        # Why: Limits how much URL information is sent to other sites,
        # preventing leakage of sensitive data in URLs
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features
        # Why: Disables access to sensitive browser APIs that this app doesn't need,
        # reducing attack surface if XSS occurs
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # Prevent caching of API responses
        # Why: Ensures sensitive data isn't stored in browser/proxy caches
        # Only apply to API routes, not static files
        if request.url.path.startswith("/api") or request.url.path in ["/auth", "/requests", "/offers"]:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response
