"""Smoke test for bodies endpoint."""
import sys
import os

# Add packages directory to path
packages_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "packages")
sys.path.insert(0, packages_path)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import engine, Base, SessionLocal
from backend.seed import seed_satellites, seed_planets_and_moons

# Create test database tables
Base.metadata.create_all(bind=engine)

# Seed test data
db = SessionLocal()
seed_satellites(db)
seed_planets_and_moons(db)
db.close()

client = TestClient(app)

# Test 1: Get planet
print('Test 1: GET /bodies/planet/3')
response = client.get('/bodies/planet/3')
print(f'Status: {response.status_code}')
print(f'Response: {response.json()}')
assert response.status_code == 200
data = response.json()
assert data['name'] == 'Earth'
assert data['parent'] is None
assert len(data['siblings']) > 0
print('PASSED')

# Test 2: Get moon
print('\nTest 2: GET /bodies/moon/1')
response = client.get('/bodies/moon/1')
print(f'Status: {response.status_code}')
print(f'Response: {response.json()}')
assert response.status_code == 200
data = response.json()
assert data['name'] == 'Moon'
assert data['parent'] is not None
assert data['parent']['name'] == 'Earth'
print('PASSED')

# Test 3: Get satellite orbiting Mars
print('\nTest 3: GET /bodies/satellite/11')
response = client.get('/bodies/satellite/11')
print(f'Status: {response.status_code}')
print(f'Response: {response.json()}')
assert response.status_code == 200
data = response.json()
assert data['type'] == 'satellite'
assert data['parent'] is not None
assert data['parent']['name'] == 'Mars'
assert len(data['siblings']) > 0
print('PASSED')

# Cleanup
Base.metadata.drop_all(bind=engine)
print('\nAll smoke tests passed!')
