from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.api.routes.listings import router as listings_router
from core.api.routes.plugins import router as plugins_router

app = FastAPI(
    title="RealEstatesAntiFraud Core API",
    version="1.0.0",
    description="Anti-fraud system for real estate listings",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

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
    return {"status": "ok", "version": "1.0.0"}
