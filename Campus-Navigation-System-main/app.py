from flask import Flask, render_template, request, jsonify
import requests
import math

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  GOOGLE GEMINI API  (free tier — no credit card needed)
#  Get your free key at: https://aistudio.google.com/app/apikey
#  Paste it below between the quotes
# ─────────────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = "AIzaSyB-6oJGbcUfV4vV_-L_MTeRWjHah2Xgu0g"

# Using gemini-1.5-flash — fastest & free
GEMINI_MODEL   = "gemini-1.5-flash"
GEMINI_BASE    = "https://generativelanguage.googleapis.com/v1beta/models"


def gemini_url():
    """Build the Gemini endpoint URL fresh each call so key changes are picked up."""
    return f"{GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


# ─────────────────────────────────────────────────────────────────────────────
#  CAMPUS KNOWLEDGE  — shared by both AI endpoints
# ─────────────────────────────────────────────────────────────────────────────
CAMPUS_CONTEXT = """
You are the official AI assistant for Kyambogo University (KYU) campus in Kampala, Uganda.
Answer ONLY questions about Kyambogo University — locations, directions, facilities, student services.
For anything unrelated to campus, politely redirect the user.

CAMPUS KNOWLEDGE:

ENTRANCES:
- Main Gate (Kyambogo Road): primary entrance, most accessible, 24/7 security desk
- Eastern Gate (Police Post): east side, closest gate to student hostels
- Western Gate (Faculty of Science): west side near Engineering and Science faculties

ADMINISTRATION (open Mon-Fri 8am-5pm):
- Administration Block (Senate): collect student ID, Registrar's Office, Finance Department
- Guild Offices: student government, next to Admin Block

LIBRARIES:
- Central Library (Main): thousands of textbooks and journals, borrow up to 3 books — Mon-Sat 8am-8pm
- E-Library: computers and internet for digital research, right next to Central Library
- Faculty of Engineering Library: inside Engineering building

FACULTIES & SCHOOLS:
West side: Engineering, Science, Arts & Humanities, Vocational Studies, Health Sciences, Built Environment
Central/East: Education, Management, Law

DINING:
- Main Cafeteria: central campus, 3 meals/day, busiest 12pm-2pm
- Faculty Engineering Canteen & Science Canteen: quieter, closer to classes
- Student Market: east side near hostels — stationery, toiletries, snacks

BANKING:
- Bank Stanbic & Bank Centenary: east side near Student Market

MEDICAL:
- University Health Centre: general health, Mon-Fri 8am-5pm
- Dental Clinic & Pharmacy: right next to Health Centre
- After-hours emergency: Police Post near Eastern Gate (24/7) — nearest hospital is Mulago

RELIGIOUS:
- Chapel (St. Francis) & Mosque: east side, open to all students

STUDENT HOSTELS (east side, near Eastern Gate):
- Girls Hostel Block A & B, Boys Hostel Block C & D, International Students Hostel
- All have 24-hour security and study areas

SPORTS (west side):
- Sports Ground (Main), Basketball Court, Volleyball Court, Tennis Court, University Gym
- Sports clubs and inter-faculty competitions run every semester

OTHER FACILITIES:
- ICT Center: computer workstations and internet access
- Printing Press: printing, binding, photocopying — best for large jobs like final year reports
- University Bookshop: textbooks and stationery
- Police Post: near Eastern Gate, 24/7
- University Farm: far west side

NAVIGATION TIPS:
- Campus is walkable end-to-end in about 20 minutes
- Main tarmac road runs through the centre from Main Gate
- Use well-known landmarks in directions: "pass the cafeteria", "turn at the Admin Block"

RESPONSE RULES:
- Be warm, concise, and mobile-friendly
- Use short bullet points for lists
- When your answer points to a specific navigable destination, end your response with exactly:
  [NAVIGATE:ExactDestinationName]
- Only include ONE [NAVIGATE:...] tag per response
- Use ONLY these exact names inside the tag:
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
#  GEMINI HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def gemini_chat(messages):
    """
    Multi-turn chat via Gemini.
    messages: list of {role, content} — 'assistant' role is mapped to 'model'.
    System instruction is passed via the proper systemInstruction field.
    """
    contents = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else "user"
        contents.append({
            "role":  role,
            "parts": [{"text": m["content"]}]
        })

    payload = {
        "systemInstruction": {
            "parts": [{"text": CAMPUS_CONTEXT}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature":     0.7,
            "maxOutputTokens": 800,
        },
    }

    resp = requests.post(gemini_url(), json=payload, timeout=20)

    # Surface the actual Gemini error message if the call fails
    if not resp.ok:
        try:
            err = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            err = resp.text
        raise Exception(f"Gemini {resp.status_code}: {err}")

    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def gemini_tip(faculty, name, stop):
    """Single short tip for a First Day Guide tour stop."""
    prompt = (
        f"You are a friendly senior student at Kyambogo University in Kampala, Uganda. "
        f"Write ONE short practical tip (2 sentences max, no intro phrase) about "
        f'"{stop}" that is specifically useful for a {faculty} student named {name}. '
        f"Be specific and accurate to the real Kyambogo University campus."
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 120},
    }
    resp = requests.post(gemini_url(), json=payload, timeout=15)
    if not resp.ok:
        raise Exception(f"Gemini tip {resp.status_code}")
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


# ─────────────────────────────────────────────────────────────────────────────
#  CAMPUS DESTINATIONS
# ─────────────────────────────────────────────────────────────────────────────
destinations = {
    "Main Gate (Kyambogo Road)":          [0.34795, 32.63142],
    "Eastern Gate (Police Post)":         [0.34938, 32.63358],
    "Western Gate (Faculty of Science)":  [0.35168, 32.62718],
    "Administration Block (Senate)":      [0.35022, 32.62975],
    "Guild Offices":                      [0.35035, 32.62960],
    "Registrar's Office":                [0.35010, 32.62938],
    "Finance Department":                 [0.34998, 32.62950],
    "Central Library (Main)":            [0.34968, 32.62852],
    "E-Library":                         [0.34980, 32.62820],
    "Faculty of Engineering Library":    [0.35210, 32.62698],
    "Faculty of Engineering":            [0.35228, 32.62708],
    "Faculty of Science":                [0.35172, 32.62758],
    "Faculty of Arts and Humanities":    [0.35188, 32.62888],
    "Faculty of Vocational Studies":     [0.35282, 32.62648],
    "School of Education":               [0.34928, 32.63022],
    "School of Management":              [0.35062, 32.62988],
    "School of Law":                     [0.35122, 32.62948],
    "School of Health Sciences":         [0.35312, 32.62688],
    "School of Built Environment":       [0.35252, 32.62738],
    "Girls Hostel (Block A)":            [0.34608, 32.63228],
    "Girls Hostel (Block B)":            [0.34638, 32.63208],
    "Boys Hostel (Block C)":             [0.34562, 32.63078],
    "Boys Hostel (Block D)":             [0.34528, 32.63118],
    "International Students Hostel":     [0.34718, 32.63188],
    "Main Cafeteria":                    [0.35052, 32.62902],
    "Faculty of Engineering Canteen":    [0.35242, 32.62688],
    "Science Canteen":                   [0.35182, 32.62768],
    "Student Market":                    [0.34888, 32.63128],
    "Bank (Stanbic)":                    [0.34848, 32.63108],
    "Bank (Centenary)":                  [0.34868, 32.63088],
    "Main Auditorium (Freedom Square)":  [0.34905, 32.62928],
    "Engineering Lecture Hall":          [0.35222, 32.62728],
    "Science Lecture Hall":              [0.35162, 32.62788],
    "Arts Lecture Hall":                 [0.35192, 32.62868],
    "Sports Ground (Main)":              [0.35355, 32.62492],
    "Basketball Court":                  [0.35312, 32.62528],
    "Volleyball Court":                  [0.35322, 32.62548],
    "Tennis Court":                      [0.35302, 32.62568],
    "University Gym":                    [0.35272, 32.62588],
    "University Health Centre":          [0.35122, 32.63018],
    "Dental Clinic":                     [0.35112, 32.63038],
    "Pharmacy":                          [0.35092, 32.63048],
    "ICT Center":                        [0.35022, 32.62878],
    "Printing Press":                    [0.34952, 32.62988],
    "University Bookshop":               [0.34942, 32.62918],
    "Chapel (St. Francis)":              [0.34828, 32.63058],
    "Mosque":                            [0.34798, 32.63188],
    "Police Post":                       [0.34918, 32.63338],
    "University Farm":                   [0.35422, 32.62518],
}

categories = {
    "Entrances": [
        "Main Gate (Kyambogo Road)", "Eastern Gate (Police Post)",
        "Western Gate (Faculty of Science)",
    ],
    "Administration": [
        "Administration Block (Senate)", "Guild Offices",
        "Registrar's Office", "Finance Department",
    ],
    "Libraries": [
        "Central Library (Main)", "E-Library", "Faculty of Engineering Library",
    ],
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
    "Sports & Recreation": [
        "Sports Ground (Main)", "Basketball Court", "Volleyball Court",
        "Tennis Court", "University Gym",
    ],
    "Medical": [
        "University Health Centre", "Dental Clinic", "Pharmacy",
    ],
    "Other Facilities": [
        "ICT Center", "Printing Press", "University Bookshop",
        "Chapel (St. Francis)", "Mosque", "Police Post", "University Farm",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
#  HAVERSINE
# ─────────────────────────────────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(d_lon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE ROUTES
# ─────────────────────────────────────────────────────────────────────────────
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
    return render_template("result.html",
                           destination_name=dest_name,
                           dest_lat=lat, dest_lon=lon)


@app.route("/assistant")
def assistant():
    return render_template("assistant.html")


@app.route("/firstday")
def firstday():
    return render_template("firstday.html")


# ─────────────────────────────────────────────────────────────────────────────
#  AI ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/assistant", methods=["POST"])
def api_assistant():
    data     = request.get_json()
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": "No messages provided"}), 400
    try:
        reply = gemini_chat(messages)
        return jsonify({"reply": reply})
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out — please try again."}), 504
    except Exception as e:
        print(f"[/api/assistant ERROR] {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai-tip", methods=["POST"])
def api_ai_tip():
    data    = request.get_json()
    faculty = data.get("faculty", "your faculty")
    name    = data.get("name",    "Fresher")
    stop    = data.get("stop",    "this location")
    try:
        tip = gemini_tip(faculty, name, stop)
        return jsonify({"tip": tip})
    except Exception as e:
        print(f"[/api/ai-tip ERROR] {e}")
        return jsonify({"tip": ""}), 200   # JS falls back to hardcoded text


# ─────────────────────────────────────────────────────────────────────────────
#  ROUTING ENDPOINT  (OSRM walking, straight-line fallback)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/route", methods=["POST"])
def api_route():
    data     = request.get_json()
    user_lat = data.get("lat")
    user_lon = data.get("lon")
    dest_lat = data.get("dest_lat")
    dest_lon = data.get("dest_lon")

    if not all([user_lat, user_lon, dest_lat, dest_lon]):
        return jsonify({"error": "Missing coordinates"}), 400

    # ── OSRM (free, no API key needed) ──────────────────────────────────────
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
                    if mtype == "depart":
                        text = "Start walking"
                    elif mtype == "arrive":
                        text = "Arrive at your destination"
                    elif mtype == "turn":
                        text = f"Turn {modifier}"
                    elif mtype in ("continue", "new name"):
                        text = "Continue straight"
                    elif mtype == "roundabout":
                        exit_n = step.get("maneuver", {}).get("exit", "")
                        text   = f"Take exit {exit_n} at the roundabout"
                    else:
                        text = mtype.replace("-", " ").capitalize()
                    instructions.append({
                        "text":     text,
                        "distance": round(dist, 1),
                        "time":     round(step.get("duration", 0) / 60, 1),
                    })

            return jsonify({
                "success":      True,
                "path":         path,
                "distance_km":  distance_km,
                "duration_min": duration_min,
                "instructions": instructions,
                "source":       "osrm",
            })

    except Exception as e:
        print(f"[OSRM ERROR] {e}")

    # ── Straight-line fallback ──────────────────────────────────────────────
    dist = haversine(user_lat, user_lon, dest_lat, dest_lon)
    return jsonify({
        "success":      True,
        "path":         [[user_lat, user_lon], [dest_lat, dest_lon]],
        "distance_km":  round(dist, 2),
        "duration_min": max(1, round(dist * 15)),
        "instructions": [
            {"text": "Head toward your destination",
             "distance": round(dist * 1000, 1), "time": round(dist * 15, 1)},
            {"text": "Arrive at your destination", "distance": 0, "time": 0},
        ],
        "source": "direct",
    })


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
