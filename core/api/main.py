import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Awaitable, Callable

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from core.api.routes.listings import router as listings_router
from core.api.routes.plugins import router as plugins_router
from core.utils.context import (
    clear_trace_context,
    get_trace_id,
    set_trace_context,
)
from core.utils.logging import configure_logging, get_logger

# Initialize structured logging
configure_logging()
logger = get_logger(__name__)

# HTTP headers for trace and request IDs
TRACE_ID_HEADER = "X-Trace-ID"
REQUEST_ID_HEADER = "X-Request-ID"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for application startup and shutdown.

    Logs important lifecycle events in structured format.
    """
    # Startup
    logger.info(
        "Application starting",
        context={
            "app_name": app.title,
            "version": app.version,
            "docs_url": app.docs_url,
        },
    )

    yield

    # Shutdown
    logger.info("Application shutting down", context={"app_name": app.title})


app = FastAPI(
    title="RealEstatesAntiFraud Core API",
    version="1.0.0",
    description="Anti-fraud system for real estate listings",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)


@app.middleware("http")
async def trace_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Middleware to manage trace and request IDs for distributed tracing.

    This middleware:
    1. Extracts or generates trace_id and request_id
    2. Sets them in the request context
    3. Propagates them in response headers
    4. Cleans up context after request
    """
    # Extract IDs from headers or generate new ones
    trace_id = request.headers.get(TRACE_ID_HEADER.lower())
    request_id = request.headers.get(REQUEST_ID_HEADER.lower())

    # Set trace context (generates IDs if not provided)
    trace_id, request_id = set_trace_context(trace_id, request_id)

    try:
        # Process request
        response = await call_next(request)

        # Add trace headers to response
        response.headers[TRACE_ID_HEADER] = trace_id
        response.headers[REQUEST_ID_HEADER] = request_id

        return response
    finally:
        # Always clear context to avoid leakage
        clear_trace_context()


@app.middleware("http")
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Middleware to log all HTTP requests with structured context.

    Logs request method, path, client IP, response time, and trace IDs.
    """
    start_time = time.time()

    # Get trace ID from context (set by trace_context_middleware)
    trace_id = get_trace_id()

    # Log incoming request
    logger.info(
        "HTTP request received",
        context={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "trace_id": trace_id,
        },
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log response
    logger.info(
        "HTTP request completed",
        context={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "trace_id": trace_id,
        },
    )

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 router
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(plugins_router, prefix="/plugins", tags=["plugins"])
api_v1_router.include_router(listings_router, prefix="/listings", tags=["listings"])

app.include_router(api_v1_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint - not versioned for monitoring tools."""
    logger.debug("Health check endpoint called")
    return {"status": "ok", "version": "1.0.0"}
