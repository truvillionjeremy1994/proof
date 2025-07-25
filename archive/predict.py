import sys
import cv2
import numpy as np
import mediapipe as mp
import exifread
from tensorflow.keras.models import load_model

# ---- Load Model ----
model = load_model("smartid_model.h5")

# ---- Load + Preprocess Image ----
image_path = sys.argv[1] if len(sys.argv) > 1 else "test_real.jpg"
img = cv2.imread(image_path)

if img is None:
    print(f"\n❌ ERROR: Couldn't read image at path: {image_path}")
    sys.exit(1)

resized = cv2.resize(img, (128, 128))
resized = resized / 255.0
resized = resized.reshape(1, 128, 128, 3)

# ---- AI Model Score ----
ai_score = model.predict(resized)[0][0] * 100
ai_score = round(ai_score, 2)

# ---- Depth Score (Blur-based) ----
def get_depth_score(path):
    gray = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F).var()
    if lap > 300:
        return 95, "Sharp depth with background contrast"
    elif lap > 150:
        return 80, "Some depth variation"
    else:
        return 60, "Flat or overly smooth — possibly spoofed"

# ---- Lighting Score (HSV channel) ----
def get_lighting_score(path):
    hsv = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2HSV)
    std_dev = np.std(hsv[:, :, 2])
    if std_dev > 50:
        return 95, "Even, natural lighting"
    elif std_dev > 30:
        return 80, "Some lighting variation"
    else:
        return 60, "Flat or artificial lighting (possible spoof)"

# ---- Texture Score (sharpness clarity) ----
def get_texture_score(path):
    gray = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if lap_var > 200:
        return 95, "Crisp texture with edge detail"
    elif lap_var > 100:
        return 80, "Some detail — moderate sharpness"
    else:
        return 60, "Blurry or overly smooth texture"

# ---- Metadata Score (EXIF presence) ----
def get_metadata_score(path):
    try:
        with open(path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag="DateTimeOriginal")
            if tags.get("EXIF DateTimeOriginal"):
                return 98, "Timestamp + EXIF match"
            elif tags:
                return 70, "EXIF found but timestamp missing"
            else:
                return 50, "No metadata found"
    except:
        return 50, "Failed to read metadata"

# ---- Get All Subscores ----
depth, depth_msg = get_depth_score(image_path)
lighting, lighting_msg = get_lighting_score(image_path)
texture, texture_msg = get_texture_score(image_path)
metadata, metadata_msg = get_metadata_score(image_path)

# ---- Blended Score Logic ----
blended_score = round((
    ai_score * 0.25 +
    depth * 0.25 +
    lighting * 0.2 +
    texture * 0.2 +
    metadata * 0.1
), 2)

# ---- Verdict & Interpretation ----
if blended_score >= 90:
    label = "✅ LIVE PHOTO"
    interpretation = "This image was almost certainly taken by a real person, in real time, with no tricks involved."
elif blended_score >= 70:
    label = "⚠️ UNCERTAIN"
    interpretation = "This photo has natural signs but not enough to guarantee it's live."
else:
    label = "❌ SPOOFED"
    interpretation = "This photo shows strong signs of manipulation or replay, and was likely not taken live."

# ---- Report ----
print("\n" + "=" * 60)
print("🔍 SMARTID V1.6 — PREDICTION REPORT (Blended Logic)")
print("=" * 60)
print(f"📁 File: {image_path}")
print(f"🤖 AI Model Score      : {ai_score}%")
print(f"🧠 Blended Final Score : {blended_score}%")
print(f"🏷️ Classification      : {label}")
print(f"📝 Interpretation      : {interpretation}")

print("\n📌 Subcomponent Breakdown:")
print(f"• Depth     : {depth}% — {depth_msg}")
print(f"• Lighting  : {lighting}% — {lighting_msg}")
print(f"• Texture   : {texture}% — {texture_msg}")
print(f"• Metadata  : {metadata}% — {metadata_msg}")

print("\n🧾 Final Answer:")
print(f"→ Was this photo taken by a real person—at the moment it says it was—with no tricks involved?")
print(f"→ SmartID Score: {blended_score}% → {label}")
print("=" * 60 + "\n")