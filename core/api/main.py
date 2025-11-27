from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.api.routes.listings import router as listings_router
from core.api.routes.plugins import router as plugins_router

app = FastAPI(title="RealEstatesAntiFraud Core API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plugins_router, prefix="/api/plugins", tags=["plugins"])
app.include_router(listings_router, prefix="/api/listings", tags=["listings"])


@app.get("/health")
async def health():
    return {"status": "ok"}
