import os
import joblib
from PIL import Image
import numpy as np

# Load the trained model
model = joblib.load('smartid_model.pkl')

# Folder to batch verify
verify_folder = 'verify_me'

# Image preprocessor
def extract_features(image_path):
    img = Image.open(image_path).resize((64, 64)).convert('L')
    return np.array(img).flatten()

# Loop through all images
for file in os.listdir(verify_folder):
    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
        full_path = os.path.join(verify_folder, file)
        try:
            features = extract_features(full_path).reshape(1, -1)
            proba = model.predict_proba(features)[0]
            confidence = proba[1] * 100  # Probability of class 1 (REAL)
            
            if confidence >= 90:
                label = '✅ REAL'
            elif confidence >= 70:
                label = '⚠️ UNCERTAIN'
            else:
                label = '❌ SPOOF'
            
            print(f"{file} → {label} ({confidence:.1f}%)")
        
        except Exception as e:
            print(f"{file} → ⚠️ Error: {e}")