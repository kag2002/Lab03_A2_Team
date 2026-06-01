import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("app.middleware.tracking")

class TrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Capture client IP and User-Agent
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        path = request.url.path
        method = request.method

        logger.info(f"Incoming request: {method} {path} | Client IP: {client_host} | User-Agent: {user_agent}")
        
        try:
            response: Response = await call_next(request)
        except Exception as e:
            process_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Request failed: {method} {path} | Process time: {process_time_ms:.2f}ms | Error: {str(e)}")
            raise e
            
        process_time_ms = (time.time() - start_time) * 1000
        
        # Add latency header to the response
        response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
        
        logger.info(f"Completed request: {method} {path} | Status: {response.status_code} | Process time: {process_time_ms:.2f}ms")
        
        return response
