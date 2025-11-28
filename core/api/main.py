import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from core.api.routes.listings import router as listings_router
from core.api.routes.plugins import router as plugins_router
from core.utils.logging import configure_logging, get_logger

# Initialize structured logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
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
async def log_requests(request: Request, call_next):
    """
    Middleware to log all HTTP requests with structured context.

    Logs request method, path, client IP, and response time.
    """
    start_time = time.time()

    # Log incoming request
    logger.info(
        "HTTP request received",
        context={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
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
async def health():
    """Health check endpoint - not versioned for monitoring tools."""
    logger.debug("Health check endpoint called")
    return {"status": "ok", "version": "1.0.0"}
