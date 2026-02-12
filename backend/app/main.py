from fastapi import FastAPI
from app.api.routes.auth_routes import router as auth_router
from app.api.routes.batch_routes import router as batch_router
from app.api.routes.product_routes import router as product_router
from app.api.routes.lifecycle_routes import router as lifecycle_router
from app.api.routes.logistics_routes import router as logistics_router
from app.api.routes.processing_routes import router as processing_router
from app.api.routes.regulatory_routes import router as regulatory_router

app = FastAPI(
    title="AgriTrack API",
    description="Agricultural Traceability and Supply Chain Management System",
    version="1.0.0"
)

# Include routers
app.include_router(auth_router)
app.include_router(batch_router)
app.include_router(product_router)
app.include_router(lifecycle_router)
app.include_router(logistics_router)
app.include_router(processing_router)
app.include_router(regulatory_router)

@app.get("/")
def health():
    return {"status": "running", "api": "AgriTrack v1.0.0"}
