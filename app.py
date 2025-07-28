from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import os, random, base64
from datetime import datetime
from werkzeug.utils import secure_filename
from logger import log_signal_event, log_click_event, compute_texture_score, compute_lighting_score, PREVIOUS_UPLOADS
from model_loader import proof_model, predict_confidence_score

app = Flask(__name__)
app.secret_key = "proof_secret_key"

UPLOAD_FOLDER = 'uploads'
SIGNAL_LOG_FILE = 'signal_log.json'
CLICK_LOG_FILE = 'click_log.json'
COUNTER_FILE = 'upload_count.txt'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def encode_image_base64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

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

@app.route('/')
def index():
    upload_count = get_upload_count()
    return render_template('index.html', upload_count=upload_count)

@app.route('/cleanup', methods=['GET', 'POST'])
def cleanup():
    filename = session.pop('filename', None)
    if filename:
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, filename))
        except Exception:
            pass
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    filename = session.get('filename')
    base_score = session.get('base_score')
    boosted_score = session.get('boosted_score')
    boost_delta = None

    if request.method == 'POST':
        file = request.files['image']
        if not file:
            return redirect(url_for('index'))

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        increment_upload_count()
        session_id = generate_session_id()

        tex = compute_texture_score(filepath)
        light = compute_lighting_score(filepath)
        hour = datetime.utcnow().hour
        tap = 1
        drift = 0.0

        base_score = predict_confidence_score([tex, light, hour, tap, drift], proof_model)

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

    if request.method == 'GET' and not session.get('filename'):
        return redirect(url_for('cleanup'))

    if 'boost' in request.args:
        session['tap_boost_requested'] = True
        return redirect(url_for('upload'))

    if session.get('tap_boost_requested') == True:
        session['tap_boost_requested'] = False
        true_score_before = session.get("boosted_score")
        display_score = session.get("display_score", session.get("base_score", 0))

        filepath = os.path.join(UPLOAD_FOLDER, session.get("filename"))

        tex = compute_texture_score(filepath)
        light = compute_lighting_score(filepath)
        hour = datetime.utcnow().hour
        tap = session.get("tap_count", 1)
        drift = display_score - session.get("base_score", 0)

        true_score_after = predict_confidence_score([tex, light, hour, tap, drift], proof_model)

        display_score = max(display_score, true_score_after)
        session['boosted_score'] = true_score_after
        session['display_score'] = display_score
        session['tap_count'] = tap + 1
        boost_delta = round(display_score - true_score_before, 2)

        log_click_event(
            filepath=CLICK_LOG_FILE,
            filename=session.get("filename"),
            score_before=true_score_before,
            score_after=true_score_after,
            request_meta={"ip": request.remote_addr, "user_agent": request.headers.get("User-Agent", "")},
            session_meta=session
        )

    score = session.get("display_score", base_score or 0)
    result = "honest" if score >= 80 else "deceptive"
    intent_label = "✅ Honest Photo" if result == "honest" else "❌ Deceptive Photo"

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    base64_image = encode_image_base64(filepath)

    try:
        os.remove(filepath)
        session['filename'] = None
    except Exception:
        pass

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
        boost_delta=boost_delta,
        base64_image=base64_image
    )

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/count')
def count_route():
    return f"Total uploads: {get_upload_count()}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)