import json, hashlib

def hash_file_name(filename):
    return hashlib.sha256(filename.encode()).hexdigest()

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load {path}: {e}")
        return []

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def merge_logs(scan_path, false_path, output_path):
    scans = load_json(scan_path)
    false_flags = load_json(false_path)

    # Index false flags by filename
    flag_map = {entry["filename"]: entry for entry in false_flags}

    training_data = []

    for scan in scans:
        entry = {}

        # Basic metadata
        entry["filename"] = scan.get("filename")
        entry["timestamp"] = scan.get("timestamp")
        entry["ip"] = scan.get("ip", "127.0.0.1")
        entry["score"] = scan.get("score")
        entry["original_intent"] = scan.get("intent")
        entry["reason"] = scan.get("reason")
        entry["emoji"] = scan.get("emoji")

        # Internal pattern scores
        entry["A"] = scan.get("A")
        entry["D"] = scan.get("D")
        entry["B"] = scan.get("B")

        # Upload/session behavior
        entry["upload_count"] = scan.get("upload_count", 1)
        entry["ip_variation"] = scan.get("ip_variation", False)
        entry["rapid_fire"] = scan.get("rapid_fire", False)
        entry["session_id"] = scan.get("session_id", "unknown")

        # Manual override from user flag
        if entry["filename"] in flag_map:
            flag = flag_map[entry["filename"]]
            entry["user_flag"] = flag["user_flag"]
            entry["ground_truth"] = flag["user_flag"]  # This becomes gold label
            entry["label_source"] = "user_override"
        else:
            entry["user_flag"] = None
            entry["ground_truth"] = "Honest" if "Honest" in entry["original_intent"] else "Deceptive" if "Deceptive" in entry["original_intent"] else "Uncertain"
            entry["label_source"] = "auto"

        # Optional default — can change per case later
        entry["artifact_type"] = "unknown"  # you can tag these later: selfie, document, screenshot, etc.

        # Placeholder for social signal structure
        entry["social_signals"] = {
            "repost_footprint": None,
            "caption_mismatch": None,
            "bot_velocity": None,
            "over_optimized_style": None,
            "event_timing": None
        }

        # File hash for uniqueness
        entry["sha256"] = hash_file_name(entry["filename"])

        training_data.append(entry)

    save_json(output_path, training_data)
    print(f"✅ Done. Final training set saved to {output_path}")

# === Run it ===
merge_logs(
    scan_path="scan_results.json",
    false_path="false_log.json",
    output_path="proof_training_data.json"
)