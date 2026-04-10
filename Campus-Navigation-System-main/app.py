from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# GraphHopper API Key
GRAPHHOPPER_API_KEY = "663c1034-015a-454f-b4df-928f15b8b91b"

# Accurate Kyambogo University coordinates (from Google Maps)
destinations = {
    # Main Entrances
    "Main Gate (Kyambogo Road)": [0.34785, 32.63135],
    "Eastern Gate (Police Post)": [0.34925, 32.63345],
    "Western Gate (Faculty of Science)": [0.35175, 32.62715],
    
    # Administrative Buildings
    "Administration Block (Senate)": [0.35028, 32.62962],
    "Guild Offices": [0.35042, 32.62955],
    "Registrar's Office": [0.35015, 32.62930],
    "Finance Department": [0.34995, 32.62945],
    
    # Libraries
    "Central Library (Main)": [0.34971, 32.62848],
    "E-Library": [0.34985, 32.62815],
    "Faculty of Engineering Library": [0.35215, 32.62695],
    
    # Faculties and Academic Buildings
    "Faculty of Engineering": [0.35231, 32.62705],
    "Faculty of Science": [0.35175, 32.62754],
    "Faculty of Arts and Humanities": [0.35192, 32.62885],
    "Faculty of Vocational Studies": [0.35285, 32.62645],
    "School of Education": [0.34925, 32.63018],
    "School of Management": [0.35065, 32.62985],
    "School of Law": [0.35125, 32.62945],
    "School of Health Sciences": [0.35315, 32.62685],
    "School of Built Environment": [0.35255, 32.62735],
    
    # Student Accommodation
    "Girls Hostel (Block A)": [0.34605, 32.63223],
    "Girls Hostel (Block B)": [0.34635, 32.63205],
    "Boys Hostel (Block C)": [0.34558, 32.63075],
    "Boys Hostel (Block D)": [0.34525, 32.63115],
    "International Students Hostel": [0.34715, 32.63185],
    
    # Dining and Shopping
    "Main Cafeteria": [0.35055, 32.62898],
    "Faculty of Engineering Canteen": [0.35245, 32.62685],
    "Science Canteen": [0.35185, 32.62765],
    "Student Market": [0.34885, 32.63125],
    "Bank (Stanbic)": [0.34845, 32.63105],
    "Bank (Centenary)": [0.34865, 32.63085],
    
    # Auditoriums and Halls
    "Main Auditorium (Freedom Square)": [0.34908, 32.62925],
    "Engineering Lecture Hall": [0.35225, 32.62725],
    "Science Lecture Hall": [0.35165, 32.62785],
    "Arts Lecture Hall": [0.35195, 32.62865],
    
    # Sports and Recreation
    "Sports Ground (Main)": [0.35358, 32.62488],
    "Basketball Court": [0.35315, 32.62525],
    "Volleyball Court": [0.35325, 32.62545],
    "Tennis Court": [0.35305, 32.62565],
    "University Gym": [0.35275, 32.62585],
    
    # Medical and Health
    "University Health Centre": [0.35125, 32.63015],
    "Dental Clinic": [0.35115, 32.63035],
    "Pharmacy": [0.35095, 32.63045],
    
    # Other Facilities
    "ICT Center": [0.35025, 32.62875],
    "Printing Press": [0.34955, 32.62985],
    "University Bookshop": [0.34945, 32.62915],
    "Chapel (St. Francis)": [0.34825, 32.63055],
    "Mosque": [0.34795, 32.63185],
    "Police Post": [0.34915, 32.63335],
    "University Farm": [0.35425, 32.62515],
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    # Group destinations by category for better organization
    categories = {
        "Entrances": ["Main Gate (Kyambogo Road)", "Eastern Gate (Police Post)", "Western Gate (Faculty of Science)"],
        "Administration": ["Administration Block (Senate)", "Guild Offices", "Registrar's Office", "Finance Department"],
        "Libraries": ["Central Library (Main)", "E-Library", "Faculty of Engineering Library"],
        "Faculties & Schools": ["Faculty of Engineering", "Faculty of Science", "Faculty of Arts and Humanities", 
                               "Faculty of Vocational Studies", "School of Education", "School of Management", 
                               "School of Law", "School of Health Sciences", "School of Built Environment"],
        "Student Accommodation": ["Girls Hostel (Block A)", "Girls Hostel (Block B)", "Boys Hostel (Block C)", 
                                 "Boys Hostel (Block D)", "International Students Hostel"],
        "Dining & Shopping": ["Main Cafeteria", "Faculty of Engineering Canteen", "Science Canteen", 
                             "Student Market", "Bank (Stanbic)", "Bank (Centenary)"],
        "Auditoriums & Halls": ["Main Auditorium (Freedom Square)", "Engineering Lecture Hall", 
                               "Science Lecture Hall", "Arts Lecture Hall"],
        "Sports & Recreation": ["Sports Ground (Main)", "Basketball Court", "Volleyball Court", 
                               "Tennis Court", "University Gym"],
        "Medical": ["University Health Centre", "Dental Clinic", "Pharmacy"],
        "Other Facilities": ["ICT Center", "Printing Press", "University Bookshop", "Chapel (St. Francis)", 
                           "Mosque", "Police Post", "University Farm"]
    }
    return render_template('home.html', categories=categories)

@app.route('/result', methods=['POST'])
def result():
    dest_name = request.form.get('destination')
    
    if dest_name not in destinations:
        return "<h1>Invalid destination</h1>", 400

    lat, lon = destinations[dest_name]
    
    return render_template(
        'result.html',
        destination_name=dest_name,
        dest_lat=lat,
        dest_lon=lon
    )

@app.route('/api/route', methods=['POST'])
def api_route():
    data = request.get_json()
    user_lat = data.get('lat')
    user_lon = data.get('lon')
    dest_lat = data.get('dest_lat')
    dest_lon = data.get('dest_lon')

    if not all([user_lat, user_lon, dest_lat, dest_lon]):
        return jsonify({"error": "Missing coordinates"}), 400

    try:
        url = "https://graphhopper.com/api/1/route"

        params = {
            "point": [f"{user_lat},{user_lon}", f"{dest_lat},{dest_lon}"],
            "vehicle": "foot",
            "locale": "en",
            "key": GRAPHHOPPER_API_KEY,
            "points_encoded": "false",
            "instructions": "true",
            "elevation": "false",
            "calc_points": "true",
            "optimize": "true"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        result = response.json()

        if "paths" not in result or not result["paths"]:
            return jsonify({"error": "No route found"}), 404

        path_data = result["paths"][0]

        # Extract polyline coordinates [lat, lon]
        points = path_data["points"]["coordinates"]
        route_path = [[lat, lon] for lon, lat in points]

        distance_km = round(path_data["distance"] / 1000, 2)
        duration_min = round(path_data["time"] / 1000 / 60)
        
        # Extract turn-by-turn instructions
        instructions = []
        for instruction in path_data.get("instructions", []):
            instructions.append({
                "text": instruction.get("text", ""),
                "distance": round(instruction.get("distance", 0), 1),
                "time": round(instruction.get("time", 0) / 1000 / 60, 1)
            })

        return jsonify({
            "success": True,
            "path": route_path,
            "distance_km": distance_km,
            "duration_min": duration_min,
            "instructions": instructions
        })

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)