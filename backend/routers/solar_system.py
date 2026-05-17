"""Router for solar system endpoints (planets and moons)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Planet, Moon
from ..schemas import PlanetResponse, MoonResponse, PlanetsResponse, MoonsResponse

router = APIRouter(prefix="/planets", tags=["planets"])


@router.get("/", response_model=List[PlanetResponse])
def get_planets(db: Session = Depends(get_db)):
    """Get list of all 8 planets in the solar system.
    
    Args:
        db: Database session
    
    Returns:
        List of planet objects
    """
    planets = db.query(Planet).order_by(Planet.distance_au).all()
    return [PlanetResponse.model_validate(p) for p in planets]


@router.get("/{planet_id}", response_model=PlanetResponse)
def get_planet(planet_id: int, db: Session = Depends(get_db)):
    """Get a specific planet by ID with its moons list.
    
    Args:
        planet_id: The planet ID
        db: Database session
    
    Returns:
        Planet object with moons list
    
    Raises:
        HTTPException: If planet not found
    """
    planet = db.query(Planet).filter(Planet.id == planet_id).first()
    if not planet:
        raise HTTPException(status_code=404, detail="Planet not found")
    
    planet_response = PlanetResponse.model_validate(planet)
    
    # Get moons for this planet
    moons = db.query(Moon).filter(Moon.planet_id == planet_id).all()
    planet_response.moons = [MoonResponse.model_validate(m) for m in moons]
    
    return planet_response


@router.get("/{planet_id}/moons", response_model=List[MoonResponse])
def get_planet_moons(planet_id: int, db: Session = Depends(get_db)):
    """Get all moons for a specific planet.
    
    Args:
        planet_id: The planet ID
        db: Database session
    
    Returns:
        List of moon objects
    
    Raises:
        HTTPException: If planet not found
    """
    planet = db.query(Planet).filter(Planet.id == planet_id).first()
    if not planet:
        raise HTTPException(status_code=404, detail="Planet not found")
    
    moons = db.query(Moon).filter(Moon.planet_id == planet_id).all()
    return [MoonResponse.model_validate(m) for m in moons]
