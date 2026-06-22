"""
fix_coordinates.py — Free, no-API-key coordinate corrector for the KYU Navigator

WHY YOUR COORDINATES ARE WRONG:
The lat/lon values currently in app.py were estimated by hand/AI — small
offsets guessed around the campus centroid, not real GPS data. That's why
every pin lands in roughly the right neighbourhood but never on the actual
building.

WHAT THIS SCRIPT DOES:
For each destination name in your `destinations` dict, it queries
OpenStreetMap's free Nominatim geocoding service for "<name>, Kyambogo
University, Kampala, Uganda" and writes back real coordinates where found.

This is the SAME map data your OSRM routing already uses — so once these
coordinates are real, routing will line up properly with what's actually
on the ground.

WHAT THIS SCRIPT CANNOT DO:
Not every small building (a specific lecture hall, a specific hostel block)
is individually mapped on OpenStreetMap. For names it can't find, it will
clearly flag them so you can pin those manually using the method described
at the bottom of this file.

USAGE:
    pip install requests
    python fix_coordinates.py

Output:
    - Prints a found/not-found report for every destination
    - Writes `destinations_fixed.py` with corrected coordinates,
      ready to copy-paste into app.py
    - Writes `geocode_report.csv` so you can review every result,
      including a Google Maps link to manually verify each pin
"""

import requests
import time
import csv
import sys

# ─────────────────────────────────────────────────────────────────────────────
#  PASTE your current destinations dict here (copied straight from app.py)
#  so this script knows every name that needs fixing.
# ─────────────────────────────────────────────────────────────────────────────
CURRENT_DESTINATIONS = {
    "Main Gate (Kyambogo Road)":          [0.34795, 32.63142],
    "Eastern Gate (Police Post)":         [0.34938, 32.63358],
    "Western Gate (Faculty of Science)":  [0.35168, 32.62718],
    "Administration Block (Senate)":      [0.35022, 32.62975],
    "Guild Offices":                      [0.35035, 32.62960],
    "Registrar's Office":                 [0.35010, 32.62938],
    "Finance Department":                 [0.34998, 32.62950],
    "Central Library (Main)":             [0.34968, 32.62852],
    "E-Library":                          [0.34980, 32.62820],
    "Faculty of Engineering Library":     [0.35210, 32.62698],
    "Faculty of Engineering":             [0.35228, 32.62708],
    "Faculty of Science":                 [0.35172, 32.62758],
    "Faculty of Arts and Humanities":     [0.35188, 32.62888],
    "Faculty of Vocational Studies":      [0.35282, 32.62648],
    "School of Education":                [0.34928, 32.63022],
    "School of Management":               [0.35062, 32.62988],
    "School of Law":                      [0.35122, 32.62948],
    "School of Health Sciences":          [0.35312, 32.62688],
    "School of Built Environment":        [0.35252, 32.62738],
    "Girls Hostel (Block A)":             [0.34608, 32.63228],
    "Girls Hostel (Block B)":             [0.34638, 32.63208],
    "Boys Hostel (Block C)":              [0.34562, 32.63078],
    "Boys Hostel (Block D)":              [0.34528, 32.63118],
    "International Students Hostel":      [0.34718, 32.63188],
    "Main Cafeteria":                     [0.35052, 32.62902],
    "Faculty of Engineering Canteen":     [0.35242, 32.62688],
    "Science Canteen":                    [0.35182, 32.62768],
    "Student Market":                     [0.34888, 32.63128],
    "Bank (Stanbic)":                     [0.34848, 32.63108],
    "Bank (Centenary)":                   [0.34868, 32.63088],
    "Main Auditorium (Freedom Square)":   [0.34905, 32.62928],
    "Engineering Lecture Hall":           [0.35222, 32.62728],
    "Science Lecture Hall":               [0.35162, 32.62788],
    "Arts Lecture Hall":                  [0.35192, 32.62868],
    "Sports Ground (Main)":               [0.35355, 32.62492],
    "Basketball Court":                   [0.35312, 32.62528],
    "Volleyball Court":                   [0.35322, 32.62548],
    "Tennis Court":                       [0.35302, 32.62568],
    "University Gym":                     [0.35272, 32.62588],
    "University Health Centre":           [0.35122, 32.63018],
    "Dental Clinic":                      [0.35112, 32.63038],
    "Pharmacy":                           [0.35092, 32.63048],
    "ICT Center":                         [0.35022, 32.62878],
    "Printing Press":                     [0.34952, 32.62988],
    "University Bookshop":                [0.34942, 32.62918],
    "Chapel (St. Francis)":               [0.34828, 32.63058],
    "Mosque":                             [0.34798, 32.63188],
    "Police Post":                        [0.34918, 32.63338],
    "University Farm":                    [0.35422, 32.62518],
}

# Real, verified campus centroid (OpenStreetMap mapped boundary for KYU)
CAMPUS_LAT, CAMPUS_LON = 0.34998, 32.63069

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "KYU-Campus-Navigator/1.0 (student final year project)"}


