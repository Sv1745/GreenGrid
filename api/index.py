from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    print("✅ Home route was called")
    return "Hello from Flask on Vercel!"

@app.route('/favicon.ico')
def favicon():
    print("🧩 Favicon route hit (optional)")
    return '', 204  # Avoid errors on missing favicon

# Vercel needs this handler to work with Flask apps
def handler(environ, start_response):
    return app(environ, start_response)
