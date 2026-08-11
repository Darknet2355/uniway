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
import json
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
#  ADMIN PANEL
#  Password is stored in .env — set ADMIN_PASSWORD=yourpassword
#  On Render/deployment: add ADMIN_PASSWORD in Environment Variables dashboard
# ─────────────────────────────────────────────────────────────────────────────
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "kyu@admin2025")

# Announcements are stored in a JSON file so they survive server restarts.
# The file is created automatically on first use.
ANNOUNCEMENTS_FILE = os.path.join(os.path.dirname(__file__), "announcements.json")

def load_announcements():
    if os.path.exists(ANNOUNCEMENTS_FILE):
        try:
            with open(ANNOUNCEMENTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_announcements(data):
    with open(ANNOUNCEMENTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─────────────────────────────────────────────────────────────────────────────
#  CAMPUS KNOWLEDGE
# ─────────────────────────────────────────────────────────────────────────────
CAMPUS_CONTEXT = """
You are the official AI campus assistant for Kyambogo University (KYU), Kampala, Uganda.
Answer ONLY questions about Kyambogo University campus — locations, facilities, directions, student services, academic units, and general campus life.
For anything unrelated, politely redirect the user back to campus topics.

OFFICIAL UNIVERSITY CONTACTS (use these when users need more information):
- Official website: https://www.kyu.ac.ug
- Academic Registrar email: arkyu@kyu.ac.ug
- Academic Registrar telephone: +256-414-285037 / +256-414-287343 / +256-414-287502
- Vice-Chancellor email: vckyu@kyu.ac.ug | Tel: +256-414-286238
- University Secretary email: uskyu@kyu.ac.ug
- Public Relations email: prokyu@kyu.ac.ug | Tel: +256-414-287354
- Postal address: P.O. Box 1, Kyambogo, Kampala – Uganda
- Working hours (Administration): Monday–Friday 8:00am–5:00pm
- Academic/Teaching hours: Monday–Friday 8:00am–9:00pm; Saturday 8:00am–2:00pm

CAMPUS LOCATION & ACCESS:
- Located on Kyambogo Hill, approximately 8 km east of Kampala city centre along the Kampala–Jinja highway.
- Accessible via Banda Trading Centre, Kyambogo “T” Junction, and Ntinda–Kiwatule Road.
- Campus is walkable end-to-end in about 20–25 minutes.
- Main tarmac road runs through the centre of campus.

ENTRANCES:
- Main Gate (Kyambogo Road) — primary entrance, 24/7 security, most taxis drop here
- Eastern Gate (Banda Gate) — east side, closest to student halls and east-end facilities
- Western Gate (Kabaka’s Gate) — west side

ADMINISTRATION (Mon–Fri 8am–5pm):
- Administration Block (Senate) — student IDs, Registrar, Finance Department
- Guild Offices — student government, next to Administration Block
- Registrar’s Office and Finance Department are inside the Administration Block

LIBRARIES:
- Central Library (Main) — modern main library
- E-Library / Computer facilities next to or within library complexes
- Faculty libraries exist inside several faculties (Engineering, Education, Special Needs, etc.)

FACULTIES & SCHOOLS:
- Faculty of Engineering
- Faculty of Science
- Faculty of Arts and Humanities
- Faculty of Social Sciences
- Faculty of Agriculture
- Faculty of Special Needs and Rehabilitation
- School of Education
- School of Management and Entrepreneurship
- School of Computing and Information Science
- School of Built Environment
- School of Vocational Studies
- School of Art and Industrial Design
- Institute of Distance Education, E-Learning and Learning Centres

DINING:
- Main Cafeteria (central campus) — busiest 12pm–2pm
- Faculty/Engineering and Science canteens — quieter options near their faculties
- Student Market (east side near hostels) — stationery, snacks, small shops

BANKING:
- Stanbic Bank and Centenary Bank outlets — east side near Student Market

MEDICAL:
- University Health Centre / Medical Clinic — Mon–Fri 8am–5pm
- After-hours emergency: Police Post at Eastern Gate (24/7)

RELIGIOUS:
- Kakumba Chapel (St. Francis) and Mosque — east side, open to all students

STUDENT HALLS OF RESIDENCE (mainly east side, near Eastern Gate):
- Nanziri Hall
- Mandela Hall
- Kulubya Hall
- Pearl Hall
- North Hall
(Note: On-campus halls accommodate only a small percentage of students; most live in private hostels around Banda, Kireka, Kyambogo and Kiwatule.)

SPORTS & RECREATION (west / central areas):
- Sports Ground (Main)
- Basketball Court, Volleyball Court, Tennis Court
- University Gym

OTHER IMPORTANT PLACES:
- ICT Centre / Computer Centre
- Main Auditorium (Freedom Square area)
- Engineering Lecture Hall / Science Lecture Hall / Arts Lecture Hall areas
- Printing Press (popular for final-year project printing and binding)
- Police Post (Eastern Gate, 24/7)
- University Farm (far west)

NAVIGATION TIPS:
- Tell a taxi or boda driver “Kyambogo University Main Gate” or “Kyambogo T-Junction”.
- The campus is hilly in places; allow extra time if carrying heavy bags.
- Most academic buildings are reachable within 10–15 minutes’ walk from the Main Gate.

RESPONSE RULES:
- Be warm, concise, and mobile-friendly.
- Use short bullet points for lists.
- When your answer points to a specific navigable location, end with exactly:
  [NAVIGATE:ExactLocationName]
  using ONLY these exact names:
  Main Gate (Kyambogo Road), Eastern Gate (Banda Gate), Western Gate (Kabaka’s Gate),
  Administration Block (Senate), Guild Offices, Registrar’s Office, Finance Department,
  Central Library (Main), E-Library,
  Faculty of Engineering, Faculty of Science, Faculty of Arts and Humanities,
  Faculty of Social Sciences, Faculty of Agriculture, Faculty of Special Needs and Rehabilitation,
  School of Education, School of Management and Entrepreneurship,
  School of Computing and Information Science, School of Built Environment,
  School of Vocational Studies, School of Art and Industrial Design,
  Nanziri Hall, Mandela Hall, Kulubya Hall, Pearl Hall, North Hall,
  Main Cafeteria, Student Market, Bank (Stanbic), Bank (Centenary),
  Main Auditorium (Freedom Square), Engineering Lecture Hall, Science Lecture Hall, Arts Lecture Hall,
  Sports Ground (Main), Basketball Court, Volleyball Court, Tennis Court, University Gym,
  University Health Centre, ICT Centre, Kakumba Chapel, Mosque, Police Post, University Farm
""".strip()# ─────────────────────────────────────────────────────────────────────────────
#  DESTINATIONS & CATEGORIES
# ─────────────────────────────────────────────────────────────────────────────
destinations = {
    "Main Gate (Kyambogo Road)":          [0.347455, 32.625685],
    "Eastern Gate (Banda)":         [0.345694, 32.634164],
    "Western Gate (kabaka's gate)":  [0.353559, 32.630148],
    "Administration Block (Senate)":      [0.34779187235189896, 32.63195052740961],
    "Guild Offices":                      [0.35042, 32.62955],
    "Registrar's Office":                 [0.35015, 32.62930],
    "Finance Department":                 [0.34995, 32.62945],
    "Central Library (Main)":             [0.34971, 32.62848],
    "E-Library":                          [0.34985, 32.62815],
    "Faculty of Engineering Library":     [0.35215, 32.62695],
    "Faculty of Engineering":             [0.3484334211999567, 32.627732720712174],
    "Faculty of Science":                 [0.348591, 32.626383],
    "Faculty of Arts and Humanities":     [0.35192, 32.62885],
    "Faculty of Vocational Studies":      [0.35285, 32.62645],
    "School of Education":                [0.349675, 32.626812],
    "School of Management and Entrepreneurship":               [0.35065, 32.62985],
    "School of Computing and Information Science":           [0.348237, 32.626478],
    
    "School of Built Environment":        [0.35255, 32.62735],
    "Nanziri hall":             [0.3470722484421752, 32.62976017122643],
    "Mandela hall":             [0.346255, 32.630710],
    "North hall":              [0.354156, 32.625517],
    "Kulubya hall":              [0.352325, 32.626041],
    "Pearl hall":      [0.3515699040866617, 32.62514045208313],
    "Main Cafeteria":                     [0.35055, 32.62898],
    "Faculty of Engineering Canteen":     [0.35245, 32.62685],
    "Science Canteen":                    [0.35185, 32.62765],
   
    "Bank (Stanbic)":                     [0.34845, 32.63105],
    "Bank (Centenary)":                   [0.34865, 32.63085],
    "Main Auditorium (CTF)":   [0.34908, 32.62925],
    "Engineering Lecture Hall":           [0.35225, 32.62725],
    "Science Lecture Hall":               [0.35165, 32.62785],
    "Arts Lecture Hall":                  [0.35195, 32.62865],
    "Sports Ground (Main)":               [0.35358, 32.62488],
    "Basketball Court":                   [0.35315, 32.62525],
    "Volleyball Court":                   [0.35325, 32.62545],
    "Tennis Court":                       [0.35305, 32.62565],
    "University Gym":                     [0.35275, 32.62585],
    "University Health Centre":           [0.35125, 32.63015],
    
    
    "ICT Center":                         [0.35025, 32.62875],
    
    "Kakumba Chapel":               [0.34825, 32.63055],
    "Mosque":                             [0.34795, 32.63185],
    "Police Post":                        [0.34915, 32.63335],
    "University Farm":                    [0.35425, 32.62515],
}

categories = {
    "Entrances": ["Main Gate (Kyambogo Road)", "Eastern Gate (banda gate)", "Western Gate (kabaka's gate)"],
    "Administration": ["Administration Block (Senate)", "Guild Offices", "Registrar's Office", "Finance Department"],
    "Libraries": ["Central Library (Main)", "E-Library", "Faculty of Engineering Library"],
    "Faculties & Schools": [
        "Faculty of Engineering", "Faculty of Science", "Faculty of Arts and Humanities",
        "Faculty of Vocational Studies", "School of Education", "School of Management",
        "School of Built Environment",
    ],
    "Student Accommodation": [
        "Naziri", "Mandela",
        "kulubya", "Pearl", "North hall",
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
    "Medical": ["University Health Centre"],
    "Other Facilities": ["ICT Center", "kakumba Chapel", "Mosque", "Police Post", "University Farm"],
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


# ─────────────────────────────────────────────────────────────────────────────
#  ADMIN PANEL ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    """Verify admin password. Returns a session token the frontend stores."""
    data = request.get_json()
    password = data.get("password", "")
    if password == ADMIN_PASSWORD:
        # Simple token: hash of password + secret key
        import hashlib
        token = hashlib.sha256(
            (ADMIN_PASSWORD + app.secret_key).encode()
        ).hexdigest()[:32]
        return jsonify({"ok": True, "token": token})
    return jsonify({"ok": False, "error": "Incorrect password"}), 401


@app.route("/api/admin/verify", methods=["POST"])
def admin_verify():
    """Check if a stored token is still valid."""
    import hashlib
    data  = request.get_json()
    token = data.get("token", "")
    valid_token = hashlib.sha256(
        (ADMIN_PASSWORD + app.secret_key).encode()
    ).hexdigest()[:32]
    return jsonify({"ok": token == valid_token})


@app.route("/api/admin/announcements", methods=["GET"])
def get_announcements():
    return jsonify(load_announcements())


@app.route("/api/admin/announcements", methods=["POST"])
def save_announcement():
    """Add a new announcement."""
    import hashlib, time
    data  = request.get_json()
    token = data.get("token", "")
    valid_token = hashlib.sha256(
        (ADMIN_PASSWORD + app.secret_key).encode()
    ).hexdigest()[:32]
    if token != valid_token:
        return jsonify({"error": "Unauthorised"}), 401

    msg  = data.get("msg", "").strip()
    kind = data.get("type", "info")
    if not msg:
        return jsonify({"error": "Message is required"}), 400

    announcements = load_announcements()
    announcements.insert(0, {
        "id":   int(time.time() * 1000),
        "msg":  msg,
        "type": kind,
        "time": __import__("datetime").datetime.now().strftime("%d %b %Y, %H:%M"),
    })
    save_announcements(announcements)
    return jsonify({"ok": True, "count": len(announcements)})


@app.route("/api/admin/announcements/<int:ann_id>", methods=["DELETE"])
def delete_announcement(ann_id):
    """Delete an announcement by id."""
    import hashlib
    token = request.args.get("token", "")
    valid_token = hashlib.sha256(
        (ADMIN_PASSWORD + app.secret_key).encode()
    ).hexdigest()[:32]
    if token != valid_token:
        return jsonify({"error": "Unauthorised"}), 401

    announcements = load_announcements()
    announcements = [a for a in announcements if a.get("id") != ann_id]
    save_announcements(announcements)
    return jsonify({"ok": True})


@app.route("/api/admin/export", methods=["GET"])
def admin_export():
    """Download current destinations as a Python file."""
    import hashlib
    token = request.args.get("token", "")
    valid_token = hashlib.sha256(
        (ADMIN_PASSWORD + app.secret_key).encode()
    ).hexdigest()[:32]
    if token != valid_token:
        return jsonify({"error": "Unauthorised"}), 401

    lines = ["# Auto-exported from KYU Admin Panel\n",
             "# Paste this destinations dict into app.py\n\n",
             "destinations = {\n"]
    for name, (lat, lon) in destinations.items():
        lines.append(f'    "{name}": [{lat}, {lon}],\n')
    lines.append("}\n")

    from flask import Response
    return Response(
        "".join(lines),
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=destinations.py"}
    )


# ─────────────────────────────────────────────────────────────────────────────
#  PUBLIC ANNOUNCEMENTS  (shown on home screen to all users)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/announcements", methods=["GET"])
def public_announcements():
    """Return announcements for display on the home screen."""
    return jsonify(load_announcements())

