from flask import Flask, render_template
import json
import os

app = Flask(__name__)

@app.route("/")
def home():
    return '''
    <h2>Welcome to Proof Alpha</h2>
    <p><a href="/log">📊 View Log Dashboard</a></p>
    '''

@app.route("/log")
def view_log():
    try:
        with open("scan_results.json", "r") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs = logs[::-1]  # Most recent first
    return render_template("log_dashboard.html", logs=logs)

if __name__ == "__main__":
    print("🧠 ROUTES LOADED: / and /log")
    print("📁 Current Directory:", os.getcwd())
    app.run(debug=True)
