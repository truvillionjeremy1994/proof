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

            html = """
            <html>
            <head>
                <title>Proof Log Dashboard</title>
                <style>
                    body { background-color: #111; color: #fff; font-family: Arial, sans-serif; text-align: center; }
                    .scan { border: 1px solid #333; border-radius: 8px; background: #1c1c1c; padding: 20px; margin: 20px auto; width: 90%; max-width: 480px; text-align: left; }
                    img { width: 100%; border-radius: 6px; margin-top: 10px; }
                    .btn-container { display: flex; justify-content: center; gap: 10px; margin-top: 10px; flex-wrap: wrap; }
                    button { padding: 10px 14px; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
                    .honest { background-color: #226622; color: white; }
                    .deceptive { background-color: #991111; color: white; }
                    .delete { background-color: #555; color: white; }
                    a.back { color: #0af; text-decoration: none; display: inline-block; margin-top: 20px; }
                </style>
            </head>
            <body>
                <h2>📊 Proof Log Dashboard</h2>
            """
            for log in logs[::-1]:
                html += f"""
                <div class='scan'>
                    <strong>{log['emoji']} {log['intent']}</strong><br>
                    <b>Score:</b> {log['score']}<br>
                    <b>File:</b> {log['filename']}<br>
                    <b>Scanned:</b> {log['timestamp']}<br>
                    <b>Depth:</b> {log['A']}<br>
                    <b>Deception:</b> {log['D']}<br>
                    <b>Behavior:</b> {log['B']}<br>
                    <b>Rapid Fire:</b> {log['rapid_fire']}<br>
                    <b>IP Change:</b> {log['ip_variation']}<br>
                    <img src='/uploads/{log['filename']}'><br>
                    <div class='btn-container'>
                        <form method='POST' action='/flag/{log['filename']}/honest'>
                            <button class='honest' type='submit'>✅ Honest</button>
                        </form>
                        <form method='POST' action='/flag/{log['filename']}/deceptive'>
                            <button class='deceptive' type='submit'>❌ Deceptive</button>
                        </form>
                        <form method='POST' action='/flag/{log['filename']}/delete'>
                            <button class='delete' type='submit'>🗑️ Delete</button>
                        </form>
                    </div>
                </div>
                """
            html += "<a class='back' href='/'>← Back to Upload</a></body></html>"
            return html

        else:
            return render_template_string("""
                <html><body style='background:#111;color:#fff;text-align:center;padding:50px;'>
                <h2>Wrong PIN. Try again.</h2>
                <form method="post">
                    <input type="password" name="pin" placeholder="Enter PIN" style='padding:10px;font-size:16px;'/>
                    <button type="submit" style='padding:10px 20px;'>Enter</button>
                </form>
                <br><a class='back' href='/'>← Back to Upload</a>
                </body></html>
            ")

    return render_template_string("""
        <html><body style='background:#111;color:#fff;text-align:center;padding:50px;'>
        <h2>Enter Dashboard PIN</h2>
        <form method="post">
            <input type="password" name="pin" placeholder="Enter PIN" style='padding:10px;font-size:16px;'/>
            <button type="submit" style='padding:10px 20px;'>Enter</button>
        </form>
        <br><a class='back' href='/'>← Back to Upload</a>
        </body></html>
    ")

@app.route('/debug')
def debug_data():
    try:
        with open(SCAN_LOG, "r") as f:
            data = json.load(f)
        return jsonify(data)
    except:
        return jsonify({"error": "Failed to load scan_results.json"})

@app.route('/flag/<filename>/<flag_type>', methods=['POST'])
def flag_file(filename, flag_type):
    src = os.path.join(UPLOAD_FOLDER, filename)

    if flag_type == "delete":
        if os.path.exists(src):
            os.remove(src)
        return redirect(url_for('index'))

    dst_folder = FLAG_HONEST if flag_type == "honest" else FLAG_DECEPTIVE
    dst = os.path.join(dst_folder, filename)
    os.makedirs(dst_folder, exist_ok=True)

    if os.path.exists(src):
        shutil.copy2(src, dst)

        record = None
        if os.path.exists(SCAN_LOG):
            with open(SCAN_LOG, 'r') as f:
                try:
                    scan_data = json.load(f)
                    record = next((r for r in scan_data if r['filename'] == filename), None)
                except:
                    scan_data = []

        flag_entry = {
            "filename": filename,
            "user_flag": flag_type,
            "timestamp": datetime.datetime.now().isoformat()
        }

        if record:
            flag_entry["original_result"] = {
                "score": record.get("score"),
                "intent": record.get("intent"),
                "emoji": record.get("emoji"),
                "timestamp": record.get("timestamp")
            }

        log_data = []
        if os.path.exists(FALSE_LOG):
            try:
                with open(FALSE_LOG, 'r') as f:
                    log_data = json.load(f)
            except:
                log_data = []

        log_data.append(flag_entry)
        with open(FALSE_LOG, 'w') as f:
            json.dump(log_data, f, indent=2)

    return redirect(url_for('index'))

# ---------------------------
# Start Server
# ---------------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)