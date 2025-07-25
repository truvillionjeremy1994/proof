import os
import json
import shutil

# === CONFIG ===
UPLOADS_DIR = "uploads"
SORTED_DIR = "sorted"
RESULTS_JSON = "results.json"
LOG_FILE = "sort_log.json"

# Create intent folder based on score
def get_intent_label(score):
    if score >= 80:
        return "Honest_Intent"
    elif score >= 60:
        return "Uncertain_Intent"
    else:
        return "Deceptive_Intent"

# Ensure destination folders exist
def ensure_folders(base_dir):
    for folder in ["Honest_Intent", "Uncertain_Intent", "Deceptive_Intent"]:
        os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

# Main sorting logic
def sort_images():
    ensure_folders(SORTED_DIR)

    try:
        with open(RESULTS_JSON, "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"Missing file: {RESULTS_JSON}")
        return

    log_entries = []
    for item in results:
        filename = item.get("filename")
        score = item.get("result_score") or item.get("score")
        if not filename or score is None:
            continue

        intent_label = get_intent_label(score)
        src = os.path.join(UPLOADS_DIR, filename)
        dest = os.path.join(SORTED_DIR, intent_label, filename)

        if os.path.exists(src):
            shutil.copy2(src, dest)
            status = "sorted"
        else:
            status = "missing"

        log_entries.append({
            "filename": filename,
            "score": score,
            "intent": intent_label,
            "status": status
        })

    with open(LOG_FILE, "w") as f:
        json.dump(log_entries, f, indent=2)

if __name__ == "__main__":
    sort_images()