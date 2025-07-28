import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send
import logging
import contextvars

# Context variable for correlation ID
correlation_id_ctx_var = contextvars.ContextVar("correlation_id", default=None)

def get_correlation_id() -> str:
    return correlation_id_ctx_var.get() or "-"

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, header_name: str = "X-Correlation-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        correlation_id = request.headers.get(self.header_name)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        # Set in context var
        token = correlation_id_ctx_var.set(correlation_id)
        # Add to request.state for downstream use
        request.state.correlation_id = correlation_id
        # Add to logging context
        old_factory = logging.getLogRecordFactory()
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.correlation_id = correlation_id
            return record
        logging.setLogRecordFactory(record_factory)
        try:
            response = await call_next(request)
            response.headers[self.header_name] = correlation_id
            return response
        finally:
            correlation_id_ctx_var.reset(token)
            logging.setLogRecordFactory(old_factory) 