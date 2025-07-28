
import os
import json
import hashlib
import difflib
import datetime
from PIL import Image
import piexif
import imagehash
import cv2
import numpy as np
from sklearn.cluster import KMeans

# === Globals ===
PREVIOUS_UPLOADS = []
CLUSTER_CACHE = []

# === Hashing ===
def hash_string(s):
    return hashlib.sha256(s.encode()).hexdigest()

def perceptual_hash(image_path):
    with Image.open(image_path) as img:
        return str(imagehash.phash(img))

# === EXIF and Image Metrics ===
def extract_exif(image_path):
    try:
        exif = piexif.load(image_path)
        make = exif["0th"].get(piexif.ImageIFD.Make, b'').decode(errors="ignore")
        model = exif["0th"].get(piexif.ImageIFD.Model, b'').decode(errors="ignore")
        datetime_original = exif["Exif"].get(piexif.ExifIFD.DateTimeOriginal, b'').decode(errors="ignore")
        return {
            "camera_make": make,
            "camera_model": model,
            "timestamp_exif": datetime_original
        }
    except Exception:
        return {}

def compute_texture_score(image_path):
    try:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        return float(np.var(cv2.Laplacian(image, cv2.CV_64F)))
    except Exception:
        return 0.0

def compute_lighting_score(image_path):
    try:
        image = cv2.imread(image_path)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        brightness = hsv[..., 2].mean()
        return float(brightness / 255.0)
    except Exception:
        return 0.0

def compute_image_dimensions(image_path):
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception:
        return (0, 0)

# === Filename & Reupload Pattern Analysis ===
def get_filename_similarity(name1, name2):
    return difflib.SequenceMatcher(None, name1, name2).ratio()

# === JSON Logger ===
def log_json(filepath, entry):
    data = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    data.append(entry)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# === Clustering ID (based on pattern fingerprint) ===
def generate_cluster_id(features):
    feature_str = json.dumps(features, sort_keys=True)
    return hashlib.sha256(feature_str.encode()).hexdigest()[:8]

# === Upload Log — Digital Artifact Forensics ===
def log_signal_event(filepath, filename, image_path, request_meta, session_meta, prior_filenames):
    now = datetime.datetime.utcnow()
    width, height = compute_image_dimensions(image_path)
    aspect_ratio = round(width / height, 3) if height > 0 else 0.0
    exif_data = extract_exif(image_path)
    tex_score = compute_texture_score(image_path)
    light_score = compute_lighting_score(image_path)
    hash_phash = perceptual_hash(image_path)
    file_size_kb = os.path.getsize(image_path) // 1024 if os.path.exists(image_path) else 0
    reupload_count = sum([1 for name in prior_filenames if get_filename_similarity(filename, name) > 0.85])
    filename_similarity = round(sum(get_filename_similarity(filename, f) for f in prior_filenames) / len(prior_filenames), 3) if prior_filenames else 0.0

    cluster_features = {
        "texture": tex_score,
        "lighting": light_score,
        "aspect_ratio": aspect_ratio,
        "upload_hour": now.hour,
        "filename_similarity": filename_similarity
    }
    cluster_id = generate_cluster_id(cluster_features)

    log_entry = {
        "event": "initial_upload",
        "filename": filename,
        "timestamp": now.isoformat(),
        "session_id": session_meta.get("session_id"),
        "ip_hash": hash_string(request_meta.get("ip")),
        "user_agent_hash": hash_string(request_meta.get("user_agent")),
        "upload_hour": now.hour,
        "cluster_id": cluster_id,
        "behavior_outcome": "unknown",
        "image": {
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "texture_score": tex_score,
            "lighting_score": light_score,
            "image_hash": hash_phash,
            "file_size_kb": file_size_kb
        },
        "exif": exif_data,
        "behavioral_signals": {
            "reupload_count": reupload_count,
            "filename_similarity_avg": filename_similarity
        }
    }

    PREVIOUS_UPLOADS.append(filename)
    log_json(filepath, log_entry)

# === Tap Log — Human Intent Signal ===
def log_click_event(filepath, filename, score_before, score_after, request_meta, session_meta):
    now = datetime.datetime.utcnow()
    delta = round(score_after - score_before, 2)

    log_entry = {
        "event": "confidence_tap",
        "filename": filename,
        "timestamp": now.isoformat(),
        "session_id": session_meta.get("session_id"),
        "ip_hash": hash_string(request_meta.get("ip")),
        "user_agent_hash": hash_string(request_meta.get("user_agent")),
        "score_before": score_before,
        "score_after": score_after,
        "delta": delta,
        "upload_hour": now.hour,
        "tap_count": session_meta.get("tap_count", 1)
    }

    log_json(filepath, log_entry)
    session_meta["tap_count"] = session_meta.get("tap_count", 1) + 1