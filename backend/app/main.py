from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import auth, tasks
from app.config import settings
from app.database import engine, Base
from loguru import logger

app = FastAPI(title="Gmail Bill Scanner API")

# Allow requests from frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL] if settings.FRONTEND_URL else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes for auth and API endpoints (sync, bills)
app.include_router(auth.router, prefix="/auth")
app.include_router(tasks.router, prefix="/api")

@app.on_event("startup")
def startup_event():
    logger.info("Starting application...")
    # Auto-create database tables (use migrations in production)
    Base.metadata.create_all(bind=engine)
