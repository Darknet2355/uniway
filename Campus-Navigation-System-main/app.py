"""
KYU Campus Navigation System — app.py
AI powered by Groq (free, fast, no credit card needed)
Routing via OSRM (free, no API key needed)
Keys loaded from .env file so they're never hardcoded
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import requests
import math
import os

# Load .env file first thing
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "kyu-dev-key")

# ─────────────────────────────────────────────────────────────────────────────
#  GROQ API — completely free, no credit card needed
#  Get your key at https://console.groq.com → API Keys → Create API Key
#  Then add to .env:  GROQ_API_KEY=your_key_here
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"

# ─────────────────────────────────────────────────────────────────────────────
#  CAMPUS KNOWLEDGE
# ─────────────────────────────────────────────────────────────────────────────
CAMPUS_CONTEXT = """
You are the official AI assistant for Kyambogo University (KYU) campus in Kampala, Uganda.
Answer ONLY questions about Kyambogo University campus — locations, facilities, directions, student services.
For anything unrelated, politely redirect the user back to campus topics.

CAMPUS KNOWLEDGE:

ENTRANCES:
- Main Gate (Kyambogo Road): primary entrance, 24/7 security, most taxis drop here
- Eastern Gate (Police Post): east side, closest to student hostels
- Western Gate (Faculty of Science): west side, near Engineering and Science

ADMINISTRATION (Mon-Fri 8am-5pm):
- Administration Block (Senate): student IDs, Registrar, Finance Department
- Guild Offices: student government, next to Admin Block

LIBRARIES:
- Central Library (Main): Mon-Sat 8am-8pm, borrow up to 3 books with student ID
- E-Library: computers and internet, right next to Central Library
- Faculty of Engineering Library: inside Engineering building

FACULTIES: Engineering, Science, Arts & Humanities, Vocational Studies (west side)
           Education, Management, Law, Health Sciences, Built Environment (central/east)

DINING:
- Main Cafeteria: central campus, 3 meals/day, busiest 12pm-2pm
- Engineering Canteen and Science Canteen: quieter, near their faculties
- Student Market: east side near hostels, stationery and snacks

BANKING: Stanbic Bank and Centenary Bank — east side near Student Market

MEDICAL:
- University Health Centre: Mon-Fri 8am-5pm
- Dental Clinic and Pharmacy: next to Health Centre
- After-hours emergency: Police Post at Eastern Gate (24/7)
- Nearest hospital: Mulago National Referral Hospital

RELIGIOUS: Chapel (St. Francis) and Mosque — east side, open to all students

STUDENT HOSTELS (east side, near Eastern Gate):
- Girls Hostel Block A and B, Boys Hostel Block C and D
- International Students Hostel nearby. All have 24-hour security

SPORTS (west side): Sports Ground, Basketball/Volleyball/Tennis Courts, University Gym

OTHER: ICT Center, Printing Press (best for final year project printing/binding),
       University Bookshop, Police Post (Eastern Gate, 24/7), University Farm (far west)

NAVIGATION TIPS:
- Campus is walkable end-to-end in about 20 minutes
- Main tarmac road runs from Main Gate through the centre
- Tell your taxi driver "Kyambogo University" — most routes pass the main gate

RESPONSE RULES:
- Be warm, concise, and mobile-friendly
- Use short bullet points for lists
- When your answer points to a specific navigable location, end with:
  [NAVIGATE:ExactLocationName]
  using ONLY these exact names:
  Main Gate (Kyambogo Road), Eastern Gate (Police Post), Western Gate (Faculty of Science),
  Administration Block (Senate), Guild Offices, Registrar's Office, Finance Department,
  Central Library (Main), E-Library, Faculty of Engineering Library,
  Faculty of Engineering, Faculty of Science, Faculty of Arts and Humanities,
  Faculty of Vocational Studies, School of Education, School of Management, School of Law,
  School of Health Sciences, School of Built Environment,
  Girls Hostel (Block A), Girls Hostel (Block B), Boys Hostel (Block C), Boys Hostel (Block D),
  International Students Hostel, Main Cafeteria, Faculty of Engineering Canteen, Science Canteen,
  Student Market, Bank (Stanbic), Bank (Centenary), Main Auditorium (Freedom Square),
  Engineering Lecture Hall, Science Lecture Hall, Arts Lecture Hall,
  Sports Ground (Main), Basketball Court, Volleyball Court, Tennis Court, University Gym,
  University Health Centre, Dental Clinic, Pharmacy,
  ICT Center, Printing Press, University Bookshop, Chapel (St. Francis), Mosque, Police Post, University Farm
