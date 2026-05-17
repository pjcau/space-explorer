"""Generate the static JSON dataset for the GitHub-Pages build.

GitHub Pages can only serve static files — no Python runtime. So we run
the same `seed.py` logic against an in-memory SQLite DB and dump every
endpoint payload to a JSON file under `docs/data/`. The frontend, when
served from a static origin, reads `./data/<name>.json` instead of
calling `/api/<name>`.

Output layout (matches the frontend's path expectations):

    docs/data/satellites.json                 # full list (500 items)
    docs/data/satellites/<id>.json            # one file per sat (for detail panel)
    docs/data/planets.json                    # 8 planets, each with inline moons
    docs/data/planets/<id>.json               # same shape, single planet
    docs/data/planets/<id>/moons.json         # moons list
    docs/data/asteroids/recent.json           # asteroid trajectories
    docs/data/bodies/<kind>/<id>.json         # parent + siblings lookup

Run it from the repo root with no arguments:

    python scripts/build_static.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# Force the SQLAlchemy engine to use a throwaway in-memory DB so we never
# touch any committed `space_data.db`.
import os as _os  # noqa: E402
_os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from backend.database import engine, Base, SessionLocal  # noqa: E402
from backend.models import Satellite, Planet, Moon  # noqa: E402

# Try to import Asteroid; the agent's seed had it in models.py but routers may
# differ across sessions. Optional.
try:
    from backend.models import Asteroid  # type: ignore  # noqa: E402
except Exception:
    Asteroid = None  # type: ignore[assignment]

from backend.seed import seed_satellites, seed_planets_and_moons  # noqa: E402

OUT_DIR = REPO / "docs" / "data"


def _serialise(row, ignore=()):
    out = {}
    for c in row.__table__.columns:
        if c.name in ignore:
            continue
        v = getattr(row, c.name)
        out[c.name] = v
    return out


def _write(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, default=str, ensure_ascii=False, indent=0))


def main() -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_satellites(db)
    seed_planets_and_moons(db)

    # ---- satellites ----
    sats = [_serialise(s) for s in db.query(Satellite).order_by(Satellite.id).all()]
    _write(OUT_DIR / "satellites.json", sats)
    for s in sats:
        _write(OUT_DIR / "satellites" / f"{s['id']}.json", s)

    # ---- planets + moons ----
    planets_raw = db.query(Planet).order_by(Planet.distance_au).all()
    moons_by_planet: dict[int, list[dict]] = {}
    for m in db.query(Moon).order_by(Moon.id).all():
        moons_by_planet.setdefault(m.planet_id, []).append(_serialise(m))

    planets_list = []
    for p in planets_raw:
        d = _serialise(p)
        d["moons"] = moons_by_planet.get(p.id, [])
        planets_list.append(d)
    _write(OUT_DIR / "planets.json", planets_list)
    for p in planets_list:
        _write(OUT_DIR / "planets" / f"{p['id']}.json", p)
        _write(OUT_DIR / "planets" / str(p["id"]) / "moons.json", p["moons"])

    # ---- bodies/{kind}/{id} ----
    # Build the same parent + siblings response the live endpoint produces.
    def body(kind: str, id_: int, name: str, parent: dict | None, siblings: list[dict]) -> dict:
        return {
            "id": id_, "name": name, "type": kind,
            "parent": parent,
            "siblings": siblings[:5],
        }

    earth_id = next((p["id"] for p in planets_list if p["name"].lower() == "earth"), 3)
    mars_id = next((p["id"] for p in planets_list if p["name"].lower() == "mars"), 4)

    # For satellites: parent is the planet they orbit.
    by_orbit = {"Earth": [], "Mars": []}
    for s in sats:
        by_orbit.setdefault(s.get("orbits_planet_id") or "Earth", []).append(s)
    earth_sats = by_orbit.get("Earth", [])
    mars_sats = by_orbit.get("Mars", [])

    for s in sats:
        host_name = s.get("orbits_planet_id") or "Earth"
        parent_id = mars_id if host_name == "Mars" else earth_id
        siblings_pool = mars_sats if host_name == "Mars" else earth_sats
        sibs = [{"id": x["id"], "name": x["name"], "type": "satellite"}
                for x in siblings_pool if x["id"] != s["id"]][:5]
        _write(OUT_DIR / "bodies" / "satellite" / f"{s['id']}.json",
               body("satellite", s["id"], s["name"],
                    {"id": parent_id, "name": host_name, "type": "planet"}, sibs))

    # For planets: parent is the Sun (synthetic), siblings are the other planets.
    sun_parent = {"id": 0, "name": "Sun", "type": "star"}
    for p in planets_list:
        sibs = [{"id": x["id"], "name": x["name"], "type": "planet"}
                for x in planets_list if x["id"] != p["id"]][:5]
        _write(OUT_DIR / "bodies" / "planet" / f"{p['id']}.json",
               body("planet", p["id"], p["name"], sun_parent, sibs))

    # For moons: parent is the planet, siblings are other moons of the same planet.
    for p in planets_list:
        moons = p["moons"]
        for m in moons:
            sibs = [{"id": x["id"], "name": x["name"], "type": "moon"}
                    for x in moons if x["id"] != m["id"]][:5]
            _write(OUT_DIR / "bodies" / "moon" / f"{m['id']}.json",
                   body("moon", m["id"], m["name"],
                        {"id": p["id"], "name": p["name"], "type": "planet"}, sibs))

    # ---- asteroids/recent (best-effort — only if the model + seed exist) ----
    if Asteroid is not None:
        try:
            asts = [_serialise(a) for a in db.query(Asteroid).order_by(Asteroid.id).limit(10).all()]
            _write(OUT_DIR / "asteroids" / "recent.json", asts)
        except Exception:
            pass

    db.close()
    n = sum(1 for _ in OUT_DIR.rglob("*.json"))
    print(f"wrote {n} JSON files to {OUT_DIR.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
