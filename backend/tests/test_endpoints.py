"""Pytest tests for all 5 API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..database import Base, get_db
from ..main import app
from ..seed import seed_satellites, seed_planets_and_moons


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_space_data.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with mocked database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestSatellitesEndpoints:
    """Tests for satellite endpoints."""
    
    def test_get_satellites_list(self, client, db_session):
        """Test GET /satellites endpoint returns list of satellites."""
        # Seed data
        seed_satellites(db_session)
        
        response = client.get("/satellites?limit=200")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check required fields
        for sat in data:
            assert "id" in sat
            assert "name" in sat
            assert "norad_id" in sat
            assert "altitude_km" in sat
            assert "inclination_deg" in sat
            assert "period_min" in sat
            assert "type" in sat
            assert "country" in sat
            assert "launch_year" in sat
    
    def test_get_satellites_with_limit(self, client, db_session):
        """Test GET /satellites with limit parameter."""
        seed_satellites(db_session)
        
        response = client.get("/satellites?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10
    
    def test_get_satellite_by_id(self, client, db_session):
        """Test GET /satellites/{id} endpoint."""
        seed_satellites(db_session)
        
        # Get first satellite ID
        response = client.get("/satellites?limit=1")
        assert response.status_code == 200
        first_sat = response.json()[0]
        sat_id = first_sat["id"]
        
        # Get specific satellite
        response = client.get(f"/satellites/{sat_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sat_id
        assert data["name"] == first_sat["name"]
    
    def test_get_satellite_not_found(self, client, db_session):
        """Test GET /satellites/{id} returns 404 for non-existent ID."""
        response = client.get("/satellites/99999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestPlanetsEndpoints:
    """Tests for planet endpoints."""
    
    def test_get_planets_list(self, client, db_session):
        """Test GET /planets endpoint returns list of 8 planets."""
        seed_planets_and_moons(db_session)
        
        response = client.get("/planets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 8
        
        # Check required fields
        for planet in data:
            assert "id" in planet
            assert "name" in planet
            assert "distance_au" in planet
            assert "radius_km" in planet
            assert "color" in planet
            assert "rotation_period_hours" in planet
    
    def test_get_planet_by_id(self, client, db_session):
        """Test GET /planets/{id} endpoint."""
        seed_planets_and_moons(db_session)
        
        # Get first planet ID
        response = client.get("/planets")
        assert response.status_code == 200
        first_planet = response.json()[0]
        planet_id = first_planet["id"]
        
        # Get specific planet
        response = client.get(f"/planets/{planet_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == planet_id
        assert data["name"] == first_planet["name"]
        assert "moons" in data
    
    def test_get_planet_with_moons(self, client, db_session):
        """Test GET /planets/{id} returns planet with moons list."""
        seed_planets_and_moons(db_session)
        
        # Get Earth (should have 1 moon)
        response = client.get("/planets")
        earth = next((p for p in response.json() if p["name"] == "Earth"), None)
        assert earth is not None
        
        response = client.get(f"/planets/{earth['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Earth"
        assert data["moons"] is not None
        assert len(data["moons"]) == 1
        assert data["moons"][0]["name"] == "Moon"
    
    def test_get_planet_not_found(self, client, db_session):
        """Test GET /planets/{id} returns 404 for non-existent ID."""
        response = client.get("/planets/99999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestPlanetsMoonsEndpoints:
    """Tests for planet moons endpoint."""
    
    def test_get_planet_moons(self, client, db_session):
        """Test GET /planets/{id}/moons endpoint."""
        seed_planets_and_moons(db_session)
        
        # Get Jupiter (should have 9 moons)
        response = client.get("/planets")
        jupiter = next((p for p in response.json() if p["name"] == "Jupiter"), None)
        assert jupiter is not None
        
        response = client.get(f"/planets/{jupiter['id']}/moons")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 9
        
        # Check required fields
        for moon in data:
            assert "name" in moon
            assert "orbital_radius_km" in moon
            assert "radius_km" in moon
    
    def test_get_planet_moons_earth(self, client, db_session):
        """Test GET /planets/{id}/moons for Earth."""
        seed_planets_and_moons(db_session)
        
        # Get Earth (should have 1 moon)
        response = client.get("/planets")
        earth = next((p for p in response.json() if p["name"] == "Earth"), None)
        assert earth is not None
        
        response = client.get(f"/planets/{earth['id']}/moons")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Moon"
    
    def test_get_planet_moons_saturn(self, client, db_session):
        """Test GET /planets/{id}/moons for Saturn."""
        seed_planets_and_moons(db_session)
        
        # Get Saturn (should have 10 moons)
        response = client.get("/planets")
        saturn = next((p for p in response.json() if p["name"] == "Saturn"), None)
        assert saturn is not None
        
        response = client.get(f"/planets/{saturn['id']}/moons")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
    
    def test_get_planet_moons_not_found(self, client, db_session):
        """Test GET /planets/{id}/moons returns 404 for non-existent planet."""
        response = client.get("/planets/99999/moons")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_root_endpoint(self, client):
        """Test GET / endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_health_endpoint(self, client):
        """Test GET /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
