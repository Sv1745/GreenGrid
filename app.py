from flask import Flask, render_template, request, jsonify
import sqlite3
import random
import google.generativeai as genai
app = Flask(__name__)

genai.configure(api_key="AIzaSyANl9jj_tbPtOIdCqykobiaI3Dsubbk8nM")  # Replace YOUR_API_KEY with the actual key
model = genai.GenerativeModel("gemini-2.0-flash")

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS microgrids
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  community_size INTEGER,
                  energy_needs REAL,
                  solar_capacity REAL,
                  battery_size REAL,
                  carbon_savings REAL,
                  resilience_score REAL,
                  maintenance_schedule TEXT,
                  trade_credits REAL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Gemini-powered optimization with debugging
def optimize_microgrid(community_size, energy_needs, location_data):
    print(f"Optimizing for: community_size={community_size}, energy_needs={energy_needs}, location_data={location_data}")
    prompt = f"Optimize a microgrid for a community of {community_size} households with {energy_needs} kWh daily needs, considering {location_data} (weather, soil, vegetation). Provide solar_capacity (kW), battery_size (kWh), carbon_savings (kg CO2e), resilience_score (0-100%), maintenance_schedule (days), and trade_credits (kWh) as a JSON object."
    try:
        response = gemini_model.generate_content(prompt)
        print(f"Gemini response: {response.text}")
        import json
        result = json.loads(response.text)  # Assuming Gemini returns JSON
        return (result.get('solar_capacity', energy_needs * 1.2),
                result.get('battery_size', energy_needs * 0.5),
                result.get('carbon_savings', community_size * 0.8 * energy_needs),
                result.get('resilience_score', random.uniform(70, 95)),
                result.get('maintenance_schedule', '30 days'),
                result.get('trade_credits', community_size * 0.1))
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"Gemini error: {e}, falling back to mock data")
        return (energy_needs * 1.2, energy_needs * 0.5, community_size * 0.8 * energy_needs,
                random.uniform(70, 95), '30 days', community_size * 0.1)

# Gemini-powered gamification challenge
def generate_challenge(community_size, resilience_score):
    prompt = f"Generate a climate resilience challenge for a community of {community_size} households with a resilience_score of {resilience_score}%. Include a goal, reward (Resilience Points), and deadline (days). Return as JSON."
    try:
        response = gemini_model.generate_content(prompt)
        return json.loads(response.text)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Challenge generation error: {e}, using default")
        return {"goal": "Reduce energy use by 10%", "reward": 100, "deadline": 7}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize():
    print("Received optimize request")
    data = request.get_json()
    if not data:
        print("No JSON data received")
        return jsonify({"error": "No data provided"}), 400
    community_size = int(data.get('communitySize', 0))
    energy_needs = float(data.get('energyNeeds', 0))
    location_data = data.get('locationData', 'tropical climate, moderate shade')

    if not community_size or not energy_needs:
        print("Invalid input data")
        return jsonify({"error": "Community size and energy needs are required"}), 400

    solar_capacity, battery_size, carbon_savings, resilience_score, maintenance_schedule, trade_credits = optimize_microgrid(community_size, energy_needs, location_data)
    challenge = generate_challenge(community_size, resilience_score)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO microgrids (community_size, energy_needs, solar_capacity, battery_size, carbon_savings, resilience_score, maintenance_schedule, trade_credits) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (community_size, energy_needs, solar_capacity, battery_size, carbon_savings, resilience_score, maintenance_schedule, trade_credits))
    conn.commit()
    conn.close()

    print(f"Optimization result: {locals()}")
    return jsonify({
        'solarCapacity': solar_capacity,
        'batterySize': battery_size,
        'carbonSavings': carbon_savings,
        'resilienceScore': resilience_score,
        'maintenanceSchedule': maintenance_schedule,
        'tradeCredits': trade_credits,
        'challenge': challenge
    })

@app.route('/community-stats')
def community_stats():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT SUM(carbon_savings), AVG(resilience_score), SUM(trade_credits) FROM microgrids")
    total_savings, avg_resilience, total_credits = c.fetchone()
    conn.close()
    return jsonify({
        'totalSavings': total_savings or 0,
        'avgResilience': avg_resilience or 0,
        'totalCredits': total_credits or 0
    })

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT community_size, resilience_score FROM microgrids ORDER BY resilience_score DESC LIMIT 5")
    leaderboard = [{"size": row[0], "score": row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(leaderboard)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)