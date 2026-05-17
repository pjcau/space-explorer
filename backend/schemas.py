"""Pydantic schemas for API responses."""
from pydantic import BaseModel
from typing import List, Optional


class SatelliteResponse(BaseModel):
    """Satellite response schema."""
    id: int
    name: str
    norad_id: int
    altitude_km: float
    inclination_deg: float
    period_min: float
    type: str
    country: str
    launch_year: int
    description: Optional[str] = None
    orbits_planet_id: Optional[str] = None

    class Config:
        from_attributes = True


class MoonResponse(BaseModel):
    """Moon response schema."""
    id: int
    name: str
    orbital_radius_km: float
    radius_km: float
    description: Optional[str] = None

    class Config:
        from_attributes = True


class PlanetResponse(BaseModel):
    """Planet response schema."""
    id: int
    name: str
    distance_au: float
    radius_km: float
    color: str
    rotation_period_hours: float
    description: Optional[str] = None
    moons: List[MoonResponse] = []

    class Config:
        from_attributes = True


class PlanetsResponse(BaseModel):
    """Wrapper for planets list."""
    planets: List[PlanetResponse]


class MoonsResponse(BaseModel):
    """Wrapper for moons list."""
    moons: List[MoonResponse]


class BodyParent(BaseModel):
    """Parent body information."""
    id: int
    name: str
    type: str


class BodySibling(BaseModel):
    """Sibling body information."""
    id: int
    name: str
    type: str


class BodyDetailResponse(BaseModel):
    """Response for GET /bodies/{kind}/{id} endpoint."""
    id: int
    name: str
    type: str
    parent: Optional[BodyParent] = None
    siblings: List[BodySibling] = []
