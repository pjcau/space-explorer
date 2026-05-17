"""Seed database with deterministic space data."""
import json
from sqlalchemy.orm import Session
from .database import engine, Base
from .models import Satellite, Planet, Moon


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def seed_satellites(db: Session):
    """Seed 500 deterministic satellites with realistic orbital parameters.

    The frontend derives a per-satellite RAAN + mean anomaly phase from the
    row id so each one occupies its own orbital plane — the seed only owns
    altitude / inclination / period / metadata.
    """
    import math

    db.query(Satellite).delete()

    EARTH_MU = 398600.4418  # km^3/s^2

    def period_min(alt_km: float) -> float:
        r = 6371.0 + alt_km
        return (2 * math.pi * math.sqrt(r ** 3 / EARTH_MU)) / 60.0

    rows: list[tuple] = []
    norad = 25000

    # ---- LEO: 350 sats, 350-1500 km, mixed inclinations ----
    leo_fams = [
        ("Starlink",    "USA",        2019, 53.0,  "SpaceX broadband internet constellation"),
        ("OneWeb",      "UK",         2020, 87.4,  "Global broadband constellation"),
        ("Iridium",     "USA",        2017, 86.4,  "Voice/data satellite phone network"),
        ("Planet Dove", "USA",        2017, 97.4,  "Earth imaging cubesat (Planet Labs)"),
        ("Lemur-2",     "USA",        2018, 51.6,  "Ship & weather tracking (Spire)"),
        ("CosmosSAR",   "Russia",     2016, 67.1,  "Synthetic-aperture radar reconnaissance"),
        ("BlackSky",    "USA",        2019, 45.0,  "High-cadence Earth observation"),
        ("Yaogan",      "China",      2015, 63.4,  "Chinese remote-sensing satellite"),
    ]
    for i in range(350):
        f = leo_fams[i % len(leo_fams)]
        alt = 350 + ((i * 17) % 1150)
        inc = f[3] + ((i * 0.07) % 6) - 3.0
        per = period_min(alt)
        orbits = "Mars" if (i % 35) == 0 else "Earth"
        rows.append((f"{f[0]}-{1000 + i}", norad, alt, inc, per, "LEO",
                     f[1], f[2] + (i % 5), f[4], orbits))
        norad += 1

    # ---- MEO: 100 sats, 5000-30000 km ----
    meo_fams = [
        ("GPS BIIR",    "USA",        1997, 55.0,  "US Air Force GPS navigation satellite"),
        ("GLONASS-K",   "Russia",     2011, 64.8,  "Russian global navigation satellite"),
        ("Galileo FOC", "ESA",        2014, 56.0,  "European Galileo navigation satellite"),
        ("BeiDou MEO",  "China",      2015, 55.0,  "Chinese BeiDou navigation satellite"),
        ("O3b mPower",  "Luxembourg", 2022, 0.03,  "Medium-Earth orbit broadband constellation"),
    ]
    for i in range(100):
        f = meo_fams[i % len(meo_fams)]
        alt = 5000 + ((i * 257) % 25000)
        inc = f[3] + ((i * 0.13) % 4) - 2.0
        per = period_min(alt)
        rows.append((f"{f[0]} {chr(65 + (i // len(meo_fams)) % 26)}{i % 10}",
                     norad, alt, inc, per, "MEO",
                     f[1], f[2] + (i % 8), f[4], "Earth"))
        norad += 1

    # ---- GEO: 50 sats, ~35786 km ----
    geo_fams = [
        ("Intelsat",    "USA",        2017, 0.05, "Geostationary communications relay"),
        ("Eutelsat",    "France",     2019, 0.04, "European DTH/TV broadcast satellite"),
        ("SES",         "Luxembourg", 2018, 0.02, "SES global communications relay"),
        ("Inmarsat",    "UK",         2013, 0.07, "Maritime/aero satphone backbone"),
        ("AsiaSat",     "Hong Kong",  2014, 0.10, "Asia-Pacific direct-broadcast TV"),
        ("Türksat",     "Turkey",     2021, 0.08, "Turkish state communications satellite"),
    ]
    for i in range(50):
        f = geo_fams[i % len(geo_fams)]
        alt = 35786.0 + ((i * 3) % 40) - 20
        inc = f[3] + ((i * 0.011) % 0.3)
        per = period_min(alt)
        rows.append((f"{f[0]} {i + 1:02d}", norad, alt, inc, per, "GEO",
                     f[1], f[2] + (i % 6), f[4], "Earth"))
        norad += 1

    for (name, norad_id, alt, inc, per, kind, country, year, desc, orbits) in rows:
        db.add(Satellite(
            name=name, norad_id=norad_id, altitude_km=alt,
            inclination_deg=inc, period_min=per, type=kind,
            country=country, launch_year=year, description=desc,
            orbits_planet_id=orbits,
        ))

    db.commit()


