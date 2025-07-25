from flask import Flask, render_template, request, url_for
import os
import joblib
from PIL import Image
import numpy as np
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Load your SmartID model
model = joblib.load('smartid_model.pkl')

# Updated folder path to work with Flask's static directory
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_features(image_path):
    img = Image.open(image_path).resize((64, 64)).convert('L')
    return np.array(img).flatten()

@app.route('/', methods=['GET', 'POST'])
def index():
    label = None
    confidence = None
    filename = None

    if request.method == 'POST':
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Extract features and make prediction
            features = extract_features(filepath).reshape(1, -1)
            proba = model.predict_proba(features)[0]
            confidence = round(proba[1] * 100, 2)

            if confidence >= 90:
                label = '✅ REAL'
            elif confidence >= 70:
                label = '⚠️ UNCERTAIN'
            else:
                label = '❌ SPOOF'

    return render_template('index.html', label=label, confidence=confidence, filename=f"uploads/{filename}" if filename else None)

if __name__ == '__main__':
    app.run(debug=True)