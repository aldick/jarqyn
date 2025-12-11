from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

app = FastAPI(
    title="Pavlodar Problem Reporting System",
    description="Backend API for city problem reporting prototype",
    version="0.1.0"
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "backend" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

from app.routes import reports, admin, public

app.include_router(reports.router, prefix="/api", tags=["Reports"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])
app.include_router(public.router, prefix="/api", tags=["Public"])

from app.database import engine, Base

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "Pavlodar Problem Reporting System API is running"}