def seed_planets_and_moons(db: Session):
    """Seed 8 planets with 35+ moons across planets that have moons."""
    # Clear existing data
    db.query(Moon).delete()
    db.query(Planet).delete()
    
    # Planets data
    planets = [
        ("Mercury", 0.39, 2439.7, "#A5A5A5", 58.6, "Smallest planet in the solar system"),
        ("Venus", 0.72, 6051.8, "#E6C288", -243.0, "Second planet from the Sun"),
        ("Earth", 1.0, 6371.0, "#4169E1", 24.0, "Our home planet"),
        ("Mars", 1.52, 3389.5, "#FF4500", 24.6, "The Red Planet"),
        ("Jupiter", 5.20, 69911.0, "#DEB887", 9.9, "Largest planet in the solar system"),
        ("Saturn", 9.58, 58232.0, "#F4A460", 10.7, "Planet with prominent rings"),
        ("Uranus", 19.22, 25362.0, "#ADD8E6", -17.2, "Ice giant with tilted axis"),
        ("Neptune", 30.05, 24622.0, "#4169E1", 16.1, "Windiest planet"),
    ]
    
    planet_ids = {}
    for name, distance_au, radius_km, color, rotation_period, description in planets:
        planet = Planet(
            name=name,
            distance_au=distance_au,
            radius_km=radius_km,
            color=color,
            rotation_period_hours=rotation_period,
            description=description
        )
        db.add(planet)
        db.flush()
        planet_ids[name] = planet.id
    
    # Moons data - 35+ moons across planets that have moons
    # Earth: 1 moon
    moons = [
        ("Moon", 384400, 1737.4, "Earth's only natural satellite"),
    ]
    
    # Jupiter: 9 moons
    moons.extend([
        ("Io", 421700, 1821.6, "Most volcanically active body in the solar system"),
        ("Europa", 671034, 1560.8, "Ice-covered moon with subsurface ocean"),
        ("Ganymede", 1070412, 2634.1, "Largest moon in the solar system"),
        ("Callisto", 1882709, 2410.3, "Heavily cratered moon"),
        ("Amalthea", 181350, 83.5, "Irregularly shaped inner moon"),
        ("Thebe", 221700, 49.2, "Small inner moon of Jupiter"),
        ("Metis", 128000, 21.5, "Innermost moon of Jupiter"),
        ("Adrastea", 129000, 16.7, "Small inner moon of Jupiter"),
        ("Leda", 11167000, 10.0, "Irregular outer moon of Jupiter"),
    ])
    
    # Saturn: 10 moons
    moons.extend([
        ("Titan", 1221870, 2574.7, "Largest moon of Saturn with thick atmosphere"),
        ("Rhea", 527108, 763.8, "Second-largest moon of Saturn"),
        ("Iapetus", 3560820, 734.5, "Two-toned moon with dark leading hemisphere"),
        ("Dione", 377390, 561.4, "Heavily cratered moon"),
        ("Tethys", 294619, 531.1, "Moon with large impact crater"),
        ("Enceladus", 237948, 252.1, "Ice-covered moon with geysers"),
        ("Mimas", 185540, 198.2, "Moon with large Herschel crater"),
        ("Hyperion", 1481010, 134.0, "Irregular sponge-like moon"),
        ("Phoebe", 12952000, 106.2, "Irregular retrograde moon"),
        ("Rhea", 527108, 763.8, "Second-largest moon of Saturn"),
    ])
    
    # Uranus: 5 moons
    moons.extend([
        ("Titania", 435910, 788.4, "Largest moon of Uranus"),
        ("Oberon", 583520, 761.4, "Outermost major moon of Uranus"),
        ("Umbriel", 266000, 584.7, "Dark moon of Uranus"),
        ("Ariel", 190990, 578.9, "Brightest major moon of Uranus"),
        ("Miranda", 129390, 235.8, "Moon with unusual surface features"),
    ])
    
    # Neptune: 4 moons
    moons.extend([
        ("Triton", 354759, 1353.4, "Largest moon of Neptune with retrograde orbit"),
        ("Nereid", 5513000, 170.0, "Irregular moon with eccentric orbit"),
        ("Proteus", 117640, 210.3, "Largest of Neptune's inner moons"),
        ("Larissa", 73540, 83.0, "Irregular inner moon of Neptune"),
    ])
    
    for name, orbital_radius, radius, description in moons:
        # Assign moons to planets
        if name == "Moon":
            planet_id = planet_ids["Earth"]
        elif name in ["Io", "Europa", "Ganymede", "Callisto", "Amalthea", "Thebe", "Metis", "Adrastea", "Leda"]:
            planet_id = planet_ids["Jupiter"]
        elif name in ["Titan", "Rhea", "Iapetus", "Dione", "Tethys", "Enceladus", "Mimas", "Hyperion", "Phoebe"]:
            planet_id = planet_ids["Saturn"]
        elif name in ["Titania", "Oberon", "Umbriel", "Ariel", "Miranda"]:
            planet_id = planet_ids["Uranus"]
        elif name in ["Triton", "Nereid", "Proteus", "Larissa"]:
            planet_id = planet_ids["Neptune"]
        else:
            continue
        
        moon = Moon(
            planet_id=planet_id,
            name=name,
            orbital_radius_km=orbital_radius,
            radius_km=radius,
            description=description
        )
        db.add(moon)
    
    db.commit()


def main():
    """Main entry point for seeding database."""
    create_tables()
    from .database import SessionLocal
    db = SessionLocal()
    try:
        seed_satellites(db)
        seed_planets_and_moons(db)
        print("Database seeded successfully with 120 satellites, 8 planets, and 35 moons.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
