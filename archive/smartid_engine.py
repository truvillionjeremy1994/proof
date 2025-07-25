import cv2
import numpy as np
import mediapipe as mp
import exifread
from tensorflow.keras.models import load_model

model = load_model("smartid_model.h5")

# Subscore Functions
def get_depth_score(path):
    gray = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F).var()
    if lap > 300:
        return 95, "Sharp depth with background contrast"
    elif lap > 150:
        return 80, "Some depth variation"
    else:
        return 60, "Flat or overly smooth — possibly spoofed"

def get_lighting_score(path):
    hsv = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2HSV)
    std_dev = np.std(hsv[:, :, 2])
    if std_dev > 50:
        return 95, "Even, natural lighting"
    elif std_dev > 30:
        return 80, "Some lighting variation"
    else:
        return 60, "Flat or artificial lighting"

def get_texture_score(path):
    gray = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if lap_var > 200:
        return 95, "Crisp texture with edge detail"
    elif lap_var > 100:
        return 80, "Moderate sharpness"
    else:
        return 60, "Low texture detail"

def get_metadata_score(path):
    try:
        with open(path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag="DateTimeOriginal")
            if tags.get("EXIF DateTimeOriginal"):
                return 98, "Timestamp + EXIF match"
            elif tags:
                return 70, "EXIF found but no timestamp"
            else:
                return 40, "No metadata — may be manipulated"
    except:
        return 30, "No metadata or unreadable"

def get_motion_score(path):
    return 75, "Motion detection placeholder — adjust if needed"

# Core Analysis Function
def analyze_image(image_path):
    subscores = {}

    subscores['depth'], depth_msg = get_depth_score(image_path)
    subscores['lighting'], lighting_msg = get_lighting_score(image_path)
    subscores['texture'], texture_msg = get_texture_score(image_path)
    subscores['motion'], motion_msg = get_motion_score(image_path)
    subscores['metadata'], metadata_msg = get_metadata_score(image_path)

    # Blended score calculation
    blended_score = (
        0.25 * subscores['depth'] +
        0.25 * subscores['lighting'] +
        0.2  * subscores['texture'] +
        0.15 * subscores['motion'] +
        0.15 * subscores['metadata']
    )

    # Penalty logic
    if subscores['motion'] < 45 and subscores['metadata'] < 60:
        blended_score = max(0, blended_score - 15)

    # Verdict
    if blended_score >= 90:
        verdict = "✅ Live Photo"
    elif blended_score >= 70:
        verdict = "⚠️ Uncertain"
    else:
        verdict = "❌ Spoofed"

    # Subscore breakdown for UI/log
    breakdown = {
        "Depth": f"{subscores['depth']}% — {depth_msg}",
        "Lighting": f"{subscores['lighting']}% — {lighting_msg}",
        "Texture": f"{subscores['texture']}% — {texture_msg}",
        "Motion": f"{subscores['motion']}% — {motion_msg}",
        "Metadata": f"{subscores['metadata']}% — {metadata_msg}"
    }

    return round(blended_score, 2), verdict, breakdown