"""Router for satellite endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Satellite
from ..schemas import SatelliteResponse, PlanetsResponse, MoonsResponse

router = APIRouter(prefix="/satellites", tags=["satellites"])


@router.get("/", response_model=List[SatelliteResponse])
def get_satellites(
    limit: int = Query(200, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """Get list of satellites with optional limit.
    
    Args:
        limit: Maximum number of satellites to return (default: 200, max: 10000)
        db: Database session
    
    Returns:
        List of satellite objects
    """
    satellites = db.query(Satellite).order_by(Satellite.norad_id).limit(limit).all()
    return [SatelliteResponse.model_validate(s) for s in satellites]


@router.get("/{satellite_id}", response_model=SatelliteResponse)
def get_satellite(satellite_id: int, db: Session = Depends(get_db)):
    """Get a specific satellite by ID.
    
    Args:
        satellite_id: The satellite ID
        db: Database session
    
    Returns:
        Satellite object
    
    Raises:
        HTTPException: If satellite not found
    """
    satellite = db.query(Satellite).filter(Satellite.id == satellite_id).first()
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return SatelliteResponse.model_validate(satellite)
