from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Asteroid
from ..schemas import AsteroidResponse, AsteroidsResponse, Point3D
import json

router = APIRouter(prefix="/asteroids", tags=["asteroids"])


@router.get("/recent", response_model=AsteroidsResponse)
def get_recent_asteroids(db: Session = Depends(get_db)):
    """Get the 10 most recent asteroid close-approach routes."""
    asteroids = (
        db.query(Asteroid)
        .order_by(Asteroid.approach_date.desc())
        .limit(10)
        .all()
    )
    
    result = []
    for asteroid in asteroids:
        trajectory = json.loads(asteroid.trajectory)
        result.append(AsteroidResponse(
            name=asteroid.name,
            miss_distance_km=asteroid.miss_distance_km,
            velocity_kmps=asteroid.velocity_kmps,
            approach_date=asteroid.approach_date,
            trajectory=[Point3D(**p) for p in trajectory]
        ))
    
    return AsteroidsResponse(asteroids=result)
