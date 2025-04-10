from flask import Flask, render_template, request, jsonify
import sqlite3
import random
import google.generativeai as genai
import json
import os

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS microgrids")
    c.execute('''CREATE TABLE microgrids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        community_size INTEGER,
        energy_needs REAL,
        solar_capacity REAL,
        battery_size REAL,
        carbon_savings REAL,
        resilience_score REAL,
        maintenance_schedule TEXT,
        trade_credits REAL,
        budget REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

# Gemini-powered optimization
def optimize_microgrid(community_size, energy_needs, location_data, budget=None):
    print(f"Optimizing for: community_size={community_size}, energy_needs={energy_needs}, location_data={location_data}, budget={budget}")
    prompt = f"""
    Optimize a microgrid for a community of {community_size} households with {energy_needs} kWh daily needs,
    considering {location_data} (weather, soil, vegetation). If budget is provided ({budget} USD), prioritize
    cost-effective solutions. Return a JSON object with: solar_capacity (kW), battery_size (kWh),
    carbon_savings (kg CO2e), resilience_score (0-100%), maintenance_schedule (days), trade_credits (kWh).
    """
    try:
        response = gemini_model.generate_content(prompt)
        print(f"Gemini response: {response.text}")
        result = json.loads(response.text.strip())
        return (
            result.get('solar_capacity', energy_needs * 1.2),
            result.get('battery_size', energy_needs * 0.5),
            result.get('carbon_savings', community_size * 0.8 * energy_needs),
            result.get('resilience_score', random.uniform(70, 95)),
            result.get('maintenance_schedule', '30 days'),
            result.get('trade_credits', community_size * 0.1)
        )
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"Gemini error: {e}, falling back to mock data")
        return (
            energy_needs * 1.2,
            energy_needs * 0.5,
            community_size * 0.8 * energy_needs,
            random.uniform(70, 95),
            '30 days',
            community_size * 0.1
        )

# Gemini-powered challenge generation
def generate_challenge(community_size, resilience_score):
    prompt = f"""
    Generate a climate resilience challenge for a community of {community_size} households with a resilience_score of {resilience_score}%.
    Include a goal, reward (Resilience Points), and deadline (days). Return as JSON with strict formatting.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return json.loads(response.text.strip())
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
        return jsonify({"error": "No data provided"}), 400

    community_size = int(data.get('communitySize', 0))
    energy_needs = float(data.get('energyNeeds', 0))
    location_data = data.get('locationData', 'tropical climate, moderate shade')
    budget = data.get('budget', None)

    if not community_size or not energy_needs:
        return jsonify({"error": "Community size and energy needs are required"}), 400

    solar_capacity, battery_size, carbon_savings, resilience_score, maintenance_schedule, trade_credits = optimize_microgrid(
        community_size, energy_needs, location_data, budget
    )
    challenge = generate_challenge(community_size, resilience_score)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO microgrids (community_size, energy_needs, solar_capacity, battery_size, carbon_savings, resilience_score, maintenance_schedule, trade_credits, budget) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (community_size, energy_needs, solar_capacity, battery_size, carbon_savings, resilience_score, maintenance_schedule, trade_credits, budget))
    conn.commit()
    conn.close()

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
    result = c.fetchone()
    conn.close()
    total_savings, avg_resilience, total_credits = result if result[0] else (0, 0, 0)
    return jsonify({
        'totalSavings': total_savings,
        'avgResilience': avg_resilience,
        'totalCredits': total_credits
    })

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT community_size, resilience_score FROM microgrids ORDER BY resilience_score DESC LIMIT 5")
    leaderboard = [{"size": row[0], "score": row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(leaderboard)

# Required for Vercel to work
init_db()
app = app