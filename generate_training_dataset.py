import json
import csv
import os

# === Config
SIGNAL_LOG_FILE = "signal_log.json"
CLICK_LOG_FILE = "click_log.json"
OUTPUT_CSV = "training_dataset.csv"

# === Load both logs
with open(SIGNAL_LOG_FILE, "r") as f:
    signal_data = json.load(f)

with open(CLICK_LOG_FILE, "r") as f:
    click_data = json.load(f)

# === Index clicks by session_id
click_index = {}
for entry in click_data:
    sid = entry.get("session_id")
    if sid not in click_index:
        click_index[sid] = []
    click_index[sid].append(entry)

# === Build training rows
rows = []
for entry in signal_data:
    sid = entry.get("session_id")
    image = entry.get("image", {})
    behavior = entry.get("behavior_outcome", "unknown")
    final_score = entry.get("final_score", entry.get("score", 0))
    score_drift = entry.get("score_drift", 0)

    # Behavior to label
    if behavior in ["trusted_first_try", "doubted_then_trusted"]:
        label = "honest"
    elif behavior in ["manipulated", "never_trusted"]:
        label = "deceptive"
    else:
        label = "unknown"

    tap_count = 0
    if sid in click_index:
        tap_count = max(c.get("tap_count", 1) for c in click_index[sid])
        final_score = click_index[sid][-1].get("score_after", final_score)
        score_drift = round(final_score - entry.get("score", 0), 2)

    rows.append({
        "session_id": sid,
        "image_hash": image.get("image_hash"),
        "texture": image.get("texture_score"),
        "lighting": image.get("lighting_score"),
        "upload_hour": entry.get("upload_hour"),
        "tap_count": tap_count,
        "score_drift": score_drift,
        "final_score": final_score,
        "behavior_outcome": behavior,
        "label": label
    })

# === Write CSV
with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ training_dataset.csv saved with {len(rows)} rows.")
