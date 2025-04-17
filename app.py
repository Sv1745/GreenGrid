from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
import random
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Flask app config
app = Flask(__name__, template_folder="templates", static_folder="static")

# Supabase config
supabase_url = "https://yhqdszazpxmcetpxnyjx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlocWRzemF6cHhtY2V0cHhueWp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQyNTQwOTgsImV4cCI6MjA1OTgzMDA5OH0.5CtJVKBcnAmqhhdOx-EnS61NdR-WPq_5l-NFAEwzhqM"
supabase: Client = create_client(supabase_url, supabase_key)

# Gemini API config
genai.configure(api_key="AIzaSyANl9jj_tbPtOIdCqykobiaI3Dsubbk8nM")
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

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

    # Insert into Supabase
    result = supabase.table("microgrids").insert({
        "community_size": community_size,
        "energy_needs": energy_needs,
        "solar_capacity": solar_capacity,
        "battery_size": battery_size,
        "carbon_savings": carbon_savings,
        "resilience_score": resilience_score,
        "maintenance_schedule": maintenance_schedule,
        "trade_credits": trade_credits,
        "budget": budget
    }).execute()

    if result.get("status_code", 200) >= 400:
        return jsonify({"error": "Failed to insert into Supabase"}), 500

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
    response = supabase.table("microgrids").select("carbon_savings, resilience_score, trade_credits").execute()
    rows = response.data if response and response.data else []

    if not rows:
        return jsonify({
            'totalSavings': 0,
            'avgResilience': 0,
            'totalCredits': 0
        })

    total_savings = sum(row['carbon_savings'] for row in rows)
    avg_resilience = sum(row['resilience_score'] for row in rows) / len(rows)
    total_credits = sum(row['trade_credits'] for row in rows)

    return jsonify({
        'totalSavings': total_savings,
        'avgResilience': avg_resilience,
        'totalCredits': total_credits
    })

@app.route('/leaderboard')
def leaderboard():
    response = supabase.table("microgrids") \
        .select("community_size, resilience_score") \
        .order("resilience_score", desc=True) \
        .limit(5).execute()

    leaderboard = [{"size": row['community_size'], "score": row['resilience_score']} for row in response.data]
    return jsonify(leaderboard)

# No need for init_db() in Supabase setup
if __name__ == '__main__':
    app.run(debug=True)
