KYAMBOGO CAMPUS NAVIGATOR - Setup Instructions
==============================================

1. Install dependencies:
   pip install flask requests

2. Project structure:
   your_project/
   ├── app.py
   ├── static/
   │   └── logo.png
   └── templates/
       ├── index.html
       ├── home.html
       └── result.html

3. Run the app:
   python app.py

4. Open in browser:
   http://localhost:5000

ROUTING FIX NOTES:
- The app now uses OSRM (Open Source Routing Machine) which has
  better OpenStreetMap footpath data for Uganda than GraphHopper.
- If OSRM is unreachable, a straight-line distance is shown as fallback.
- The location validation that blocked users outside a tiny bounding box
  has been removed — anyone on or near campus will now get routing.
- Route is debounced (max once every 15 seconds) to avoid API spam.
