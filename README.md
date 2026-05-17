# 🛰 Space Explorer

An interactive 3D web app that visualises **500 satellites** in real
orbits around Earth plus the **8 planets** of the solar system, their
moons, and a few asteroid trajectories. All bodies are clickable, all
orbits are computed from real-ish Keplerian parameters, and the whole
thing runs from a single Docker command.

![status](https://img.shields.io/badge/status-prototype-yellow)
![tech](https://img.shields.io/badge/three.js-0.160-blue)
![backend](https://img.shields.io/badge/FastAPI-1.0-009688)

## What's inside

```
.
├── backend/                # FastAPI + SQLite + seed script
│   ├── main.py             # API entrypoint, CORS, router mounts
│   ├── database.py         # SQLAlchemy engine — picks DATABASE_URL from env
│   ├── models.py           # ORM models: Satellite, Planet, Moon, Asteroid
│   ├── schemas.py          # Pydantic response schemas
│   ├── seed.py             # Deterministic seeder (500 sats, 8 planets, moons)
│   ├── routers/            # /satellites, /planets, /asteroids, /bodies
│   └── tests/              # pytest suite
├── frontend/
│   └── index.html          # Single-file three.js app — no build step
├── nginx.conf              # Reverse-proxy: /api → backend, / → static
├── docker-compose.yml      # 2 services, single port exposed
└── README.md               # this file
```

## Run it locally (Docker)

```bash
docker compose up -d --build
open http://localhost:5500
```

That's it. One port (`5500`) exposed. nginx serves the static frontend
and reverse-proxies `/api/*` to the backend container — so the app
works from any browser on your LAN by just opening
`http://<your-ip>:5500`.

The first start seeds the SQLite database with 500 satellites, 8
planets, ~35 moons and 10 asteroid close-approach tracks. Data lives in
a Docker volume (`space-explorer_explorer_db`) and persists across
restarts.

To stop and wipe:
```bash
docker compose down -v
```

## Features

- **500 satellites** with realistic orbital params (LEO/MEO/GEO) drawn
  from real-ish constellations (Starlink, OneWeb, GPS, Galileo,
  Intelsat…).
- **True orbital motion**: each satellite has its own RAAN +
  inclination + period and moves along the orbit in real time
  (time-warp: 1× real → 2000× compressed).
- **Pause / play / speed slider** — bottom-left control panel.
- **Show orbits toggle** — 500 orbit lines rendered as a single
  `LineSegments` mesh (1 draw call, no FPS hit).
- **Hover tooltip** with name, type, altitude, country.
- **Click to focus**: camera animates to the body, opens a polished
  detail panel with all fields + parent/siblings chips for one-click
  cross-body navigation.
- **8 planet scenes**: switch with the bottom planet bar; each shows
  the planet's moons orbiting on visible rings.
- **Search + LEO/MEO/GEO filter** on the Earth scene.

## Endpoints

| Method | Path                          | What it returns |
|--------|-------------------------------|-----------------|
| GET    | `/health`                     | `{"status":"ok"}` |
| GET    | `/satellites/?limit=500`      | List of satellites |
| GET    | `/satellites/{id}`            | Single satellite details |
| GET    | `/planets/`                   | All 8 planets |
| GET    | `/planets/{id}`               | Planet + its moons |
| GET    | `/planets/{id}/moons`         | Moons of a planet |
| GET    | `/asteroids/recent?limit=10`  | Recent asteroid close approaches |
| GET    | `/bodies/{kind}/{id}`         | Cross-body parent + siblings |

Swagger UI: `http://localhost:5500/api/docs` (mounted by FastAPI).

## Run the backend bare (no Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m seed         # seeds ./space_data.db
uvicorn main:app --reload
```
Then serve the frontend with any static server and update its
`API_BASE` to point at `http://127.0.0.1:8000`.

## Tests

```bash
cd backend
pip install pytest
pytest -q
```

## Roadmap

- [x] **v0.1** — Local Docker compose stack, 500 animated satellites
- [ ] **v0.2** — Vercel deploy: static frontend + serverless `/api/*`
- [ ] **v0.3** — Real TLE ingestion from CelesTrak instead of fake data
- [ ] **v0.4** — Time scrubber: jump to a specific UTC timestamp
- [ ] **v0.5** — Search the planet scenes too (not just Earth)

## License

MIT — see `LICENSE`.