""".strip()

# ─────────────────────────────────────────────────────────────────────────────
#  DESTINATIONS & CATEGORIES
# ─────────────────────────────────────────────────────────────────────────────
destinations = {
    "Main Gate (Kyambogo Road)":          [0.34785, 32.63135],
    "Eastern Gate (Police Post)":         [0.34925, 32.63345],
    "Western Gate (Faculty of Science)":  [0.35175, 32.62715],
    "Administration Block (Senate)":      [0.35028, 32.62962],
    "Guild Offices":                      [0.35042, 32.62955],
    "Registrar's Office":                 [0.35015, 32.62930],
    "Finance Department":                 [0.34995, 32.62945],
    "Central Library (Main)":             [0.34971, 32.62848],
    "E-Library":                          [0.34985, 32.62815],
    "Faculty of Engineering Library":     [0.35215, 32.62695],
    "Faculty of Engineering":             [0.35231, 32.62705],
    "Faculty of Science":                 [0.35175, 32.62754],
    "Faculty of Arts and Humanities":     [0.35192, 32.62885],
    "Faculty of Vocational Studies":      [0.35285, 32.62645],
    "School of Education":                [0.34925, 32.63018],
    "School of Management":               [0.35065, 32.62985],
    "School of Law":                      [0.35125, 32.62945],
    "School of Health Sciences":          [0.35315, 32.62685],
    "School of Built Environment":        [0.35255, 32.62735],
    "Girls Hostel (Block A)":             [0.34605, 32.63223],
    "Girls Hostel (Block B)":             [0.34635, 32.63205],
    "Boys Hostel (Block C)":              [0.34558, 32.63075],
    "Boys Hostel (Block D)":              [0.34525, 32.63115],
    "International Students Hostel":      [0.34715, 32.63185],
    "Main Cafeteria":                     [0.35055, 32.62898],
    "Faculty of Engineering Canteen":     [0.35245, 32.62685],
    "Science Canteen":                    [0.35185, 32.62765],
    "Student Market":                     [0.34885, 32.63125],
    "Bank (Stanbic)":                     [0.34845, 32.63105],
    "Bank (Centenary)":                   [0.34865, 32.63085],
    "Main Auditorium (Freedom Square)":   [0.34908, 32.62925],
    "Engineering Lecture Hall":           [0.35225, 32.62725],
    "Science Lecture Hall":               [0.35165, 32.62785],
    "Arts Lecture Hall":                  [0.35195, 32.62865],
    "Sports Ground (Main)":               [0.35358, 32.62488],
    "Basketball Court":                   [0.35315, 32.62525],
    "Volleyball Court":                   [0.35325, 32.62545],
    "Tennis Court":                       [0.35305, 32.62565],
    "University Gym":                     [0.35275, 32.62585],
    "University Health Centre":           [0.35125, 32.63015],
    "Dental Clinic":                      [0.35115, 32.63035],
    "Pharmacy":                           [0.35095, 32.63045],
    "ICT Center":                         [0.35025, 32.62875],
    "Printing Press":                     [0.34955, 32.62985],
    "University Bookshop":                [0.34945, 32.62915],
    "Chapel (St. Francis)":               [0.34825, 32.63055],
    "Mosque":                             [0.34795, 32.63185],
    "Police Post":                        [0.34915, 32.63335],
    "University Farm":                    [0.35425, 32.62515],
}

categories = {
    "Entrances": ["Main Gate (Kyambogo Road)", "Eastern Gate (Police Post)", "Western Gate (Faculty of Science)"],
    "Administration": ["Administration Block (Senate)", "Guild Offices", "Registrar's Office", "Finance Department"],
    "Libraries": ["Central Library (Main)", "E-Library", "Faculty of Engineering Library"],
    "Faculties & Schools": [
        "Faculty of Engineering", "Faculty of Science", "Faculty of Arts and Humanities",
        "Faculty of Vocational Studies", "School of Education", "School of Management",
        "School of Law", "School of Health Sciences", "School of Built Environment",
    ],
    "Student Accommodation": [
        "Girls Hostel (Block A)", "Girls Hostel (Block B)",
        "Boys Hostel (Block C)", "Boys Hostel (Block D)", "International Students Hostel",
    ],
    "Dining & Shopping": [
        "Main Cafeteria", "Faculty of Engineering Canteen", "Science Canteen",
        "Student Market", "Bank (Stanbic)", "Bank (Centenary)",
    ],
    "Auditoriums & Halls": [
        "Main Auditorium (Freedom Square)", "Engineering Lecture Hall",
        "Science Lecture Hall", "Arts Lecture Hall",
    ],
    "Sports & Recreation": ["Sports Ground (Main)", "Basketball Court", "Volleyball Court", "Tennis Court", "University Gym"],
    "Medical": ["University Health Centre", "Dental Clinic", "Pharmacy"],
    "Other Facilities": ["ICT Center", "Printing Press", "University Bookshop", "Chapel (St. Francis)", "Mosque", "Police Post", "University Farm"],
}


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(d_lon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def groq_chat(messages):
    """Call Groq API with full error surfacing."""
    if not GROQ_API_KEY:
        raise Exception(
            "GROQ_API_KEY not set — open your .env file and add: "
            "GROQ_API_KEY=your_key_here  "
            "(Get a free key at https://console.groq.com)"
        )
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": CAMPUS_CONTEXT}, *messages],
        "temperature": 0.7,
        "max_tokens": 800,
    }
    resp = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=20,
    )
    if not resp.ok:
        try:
            err = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            err = resp.text
        raise Exception(f"Groq {resp.status_code}: {err}")
    return resp.json()["choices"][0]["message"]["content"]


def groq_tip(faculty, name, stop):
    prompt = (
        f"You are a friendly senior student at Kyambogo University in Kampala. "
        f"Write ONE short practical tip (2 sentences max, no intro phrase) about "
        f'"{stop}" specifically useful for a {faculty} student named {name}. '
        f"Be specific and accurate to Kyambogo University campus."
    )
    return groq_chat([{"role": "user", "content": prompt}])


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE ROUTES
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("home.html", categories=categories)

@app.route("/result", methods=["GET", "POST"])
def result():
    if request.method == "POST":
        dest_name = request.form.get("destination", "").strip()
        if dest_name not in destinations:
            return "<h1>Invalid destination</h1>", 400
        lat, lon = destinations[dest_name]
    else:
        dest_name = request.args.get("name", "").strip()
        try:
            lat = float(request.args.get("lat", ""))
            lon = float(request.args.get("lon", ""))
        except ValueError:
            if dest_name in destinations:
                lat, lon = destinations[dest_name]
            else:
                return "<h1>Invalid destination</h1>", 400
    return render_template("result.html", destination_name=dest_name, dest_lat=lat, dest_lon=lon)

@app.route("/assistant")
def assistant():
    return render_template("assistant.html")

@app.route("/firstday")
def firstday():
    return render_template("firstday.html")

@app.route("/service-worker.js")
def service_worker():
    resp = send_from_directory(os.path.join(app.root_path, "static"), "service-worker.js")
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


# ─────────────────────────────────────────────────────────────────────────────
#  API ROUTES
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/assistant", methods=["POST"])
def api_assistant():
    data = request.get_json()
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": "No messages provided"}), 400
    try:
        reply = groq_chat(messages)
        return jsonify({"reply": reply})
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out — please try again."}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot reach Groq — check your internet connection."}), 502
    except Exception as e:
        print(f"[/api/assistant ERROR] {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai-tip", methods=["POST"])
def api_ai_tip():
    data    = request.get_json()
    faculty = data.get("faculty", "your faculty")
    name    = data.get("name", "Fresher")
    stop    = data.get("stop", "this location")
    try:
        tip = groq_tip(faculty, name, stop)
        return jsonify({"tip": tip.strip()})
    except Exception as e:
        print(f"[/api/ai-tip ERROR] {e}")
        return jsonify({"tip": ""}), 200


@app.route("/api/destinations")
def api_destinations():
    return jsonify({"destinations": destinations, "categories": categories})


@app.route("/api/route", methods=["POST"])
def api_route():
    data     = request.get_json()
    user_lat = data.get("lat")
    user_lon = data.get("lon")
    dest_lat = data.get("dest_lat")
    dest_lon = data.get("dest_lon")

    if not all([user_lat, user_lon, dest_lat, dest_lon]):
        return jsonify({"error": "Missing coordinates"}), 400

    try:
        osrm_url = (
            f"http://router.project-osrm.org/route/v1/foot/"
            f"{user_lon},{user_lat};{dest_lon},{dest_lat}"
            f"?overview=full&geometries=geojson&steps=true"
        )
        r = requests.get(osrm_url, timeout=8)
        r.raise_for_status()
        osrm = r.json()

        if osrm.get("code") == "Ok" and osrm.get("routes"):
            route        = osrm["routes"][0]
            coords       = route["geometry"]["coordinates"]
            path         = [[lat, lon] for lon, lat in coords]
            distance_km  = round(route["distance"] / 1000, 2)
            duration_min = max(1, round(route["duration"] / 60))
            instructions = []
            for leg in route.get("legs", []):
                for step in leg.get("steps", []):
                    mtype    = step.get("maneuver", {}).get("type", "")
                    modifier = step.get("maneuver", {}).get("modifier", "")
                    dist     = step.get("distance", 0)
                    if dist < 5:
                        continue
                    if mtype == "depart":        text = "Start walking"
                    elif mtype == "arrive":      text = "Arrive at your destination"
                    elif mtype == "turn":        text = f"Turn {modifier}"
                    elif mtype in ("continue", "new name"): text = "Continue straight"
                    elif mtype == "roundabout":  text = f"Take exit {step.get('maneuver',{}).get('exit','')} at the roundabout"
                    else:                        text = mtype.replace("-", " ").capitalize()
                    instructions.append({"text": text, "distance": round(dist, 1), "time": round(step.get("duration", 0) / 60, 1)})
            return jsonify({"success": True, "path": path, "distance_km": distance_km, "duration_min": duration_min, "instructions": instructions, "source": "osrm"})

    except Exception as e:
        print(f"[OSRM ERROR] {e}")

    dist = haversine(user_lat, user_lon, dest_lat, dest_lon)
    return jsonify({
        "success": True,
        "path": [[user_lat, user_lon], [dest_lat, dest_lon]],
        "distance_km": round(dist, 2),
        "duration_min": max(1, round(dist * 15)),
        "instructions": [
            {"text": "Head toward your destination", "distance": round(dist * 1000, 1), "time": round(dist * 15, 1)},
            {"text": "Arrive at your destination", "distance": 0, "time": 0},
        ],
        "source": "direct",
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
