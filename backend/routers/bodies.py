"""Router for bodies endpoint - GET /bodies/{kind}/{id}."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Planet, Moon, Satellite
from ..schemas import BodyDetailResponse, BodyParent, BodySibling

router = APIRouter(prefix="/bodies", tags=["bodies"])


@router.get("/{kind}/{body_id}", response_model=BodyDetailResponse)
def get_body(kind: str, body_id: int, db: Session = Depends(get_db)):
    """Get body details with parent and siblings.
    
    Args:
        kind: Type of body - 'planet', 'moon', or 'satellite'
        body_id: ID of the body
        db: Database session
    
    Returns:
        Body details with parent and first 5 siblings
    
    Raises:
        HTTPException: If body not found or invalid kind
    """
    kind = kind.lower()
    
    if kind == "planet":
        body = db.query(Planet).filter(Planet.id == body_id).first()
        if not body:
            raise HTTPException(status_code=404, detail="Planet not found")
        
        # Planets don't have parents, siblings are other planets
        siblings = db.query(Planet).filter(Planet.id != body_id).order_by(Planet.id).limit(5).all()
        sibling_list = [
            BodySibling(id=s.id, name=s.name, type="planet")
            for s in siblings
        ]
        
        return BodyDetailResponse(
            id=body.id,
            name=body.name,
            type="planet",
            parent=None,
            siblings=sibling_list
        )
    
    elif kind == "moon":
        moon = db.query(Moon).filter(Moon.id == body_id).first()
        if not moon:
            raise HTTPException(status_code=404, detail="Moon not found")
        
        # Get parent planet
        parent = db.query(Planet).filter(Planet.id == moon.planet_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent planet not found")
        
        parent_info = BodyParent(id=parent.id, name=parent.name, type="planet")
        
        # Get siblings (other moons of the same planet)
        siblings = db.query(Moon).filter(
            Moon.planet_id == moon.planet_id,
            Moon.id != moon.id
        ).order_by(Moon.id).limit(5).all()
        sibling_list = [
            BodySibling(id=s.id, name=s.name, type="moon")
            for s in siblings
        ]
        
        return BodyDetailResponse(
            id=moon.id,
            name=moon.name,
            type="moon",
            parent=parent_info,
            siblings=sibling_list
        )
    
    elif kind == "satellite":
        satellite = db.query(Satellite).filter(Satellite.id == body_id).first()
        if not satellite:
            raise HTTPException(status_code=404, detail="Satellite not found")
        
        # Get parent planet (by orbits_planet_id)
        parent = None
        if satellite.orbits_planet_id:
            parent = db.query(Planet).filter(Planet.name == satellite.orbits_planet_id).first()
        
        parent_info = None
        if parent:
            parent_info = BodyParent(id=parent.id, name=parent.name, type="planet")
        
        # Get siblings (other satellites orbiting the same planet)
        siblings = db.query(Satellite).filter(
            Satellite.orbits_planet_id == satellite.orbits_planet_id,
            Satellite.id != satellite.id
        ).order_by(Satellite.id).limit(5).all()
        sibling_list = [
            BodySibling(id=s.id, name=s.name, type="satellite")
            for s in siblings
        ]
        
        return BodyDetailResponse(
            id=satellite.id,
            name=satellite.name,
            type="satellite",
            parent=parent_info,
            siblings=sibling_list
        )
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid kind '{kind}'. Must be 'planet', 'moon', or 'satellite'"
        )
