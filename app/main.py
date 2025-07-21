# app/main.py
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base  # Import Base from models package
from app.routers import tags, activities, users, insights, patterns, routines

load_dotenv()


# Create tables on startup
# noinspection PyUnusedLocal
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass


# Initialize FastAPI app
app = FastAPI(
    title="FlipFlow API",
    description="ADHD-focused activity tracking system backend",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(tags.router, prefix="/api/tags", tags=["tags"])
app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(patterns.router, prefix="/api/patterns", tags=["patterns"])
app.include_router(routines.router, prefix="/api/routines", tags=["routines"])


@app.get("/")
async def root():
    return {
        "message": "FlipFlow API",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "flipflow-api"
    }
