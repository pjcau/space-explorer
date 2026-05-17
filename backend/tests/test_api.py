"""Tests for space data API endpoints."""
import sys
import os

# Add packages directory to path for sqlalchemy and other dependencies BEFORE any backend imports
packages_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "packages")
sys.path.insert(0, packages_path)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from main import app
from database import engine, Base, SessionLocal
from models import Satellite, Asteroid, Planet


@pytest.fixture
def client():
    """Create test client with in-memory database."""
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    
    # Seed test data
    from seed import seed_satellites, seed_asteroids, seed_solar_system
    db = SessionLocal()
    seed_satellites(db)
    seed_asteroids(db)
    seed_solar_system(db)
    db.close()
    
    with TestClient(app) as c:
        yield c
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide database session for direct queries."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestSatellitesEndpoint:
    """Tests for GET /satellites endpoint."""
    
    def test_satellites_status_code(self, client):
        """Test endpoint returns 200 OK."""
        response = client.get("/satellites")
        assert response.status_code == 200
    
    def test_satellites_response_structure(self, client):
        """Test response has correct structure."""
        response = client.get("/satellites")
        data = response.json()
        
        assert "satellites" in data
        assert isinstance(data["satellites"], list)
        assert len(data["satellites"]) == 30
    
    def test_satellite_fields_present(self, client):
        """Test each satellite has required fields."""
        response = client.get("/satellites")
        data = response.json()
        
        required_fields = ["name", "norad_id", "altitude_km", "inclination_deg", "period_min"]
        
        for satellite in data["satellites"]:
            for field in required_fields:
                assert field in satellite, f"Missing field: {field}"
    
    def test_satellite_data_types(self, client):
        """Test satellite field data types."""
        response = client.get("/satellites")
        data = response.json()
        
        for satellite in data["satellites"]:
            assert isinstance(satellite["name"], str)
            assert isinstance(satellite["norad_id"], int)
            assert isinstance(satellite["altitude_km"], (int, float))
            assert isinstance(satellite["inclination_deg"], (int, float))
            assert isinstance(satellite["period_min"], (int, float))
    
    def test_satellite_values_reasonable(self, client):
        """Test satellite values are within realistic ranges."""
        response = client.get("/satellites")
        data = response.json()
        
        for satellite in data["satellites"]:
            # Altitude: LEO (160-2000), MEO (2000-35786), GEO (~35786)
            assert 100 <= satellite["altitude_km"] <= 40000, \
                f"Altitude {satellite['altitude_km']} out of range"
            
            # Inclination: 0-180 degrees
            assert 0 <= satellite["inclination_deg"] <= 180, \
                f"Inclination {satellite['inclination_deg']} out of range"
            
            # Period: 84 min (LEO) to 1436 min (GEO)
            assert 80 <= satellite["period_min"] <= 1500, \
                f"Period {satellite['period_min']} out of range"
    
    def test_satellites_deterministic(self, client):
        """Test that satellite data is deterministic."""
        response1 = client.get("/satellites")
        response2 = client.get("/satellites")
        
        assert response1.json() == response2.json()
    
    def test_satellites_sorted_by_norad_id(self, client):
        """Test satellites are sorted by NORAD ID."""
        response = client.get("/satellites")
        data = response.json()
        
        norad_ids = [s["norad_id"] for s in data["satellites"]]
        assert norad_ids == sorted(norad_ids)


class TestAsteroidsEndpoint:
    """Tests for GET /asteroids/recent endpoint."""
    
    def test_asteroids_status_code(self, client):
        """Test endpoint returns 200 OK."""
        response = client.get("/asteroids/recent")
        assert response.status_code == 200
    
    def test_asteroids_response_structure(self, client):
        """Test response has correct structure."""
        response = client.get("/asteroids/recent")
        data = response.json()
        
        assert "asteroids" in data
        assert isinstance(data["asteroids"], list)
        assert len(data["asteroids"]) == 10
    
    def test_asteroid_fields_present(self, client):
        """Test each asteroid has required fields."""
        response = client.get("/asteroids/recent")
        data = response.json()
        
        required_fields = ["name", "miss_distance_km", "velocity_kmps", "approach_date", "trajectory"]
        
        for asteroid in data["asteroids"]:
            for field in required_fields:
                assert field in asteroid, f"Missing field: {field}"
    
    def test_asteroid_data_types(self, client):
        """Test asteroid field data types."""
        response = client.get("/asteroids/recent")
        data = response.json()
        
        for asteroid in data["asteroids"]:
            assert isinstance(asteroid["name"], str)
            assert isinstance(asteroid["miss_distance_km"], (int, float))
            assert isinstance(asteroid["velocity_kmps"], (int, float))
            assert "approach_date" in asteroid
            assert isinstance(asteroid["trajectory"], list)
    
    def test_trajectory_structure(self, client):
        """Test trajectory is 5-point polyline with x, y, z."""
        response = client.get("/asteroids/recent")
        data = response.json()
        
        for asteroid in data["asteroids"]:
            trajectory = asteroid["trajectory"]
            assert len(trajectory) == 5, f"Trajectory should have 5 points, got {len(trajectory)}"
            
            for point in trajectory:
                assert "x" in point
                assert "y" in point
                assert "z" in point
                assert isinstance(point["x"], (int, float))
                assert isinstance(point["y"], (int, float))
                assert isinstance(point["z"], (int, float))
    
    def test_asteroid_values_reasonable(self, client):
        """Test asteroid values are within realistic ranges."""
        response = client.get("/asteroids/recent")
        data = response.json()
        
        for asteroid in data["asteroids"]:
            # Miss distance: should be > Earth radius (~6371 km)
            assert asteroid["miss_distance_km"] > 6371, \
                f"Miss distance {asteroid['miss_distance_km']} too small"
            
            # Velocity: typical asteroid approach 10-30 km/s
            assert 5 <= asteroid["velocity_kmps"] <= 50, \
                f"Velocity {asteroid['velocity_kmps']} out of range"
    
    def test_asteroids_sorted_by_date(self, client):
        """Test asteroids are sorted by approach date (most recent first)."""
        response = client.get("/asteroids/recent")
        data = response.json()
        
        dates = [a["approach_date"] for a in data["asteroids"]]
        assert dates == sorted(dates, reverse=True)
    
    def test_asteroids_deterministic(self, client):
        """Test that asteroid data is deterministic."""
        response1 = client.get("/asteroids/recent")
        response2 = client.get("/asteroids/recent")
        
        assert response1.json() == response2.json()


