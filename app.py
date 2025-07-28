from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import os, random
from datetime import datetime
from werkzeug.utils import secure_filename
from logger import log_signal_event, log_click_event, PREVIOUS_UPLOADS

app = Flask(__name__)
app.secret_key = "proof_secret_key"

UPLOAD_FOLDER = 'uploads'
SIGNAL_LOG_FILE = 'signal_log.json'
CLICK_LOG_FILE = 'click_log.json'
COUNTER_FILE = 'upload_count.txt'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Upload Counter ===
def increment_upload_count():
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'w') as f:
            f.write("0")
    with open(COUNTER_FILE, 'r+') as f:
        count = int(f.read().strip())
        count += 1
        f.seek(0)
        f.write(str(count))
        f.truncate()
    return count

def get_upload_count():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as f:
            return int(f.read().strip())
    return 0

def generate_session_id():
    raw = f"{request.remote_addr}_{datetime.utcnow().isoformat()}"
    return os.urandom(4).hex()

# === Homepage ===
@app.route('/')
def index():
    upload_count = get_upload_count()
    return render_template('index.html', upload_count=upload_count)

# === Cleanup after scan or refresh ===
@app.route('/cleanup', methods=['GET', 'POST'])
def cleanup():
    filename = session.pop('filename', None)
    if filename:
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, filename))
        except Exception:
            pass
    return redirect(url_for('index'))

# === Upload + Signal Boost ===
@app.route('/upload', methods=['POST', 'GET'])
def upload():
    filename = session.get('filename')
    base_score = session.get('base_score')
    boosted_score = session.get('boosted_score')
    boost_delta = None

    # === New Upload ===
    if request.method == 'POST':
        file = request.files['image']
        if not file:
            return redirect(url_for('index'))

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        increment_upload_count()
        session_id = generate_session_id()
        base_score = round(random.uniform(55.0, 85.0), 2)

        session['session_id'] = session_id
        session['base_score'] = base_score
        session['boosted_score'] = base_score
        session['display_score'] = base_score
        session['filename'] = filename
        session['tap_boost_requested'] = False
        session['tap_count'] = 1

        log_signal_event(
            filepath=SIGNAL_LOG_FILE,
            filename=filename,
            image_path=filepath,
            request_meta={"ip": request.remote_addr, "user_agent": request.headers.get("User-Agent", "")},
            session_meta={"session_id": session_id},
            prior_filenames=PREVIOUS_UPLOADS
        )

        return redirect(url_for('upload'))

    # === Refresh protection: redirect if no image
    if request.method == 'GET' and not session.get('filename'):
        return redirect(url_for('cleanup'))

    # === Tap for more confidence
    if 'boost' in request.args:
        session['tap_boost_requested'] = True
        return redirect(url_for('upload'))

    # === Handle tap logic (always display upward, but log truth)
    if session.get('tap_boost_requested') == True:
        session['tap_boost_requested'] = False
        true_score_before = session.get("boosted_score")
        display_score = session.get("display_score", session.get("base_score", 0))

        # Replace this line later with actual ProofModel call:
        behavior_factor = random.uniform(1.01, 1.08)
        true_score_after = round(min(true_score_before * behavior_factor, 99.9), 2)

        # Only increase display score
        display_score = max(display_score, true_score_after)

        session['boosted_score'] = true_score_after
        session['display_score'] = display_score
        boost_delta = round(display_score - true_score_before, 2)

        log_click_event(
            filepath=CLICK_LOG_FILE,
            filename=session.get("filename"),
            score_before=true_score_before,
            score_after=true_score_after,
            request_meta={"ip": request.remote_addr, "user_agent": request.headers.get("User-Agent", "")},
            session_meta=session
        )

    # === Final Result Display
    score = session.get("display_score", base_score or 0)
    result = "honest" if score >= 80 else "deceptive"
    intent_label = "✅ Honest Photo" if result == "honest" else "❌ Deceptive Photo"

    meta = {
        "filename": filename,
        "timestamp": datetime.utcnow().isoformat(),
        "score": score,
        "verdict": result
    }

    return render_template(
        "result.html",
        score=score,
        intent_label=intent_label,
        result=result,
        meta=meta,
        boost_delta=boost_delta
    )

# === Serve Image (used for testing before deletion) ===
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# === Upload Count API ===
@app.route('/count')
def count_route():
    return f"Total uploads: {get_upload_count()}"

# === Run App ===
if __name__ == '__main__':
    app.run(debug=True)
