"""Database models for satellites, planets, and moons."""
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Satellite(Base):
    """Satellite model for LEO/MEO/GEO satellites."""
    __tablename__ = "satellites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    norad_id = Column(Integer, unique=True, nullable=False, index=True)
    altitude_km = Column(Float, nullable=False)
    inclination_deg = Column(Float, nullable=False)
    period_min = Column(Float, nullable=False)
    type = Column(String(10), nullable=False)  # LEO, MEO, or GEO
    country = Column(String(100), nullable=False)
    launch_year = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    orbits_planet_id = Column(String(100), ForeignKey("planets.name"), nullable=True, default='earth')


class Planet(Base):
    """Planet model for solar system planets."""
    __tablename__ = "planets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    distance_au = Column(Float, nullable=False)
    radius_km = Column(Float, nullable=False)
    color = Column(String(20), nullable=False)  # Hex color string
    rotation_period_hours = Column(Float, nullable=False)
    description = Column(Text, nullable=True)


class Moon(Base):
    """Moon model for planetary moons."""
    __tablename__ = "moons"

    id = Column(Integer, primary_key=True, index=True)
    planet_id = Column(Integer, ForeignKey("planets.id"), nullable=False)
    name = Column(String(100), nullable=False)
    orbital_radius_km = Column(Float, nullable=False)
    radius_km = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