class TestRootEndpoint:
    """Tests for root health check endpoint."""
    
    def test_root_status_code(self, client):
        """Test root endpoint returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_response(self, client):
        """Test root endpoint returns expected response."""
        response = client.get("/")
        data = response.json()
        
        assert data["status"] == "ok"
        assert "message" in data


class TestSolarSystemEndpoint:
    """Tests for GET /solar-system endpoint."""
    
    def test_solar_system_status_code(self, client):
        """Test endpoint returns 200 OK."""
        response = client.get("/solar-system")
        assert response.status_code == 200
    
    def test_solar_system_returns_list(self, client):
        """Test response is a list of planets."""
        response = client.get("/solar-system")
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 8
    
    def test_solar_system_has_all_planets(self, client):
        """Test all 8 planets are present."""
        response = client.get("/solar-system")
        data = response.json()
        
        planet_names = [p["name"] for p in data]
        expected_planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
        
        assert planet_names == expected_planets
    
    def test_planet_fields_present(self, client):
        """Test each planet has required fields."""
        response = client.get("/solar-system")
        data = response.json()
        
        required_fields = ["name", "distance_au", "radius_km", "color", "moons"]
        
        for planet in data:
            for field in required_fields:
                assert field in planet, f"Missing field: {field}"
    
    def test_planet_data_types(self, client):
        """Test planet field data types."""
        response = client.get("/solar-system")
        data = response.json()
        
        for planet in data:
            assert isinstance(planet["name"], str)
            assert isinstance(planet["distance_au"], (int, float))
            assert isinstance(planet["radius_km"], (int, float))
            assert isinstance(planet["color"], str)
            assert isinstance(planet["moons"], list)
    
    def test_earth_has_moon(self, client):
        """Test Earth has Moon in its moons array."""
        response = client.get("/solar-system")
        data = response.json()
        
        earth = next((p for p in data if p["name"] == "Earth"), None)
        assert earth is not None
        assert "Moon" in earth["moons"]
    
    def test_mercury_no_moons(self, client):
        """Test Mercury has no moons."""
        response = client.get("/solar-system")
        data = response.json()
        
        mercury = next((p for p in data if p["name"] == "Mercury"), None)
        assert mercury is not None
        assert mercury["moons"] == []
    
    def test_color_is_hex_format(self, client):
        """Test color field is a valid hex string."""
        response = client.get("/solar-system")
        data = response.json()
        
        import re
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        
        for planet in data:
            assert hex_pattern.match(planet["color"]), f"Invalid hex color: {planet['color']}"
    
    def test_distance_au_positive(self, client):
        """Test distance_au values are positive."""
        response = client.get("/solar-system")
        data = response.json()
        
        for planet in data:
            assert planet["distance_au"] > 0, f"Distance {planet['distance_au']} should be positive"
    
    def test_radius_km_positive(self, client):
        """Test radius_km values are positive."""
        response = client.get("/solar-system")
        data = response.json()
        
        for planet in data:
            assert planet["radius_km"] > 0, f"Radius {planet['radius_km']} should be positive"
    
    def test_solar_system_deterministic(self, client):
        """Test that solar system data is deterministic."""
        response1 = client.get("/solar-system")
        response2 = client.get("/solar-system")
        
        assert response1.json() == response2.json()


class TestBodiesEndpoint:
    """Tests for GET /bodies/{kind}/{id} endpoint."""
    
    def test_get_planet_returns_details_with_no_parent_and_siblings(self, client):
        """Test GET /bodies/planet/{id} returns planet details, no parent, and sibling planets.
        
        This test verifies:
        - Planet endpoint returns 200 OK
        - Response includes id, name, type fields
        - Parent is None for planets
        - Siblings list contains other planets (up to 5)
        """
        # Get Earth (should be planet id 3 based on distance_au ordering)
        response = client.get("/bodies/planet/3")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields
        assert "id" in data
        assert "name" in data
        assert "type" in data
        assert "parent" in data
        assert "siblings" in data
        
        # Verify planet-specific values
        assert data["id"] == 3
        assert data["name"] == "Earth"
        assert data["type"] == "planet"
        
        # Planets have no parent
        assert data["parent"] is None
        
        # Siblings should be other planets (up to 5)
        assert isinstance(data["siblings"], list)
        assert len(data["siblings"]) <= 5
        assert len(data["siblings"]) > 0  # Should have at least some siblings
        
        # Each sibling should have id, name, type
        for sibling in data["siblings"]:
            assert "id" in sibling
            assert "name" in sibling
            assert "type" in sibling
            assert sibling["type"] == "planet"
    
    def test_get_moon_returns_details_with_parent_and_siblings(self, client):
        """Test GET /bodies/moon/{id} returns moon details, parent planet, and sibling moons.
        
        This test verifies:
        - Moon endpoint returns 200 OK
        - Response includes id, name, type fields
        - Parent is the planet the moon orbits
        - Siblings list contains other moons of the same planet (up to 5)
        """
        # Get Moon (Earth's moon, should be moon id 1)
        response = client.get("/bodies/moon/1")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields
        assert "id" in data
        assert "name" in data
        assert "type" in data
        assert "parent" in data
        assert "siblings" in data
        
        # Verify moon-specific values
        assert data["id"] == 1
        assert data["name"] == "Moon"
        assert data["type"] == "moon"
        
        # Moon should have a parent (Earth)
        assert data["parent"] is not None
        assert data["parent"]["id"] == 3  # Earth's id
        assert data["parent"]["name"] == "Earth"
        assert data["parent"]["type"] == "planet"
        
        # Siblings should be other moons of Earth (up to 5)
        assert isinstance(data["siblings"], list)
        assert len(data["siblings"]) <= 5
        
        # Each sibling should have id, name, type
        for sibling in data["siblings"]:
            assert "id" in sibling
            assert "name" in sibling
            assert "type" in sibling
            assert sibling["type"] == "moon"
    
    def test_get_satellite_returns_details_with_parent_and_siblings(self, client):
        """Test GET /bodies/satellite/{id} returns satellite details, parent planet, and sibling satellites.
        
        This test verifies:
        - Satellite endpoint returns 200 OK
        - Response includes id, name, type fields
        - Parent is the planet the satellite orbits
        - Siblings list contains other satellites orbiting the same planet (up to 5)
        - Tests with a satellite orbiting Mars (not Earth) to verify cross-reference
        """
        # Get a satellite orbiting Mars (should be satellite id 11 based on seed.py assigning 12 satellites to Mars)
        response = client.get("/bodies/satellite/11")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields
        assert "id" in data
        assert "name" in data
        assert "type" in data
        assert "parent" in data
        assert "siblings" in data
        
        # Verify satellite-specific values
        assert data["id"] == 11
        assert data["type"] == "satellite"
        
        # Satellite should have a parent (Mars)
        assert data["parent"] is not None
        assert data["parent"]["id"] == 4  # Mars's id
        assert data["parent"]["name"] == "Mars"
        assert data["parent"]["type"] == "planet"
        
        # Siblings should be other satellites orbiting Mars (up to 5)
        assert isinstance(data["siblings"], list)
        assert len(data["siblings"]) <= 5
        assert len(data["siblings"]) > 0  # Should have at least some siblings
        
        # Each sibling should have id, name, type
        for sibling in data["siblings"]:
            assert "id" in sibling
            assert "name" in sibling
            assert "type" in sibling
            assert sibling["type"] == "satellite"
    
    def test_get_invalid_kind_returns_400(self, client):
        """Test GET /bodies/{kind}/{id} with invalid kind returns 400 Bad Request."""
        response = client.get("/bodies/invalid/1")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "Invalid kind" in data["detail"]
    
    def test_get_nonexistent_planet_returns_404(self, client):
        """Test GET /bodies/planet/{id} with non-existent id returns 404 Not Found."""
        response = client.get("/bodies/planet/9999")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Planet not found" in data["detail"]
    
    def test_get_nonexistent_moon_returns_404(self, client):
        """Test GET /bodies/moon/{id} with non-existent id returns 404 Not Found."""
        response = client.get("/bodies/moon/9999")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Moon not found" in data["detail"]
    
    def test_get_nonexistent_satellite_returns_404(self, client):
        """Test GET /bodies/satellite/{id} with non-existent id returns 404 Not Found."""
        response = client.get("/bodies/satellite/9999")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Satellite not found" in data["detail"]
