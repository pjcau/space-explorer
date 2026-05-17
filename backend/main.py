"""FastAPI application for space data visualization."""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import json

from .database import get_db, engine, Base
from .models import Satellite, Planet
from .schemas import SatelliteResponse, PlanetResponse, PlanetsResponse, MoonsResponse
from .routers import satellites, solar_system, bodies
from .seed import seed_satellites, seed_planets_and_moons, create_tables

# Create tables on startup
create_tables()

app = FastAPI(
    title="Space Data API",
    description="API for satellite and planet visualization data",
    version="1.0.0",
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(satellites.router)
app.include_router(solar_system.router)
app.include_router(bodies.router)


@app.on_event("startup")
def seed_database():
    """Seed database with data on startup."""
    from .database import SessionLocal
    db = SessionLocal()
    try:
        seed_satellites(db)
        seed_planets_and_moons(db)
    finally:
        db.close()


@app.get("/")
def root():
    """API health check endpoint."""
    return {"status": "ok", "message": "Space Data API is running"}


@app.get("/health")
def health_check():
    """Health check endpoint for docker-compose health checks."""
    return {"status": "healthy"}
