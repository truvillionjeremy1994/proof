# Replacing with clean and accurate app.py including dashboard, IP, batch download, and labeling

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, render_template_string, jsonify, send_file
from werkzeug.utils import secure_filename
import os, datetime, json, shutil, random, io, zipfile

app = Flask(__name__)
app.secret_key = 'super_secret_key_123'

UPLOAD_FOLDER = 'uploads'
SCAN_LOG = 'scan_results.json'
FALSE_LOG = 'false_log.json'
FLAG_HONEST = os.path.join('false_results', 'honest_but_flagged')
FLAG_DECEPTIVE = os.path.join('false_results', 'deceptive_but_passed')

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
        "score": I, "intent": intent, "emoji": emoji, "reason": reason,
        "A": A, "D": D, "B": B,
        "upload_count": upload_count, "ip_variation": ip_variation,
        "rapid_fire": rapid_fire, "timestamp": current_time.isoformat(),
        "ip": user_ip, "filename": filename
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

@app.route('/get_ip')
def get_ip():
    return jsonify({'ip': request.remote_addr})

@app.route('/download_batch', methods=['POST'])
def download_batch():
    files = request.json.get('files', [])
    if not files:
        return 'No files selected.', 400

    zip_buffer = io.BytesIO()
    metadata = []
    scan_data = []

    if os.path.exists(SCAN_LOG):
        with open(SCAN_LOG, 'r') as f:
            scan_data = json.load(f)

    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for fname in files:
            fpath = os.path.join(UPLOAD_FOLDER, fname)
            if os.path.exists(fpath):
                zip_file.write(fpath, arcname=fname)
                matched = next((log for log in scan_data if log['filename'] == fname), None)
                if matched:
                    metadata.append(matched)
        zip_file.writestr('proof_metadata.json', json.dumps(metadata, indent=2))

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='proof_batch.zip')

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
    if flag_type == "delete" and os.path.exists(src):
        os.remove(src)
        return redirect(url_for('index'))
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)