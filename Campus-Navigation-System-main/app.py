from flask import Flask, render_template, request, jsonify
import requests
import math
import os

app = Flask(__name__)

# ─── Destination Coordinates (verified against OpenStreetMap) ───────────────
# All coordinates are [latitude, longitude]
destinations = {
    # Entrances
    "Main Gate (Kyambogo Road)":         [0.34795, 32.63142],
    "Eastern Gate (Police Post)":        [0.34938, 32.63358],
    "Western Gate (Faculty of Science)": [0.35168, 32.62718],

    # Administration
    "Administration Block (Senate)":     [0.35022, 32.62975],
    "Guild Offices":                     [0.35035, 32.62960],
    "Registrar's Office":               [0.35010, 32.62938],
    "Finance Department":               [0.34998, 32.62950],

    # Libraries
    "Central Library (Main)":           [0.34968, 32.62852],
    "E-Library":                        [0.34980, 32.62820],
    "Faculty of Engineering Library":   [0.35210, 32.62698],

    # Faculties & Schools
    "Faculty of Engineering":           [0.35228, 32.62708],
    "Faculty of Science":               [0.35172, 32.62758],
    "Faculty of Arts and Humanities":   [0.35188, 32.62888],
    "Faculty of Vocational Studies":    [0.35282, 32.62648],
    "School of Education":              [0.34928, 32.63022],
    "School of Management":             [0.35062, 32.62988],
    "School of Law":                    [0.35122, 32.62948],
    "School of Health Sciences":        [0.35312, 32.62688],
    "School of Built Environment":      [0.35252, 32.62738],

    # Student Accommodation
    "Girls Hostel (Block A)":           [0.34608, 32.63228],
    "Girls Hostel (Block B)":           [0.34638, 32.63208],
    "Boys Hostel (Block C)":            [0.34562, 32.63078],
    "Boys Hostel (Block D)":            [0.34528, 32.63118],
    "International Students Hostel":    [0.34718, 32.63188],

    # Dining & Shopping
    "Main Cafeteria":                   [0.35052, 32.62902],
    "Faculty of Engineering Canteen":   [0.35242, 32.62688],
    "Science Canteen":                  [0.35182, 32.62768],
    "Student Market":                   [0.34888, 32.63128],
    "Bank (Stanbic)":                   [0.34848, 32.63108],
    "Bank (Centenary)":                 [0.34868, 32.63088],

    # Auditoriums & Halls
    "Main Auditorium (Freedom Square)": [0.34905, 32.62928],
    "Engineering Lecture Hall":         [0.35222, 32.62728],
    "Science Lecture Hall":             [0.35162, 32.62788],
    "Arts Lecture Hall":                [0.35192, 32.62868],

    # Sports & Recreation
    "Sports Ground (Main)":             [0.35355, 32.62492],
    "Basketball Court":                 [0.35312, 32.62528],
    "Volleyball Court":                 [0.35322, 32.62548],
    "Tennis Court":                     [0.35302, 32.62568],
    "University Gym":                   [0.35272, 32.62588],

    # Medical
    "University Health Centre":         [0.35122, 32.63018],
    "Dental Clinic":                    [0.35112, 32.63038],
    "Pharmacy":                         [0.35092, 32.63048],

    # Other Facilities
    "ICT Center":                       [0.35022, 32.62878],
    "Printing Press":                   [0.34952, 32.62988],
    "University Bookshop":              [0.34942, 32.62918],
    "Chapel (St. Francis)":             [0.34828, 32.63058],
    "Mosque":                           [0.34798, 32.63188],
    "Police Post":                      [0.34918, 32.63338],
    "University Farm":                  [0.35422, 32.62518],
}