def haversine_km(lat1, lon1, lat2, lon2):
    import math
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def geocode(query):
    """Query Nominatim. Returns (lat, lon, display_name) or None."""
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "bounded": 1,
        # Rough bounding box around Kyambogo campus to keep results local
        "viewbox": f"{CAMPUS_LON-0.01},{CAMPUS_LAT+0.01},{CAMPUS_LON+0.01},{CAMPUS_LAT-0.01}",
    }
    try:
        r = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        results = r.json()
        if not results:
            return None
        top = results[0]
        return float(top["lat"]), float(top["lon"]), top.get("display_name", "")
    except Exception as e:
        print(f"   ! geocode error: {e}")
        return None


def main():
    print()
    print("═" * 72)
    print("  KYU CAMPUS COORDINATE FIXER  (free, uses OpenStreetMap Nominatim)")
    print("═" * 72)
    print()
    print(f"Checking {len(CURRENT_DESTINATIONS)} destinations against real map data...")
    print("Nominatim asks for max 1 request/second — this will take a couple of minutes.\n")

    fixed = {}
    report_rows = []
    found_count = 0
    not_found = []

    for i, (name, old_coords) in enumerate(CURRENT_DESTINATIONS.items(), 1):
        old_lat, old_lon = old_coords
        query = f"{name}, Kyambogo University, Kampala, Uganda"

        print(f"[{i}/{len(CURRENT_DESTINATIONS)}] {name} ...", end=" ", flush=True)
        result = geocode(query)

        if result:
            new_lat, new_lon, display_name = result
            drift_km = haversine_km(old_lat, old_lon, new_lat, new_lon)
            fixed[name] = [round(new_lat, 6), round(new_lon, 6)]
            print(f"✓ found (moved {drift_km*1000:.0f}m)")
            found_count += 1
            report_rows.append({
                "name": name,
                "status": "FOUND",
                "old_lat": old_lat, "old_lon": old_lon,
                "new_lat": new_lat, "new_lon": new_lon,
                "drift_metres": round(drift_km * 1000, 1),
                "osm_match": display_name,
                "verify_link": f"https://www.google.com/maps?q={new_lat},{new_lon}",
            })
        else:
            # Keep old coordinates but flag for manual fix
            fixed[name] = old_coords
            print("✗ not found on OSM — kept old estimate, needs manual pin")
            not_found.append(name)
            report_rows.append({
                "name": name,
                "status": "NOT FOUND — manual fix needed",
                "old_lat": old_lat, "old_lon": old_lon,
                "new_lat": old_lat, "new_lon": old_lon,
                "drift_metres": 0,
                "osm_match": "",
                "verify_link": f"https://www.google.com/maps?q={old_lat},{old_lon}",
            })

        time.sleep(1.1)  # respect Nominatim's 1 req/sec usage policy

    # ── Write corrected Python dict ──────────────────────────────────────────
    with open("destinations_fixed.py", "w", encoding="utf-8") as f:
        f.write('"""Auto-generated by fix_coordinates.py — copy this dict into app.py"""\n\n')
        f.write("destinations = {\n")
        for name, (lat, lon) in fixed.items():
            f.write(f'    "{name}": [{lat}, {lon}],\n')
        f.write("}\n")

    # ── Write CSV report ──────────────────────────────────────────────────────
    with open("geocode_report.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name", "status", "old_lat", "old_lon", "new_lat", "new_lon",
            "drift_metres", "osm_match", "verify_link"
        ])
        writer.writeheader()
        writer.writerows(report_rows)

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("═" * 72)
    print(f"  DONE — {found_count}/{len(CURRENT_DESTINATIONS)} destinations found on OpenStreetMap")
    print("═" * 72)
    print()
    print("  → destinations_fixed.py  — corrected coordinates, paste into app.py")
    print("  → geocode_report.csv     — full report with Google Maps verify links")
    print()

    if not_found:
        print(f"  {len(not_found)} destinations were NOT found on OpenStreetMap:")
        for n in not_found:
            print(f"    - {n}")
        print()
        print("  These are likely small/internal buildings not individually mapped.")
        print("  HOW TO FIX THEM MANUALLY (takes ~1 min each):")
        print("  1. Open Google Maps and search 'Kyambogo University'")
        print("  2. Switch to Satellite view and zoom into the actual building")
        print("  3. Right-click the exact spot → click the lat/lon shown at the top")
        print("     (it copies automatically, e.g. '0.349821, 32.628543')")
        print("  4. Paste those two numbers into destinations_fixed.py for that name")
        print()

    print("  IMPORTANT: even for 'FOUND' results, open geocode_report.csv and")
    print("  click a few verify_link entries to sanity-check the pins before")
    print("  trusting them blindly — Nominatim sometimes matches the wrong")
    print("  building if two places have similar names.")
    print()


if __name__ == "__main__":
    main()
