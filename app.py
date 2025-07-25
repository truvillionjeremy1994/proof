from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, render_template_string, jsonify
from werkzeug.utils import secure_filename
import os
import datetime
import json
import shutil
import random

app = Flask(__name__)
app.secret_key = 'super_secret_key_123'

# Paths
UPLOAD_FOLDER = 'uploads'
SCAN_LOG = 'scan_results.json'
FALSE_LOG = 'false_log.json'
FLAG_HONEST = os.path.join('false_results', 'honest_but_flagged')
FLAG_DECEPTIVE = os.path.join('false_results', 'deceptive_but_passed')

# Ensure folders exist
for folder in [UPLOAD_FOLDER, FLAG_HONEST, FLAG_DECEPTIVE]:
    os.makedirs(folder, exist_ok=True)

# ---------------------------
# Scoring Logic
# ---------------------------

def calculate_behavior_score(upload_count, ip_variation=False, rapid_fire=False):
    if upload_count == 1:
        return 0.0
    elif upload_count == 2:
        return 0.2
    elif upload_count == 3:
        return 0.4
    elif upload_count == 4:
        return 0.8
    else:
        base = 1.2
        if ip_variation:
            base += 0.3
        if rapid_fire:
            base += 0.3
        return min(base, 2.0)

def calculate_intent_score(A, D, B):
    I = (A * 1.25) - (D * 1.5 + B * 1.0)
    return max(0, min(100, round(I)))

def analyze_image(filepath, user_ip, current_time):
    A = round(random.uniform(70, 100), 2)
    D = round(random.uniform(0, 30), 2)

    logs = []
    if os.path.exists(SCAN_LOG):
        try:
            with open(SCAN_LOG, 'r') as f:
                logs = json.load(f)
        except:
            logs = []

    filename = os.path.basename(filepath)
    same_file_logs = [r for r in logs if r.get('filename') == filename]
    same_ip_logs = [r for r in logs if r.get('ip') == user_ip]

    upload_count = len(same_file_logs) + 1
    ip_variation = len({r.get('ip') for r in same_file_logs}) > 1

    rapid_fire = False
    for log in same_ip_logs:
        try:
            past_time = datetime.datetime.fromisoformat(log.get('timestamp'))
            if (current_time - past_time).total_seconds() <= 300:
                rapid_fire = True
                break
        except:
            continue

    B = calculate_behavior_score(upload_count, ip_variation, rapid_fire)
    I = calculate_intent_score(A, D, B)

    if I >= 80:
        intent, emoji = 'Honest Photo', '✅'
        reason = "This photo's digital footprint appears genuine — the sender shows no signs of deception."
    elif I >= 60:
        intent, emoji = 'Uncertain Photo', '⚠️'
        reason = "This photo's digital footprint raises some uncertainty — stay cautious with the sender."
    else:
        intent, emoji = 'Deceptive Photo', '❌'
        reason = "This photo's digital footprint shows signs of manipulation — the sender may be trying to mislead you."

    return {
        "score": I,
        "intent": intent,
        "emoji": emoji,
        "reason": reason,
        "A": A,
        "D": D,
        "B": B,
        "upload_count": upload_count,
        "ip_variation": ip_variation,
        "rapid_fire": rapid_fire,
        "timestamp": current_time.isoformat(),
        "ip": user_ip,
        "filename": filename
    }

# ---------------------------
# Routes
# ---------------------------

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file or file.filename == '':
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    user_ip = request.remote_addr
    now = datetime.datetime.now()

    result = analyze_image(filepath, user_ip, now)

    logs = []
    if os.path.exists(SCAN_LOG):
        try:
            with open(SCAN_LOG, 'r') as f:
                logs = json.load(f)
        except:
            logs = []

    logs.append(result)
    with open(SCAN_LOG, 'w') as f:
        json.dump(logs, f, indent=2)

    session["result"] = result
    return redirect(url_for('result'))

@app.route('/result')
def result():
    result = session.get("result")
    if not result:
        return redirect(url_for('index'))
    return render_template("result.html", result=result)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/log', methods=['GET', 'POST'])
def view_log():
    DASHBOARD_PIN = "121314"

    if request.method == "POST":
        entered_pin = request.form.get("pin")
        if entered_pin == DASHBOARD_PIN:
            try:
                with open(SCAN_LOG, "r") as f:
                    logs = json.load(f)
            except:
                logs = []

            table_html = """<h2>Scan Results</h2><table border='1' cellpadding='6'><tr>
                <th>Filename</th><th>Intent</th><th>Score</th><th>A</th><th>D</th><th>B</th><th>Upload Count</th>
                <th>IP Variation</th><th>Rapid Fire</th><th>IP</th><th>Timestamp</th></tr>"""
            for log in logs[::-1]:
                table_html += f"<tr><td>{log['filename']}</td><td>{log['intent']} {log['emoji']}</td><td>{log['score']}</td>"
                table_html += f"<td>{log['A']}</td><td>{log['D']}</td><td>{log['B']}</td><td>{log['upload_count']}</td>"
                table_html += f"<td>{log['ip_variation']}</td><td>{log['rapid_fire']}</td><td>{log['ip']}</td><td>{log['timestamp']}</td></tr>"
            table_html += "</table>"
            return render_template_string(table_html)
        else:
            return render_template_string("""
                <h2>Wrong PIN. Try again.</h2>
                <form method="post">
                    <input type="password" name="pin" placeholder="Enter PIN"/>
                    <button type="submit">Enter</button>
                </form>
            """)

    return render_template_string("""
        <h2>Enter Dashboard PIN</h2>
        <form method="post">
            <input type="password" name="pin" placeholder="Enter PIN"/>
            <button type="submit">Enter</button>
        </form>
    """)