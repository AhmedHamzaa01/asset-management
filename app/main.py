from fastapi import FastAPI
from app.infrastructure.database import engine, Base
from app.domain import models  # This imports all models so Alembic can see them
from app.api.v1.endpoints import assets, relationships, auth

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Asset Management API",
    description="DarkAtlas Asset Management System - Clean Architecture",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Asset Management API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Include routers from the new structure
app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])
app.include_router(relationships.router, prefix="/api/v1/relationships", tags=["relationships"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])