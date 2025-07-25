import json
import os

def guess_artifact_type(filename):
    name = filename.lower()

    if "selfie" in name or "face" in name:
        return "selfie"
    elif "id" in name or "passport" in name or "license" in name:
        return "photo_of_id"
    elif "screenshot" in name or "info" in name or "text" in name:
        return "text_screenshot"
    elif "scam" in name or "bait" in name:
        return "bait_test"
    elif "ai" in name or "fake" in name:
        return "ai_face"
    elif "profile" in name:
        return "profile_picture"
    elif "doc" in name or "form" in name:
        return "document_photo"
    elif "meme" in name:
        return "meme"
    else:
        return "unknown"

def auto_label_artifact_types(input_path, output_path):
    with open(input_path, 'r') as f:
        data = json.load(f)

    for entry in data:
        if entry.get("artifact_type", "unknown") == "unknown":
            filename = entry.get("filename", "")
            entry["artifact_type"] = guess_artifact_type(filename)

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Auto-labeling complete. Saved to {output_path}")

# === Run it ===
auto_label_artifact_types(
    input_path="proof_training_data.json",
    output_path="proof_training_data_labeled.json"
)