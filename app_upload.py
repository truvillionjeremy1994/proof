from flask import Flask, render_template
import json
import os
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h2>📷 Proof Alpha v1.7</h2>
    <p>Take any photo and we’ll tell you if it was…</p>
    <ul>
      <li>✅ Taken by the person who sent it.</li>
      <li>❌ Faked, tampered with, or recycled from the internet.</li>
    </ul>
    <p><a href='/log'>📊 View Log Dashboard</a></p>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file"><br><br>
      <input type="submit" value="Upload & Verify">
    </form>
    """

@app.route("/log")
def view_log():
    log_path = "scan_results.json"

    try:
        with open(log_path, "r") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs = logs[::-1]
    return render_template("log_dashboard.html", logs=logs)

if __name__ == "__main__":
    app.run(debug=True)
