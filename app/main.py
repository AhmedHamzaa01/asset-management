from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.infrastructure.database import engine, Base
from app.domain import models
from app.api.v1.endpoints import assets, relationships, auth
from app.core.exceptions import NotFoundError, ConflictError, UnauthorizedError

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Asset Management API",
    description="DarkAtlas Asset Management System - Clean Architecture",
    version="1.0.0",
)


@app.exception_handler(NotFoundError)
def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(UnauthorizedError)
def unauthorized_handler(request: Request, exc: UnauthorizedError):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.get("/")
def root():
    return {"message": "Asset Management API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])
app.include_router(relationships.router, prefix="/api/v1", tags=["relationships"])
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])