categories = {
    "Entrances": [
        "Main Gate (Kyambogo Road)",
        "Eastern Gate (Police Post)",
        "Western Gate (Faculty of Science)",
    ],
    "Administration": [
        "Administration Block (Senate)",
        "Guild Offices",
        "Registrar's Office",
        "Finance Department",
    ],
    "Libraries": [
        "Central Library (Main)",
        "E-Library",
        "Faculty of Engineering Library",
    ],
    "Faculties & Schools": [
        "Faculty of Engineering",
        "Faculty of Science",
        "Faculty of Arts and Humanities",
        "Faculty of Vocational Studies",
        "School of Education",
        "School of Management",
        "School of Law",
        "School of Health Sciences",
        "School of Built Environment",
    ],
    "Student Accommodation": [
        "Girls Hostel (Block A)",
        "Girls Hostel (Block B)",
        "Boys Hostel (Block C)",
        "Boys Hostel (Block D)",
        "International Students Hostel",
    ],
    "Dining & Shopping": [
        "Main Cafeteria",
        "Faculty of Engineering Canteen",
        "Science Canteen",
        "Student Market",
        "Bank (Stanbic)",
        "Bank (Centenary)",
    ],
    "Auditoriums & Halls": [
        "Main Auditorium (Freedom Square)",
        "Engineering Lecture Hall",
        "Science Lecture Hall",
        "Arts Lecture Hall",
    ],
    "Sports & Recreation": [
        "Sports Ground (Main)",
        "Basketball Court",
        "Volleyball Court",
        "Tennis Court",
        "University Gym",
    ],
    "Medical": [
        "University Health Centre",
        "Dental Clinic",
        "Pharmacy",
    ],
    "Other Facilities": [
        "ICT Center",
        "Printing Press",
        "University Bookshop",
        "Chapel (St. Francis)",
        "Mosque",
        "Police Post",
        "University Farm",
    ],
}


# ─── Haversine distance helper ────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(d_lon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
def home():
    return render_template("home.html", categories=categories)


@app.route("/result", methods=["POST"])
def result():
    dest_name = request.form.get("destination", "").strip()
    if dest_name not in destinations:
        return "<h1>Invalid destination</h1>", 400
    lat, lon = destinations[dest_name]
    return render_template(
        "result.html",
        destination_name=dest_name,
        dest_lat=lat,
        dest_lon=lon,
    )


@app.route("/api/route", methods=["POST"])
def api_route():
    data = request.get_json()
    user_lat = data.get("lat")
    user_lon = data.get("lon")
    dest_lat = data.get("dest_lat")
    dest_lon = data.get("dest_lon")

    if not all([user_lat, user_lon, dest_lat, dest_lon]):
        return jsonify({"error": "Missing coordinates"}), 400

    # ── 1) Try OSRM public API (walking profile) ────────────────────────────
    try:
        osrm_url = (
            f"http://router.project-osrm.org/route/v1/foot/"
            f"{user_lon},{user_lat};{dest_lon},{dest_lat}"
            f"?overview=full&geometries=geojson&steps=true&annotations=false"
        )
        r = requests.get(osrm_url, timeout=8)
        r.raise_for_status()
        osrm = r.json()

        if osrm.get("code") == "Ok" and osrm.get("routes"):
            route = osrm["routes"][0]
            coords = route["geometry"]["coordinates"]  # [lon, lat] pairs
            path = [[lat, lon] for lon, lat in coords]

            distance_km = round(route["distance"] / 1000, 2)
            duration_min = max(1, round(route["duration"] / 60))

            # Build step-by-step instructions from OSRM legs/steps
            instructions = []
            for leg in route.get("legs", []):
                for step in leg.get("steps", []):
                    maneuver = step.get("maneuver", {})
                    mtype = maneuver.get("type", "")
                    modifier = maneuver.get("modifier", "")

                    if mtype == "depart":
                        text = "Start walking"
                    elif mtype == "arrive":
                        text = f"Arrive at your destination"
                    elif mtype == "turn":
                        text = f"Turn {modifier}"
                    elif mtype == "continue":
                        text = "Continue straight"
                    elif mtype == "roundabout":
                        exit_n = step.get("maneuver", {}).get("exit", "")
                        text = f"Take exit {exit_n} at the roundabout"
                    else:
                        text = mtype.replace("-", " ").capitalize()

                    dist = step.get("distance", 0)
                    if dist > 5:   # skip trivial micro-steps
                        instructions.append({
                            "text": text,
                            "distance": round(dist, 1),
                            "time": round(step.get("duration", 0) / 60, 1),
                        })

            return jsonify({
                "success": True,
                "path": path,
                "distance_km": distance_km,
                "duration_min": duration_min,
                "instructions": instructions,
                "source": "osrm",
            })

    except Exception as e:
        print(f"OSRM failed: {e}")

    # ── 2) Fallback: straight-line with Haversine distance ──────────────────
    dist = haversine(user_lat, user_lon, dest_lat, dest_lon)
    return jsonify({
        "success": True,
        "path": [[user_lat, user_lon], [dest_lat, dest_lon]],
        "distance_km": round(dist, 2),
        "duration_min": max(1, round(dist * 15)),   # ~4 km/h walking
        "instructions": [
            {"text": "Head toward your destination", "distance": round(dist * 1000, 1), "time": round(dist * 15, 1)},
            {"text": "Arrive at your destination", "distance": 0, "time": 0},
        ],
        "source": "direct",
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
