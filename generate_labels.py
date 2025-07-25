import os
import csv

# Customize these paths if needed
input_folder = "uploads"
output_csv = "labels.csv"

# Set your label rule here
def label_from_filename(filename):
    filename_lower = filename.lower()
    if "real" in filename_lower:
        return "real"
    elif "spoof" in filename_lower or "fake" in filename_lower:
        return "spoof"
    else:
        return "unknown"

# Scan the upload directory
files = [f for f in os.listdir(input_folder) if f.lower().endswith((".jpg", ".jpeg", ".png", ".heic"))]

# Generate label CSV
with open(output_csv, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["filename", "label"])
    for file in files:
        label = label_from_filename(file)
        writer.writerow([file, label])

print(f"✅ Done. {len(files)} labels written to {output_csv}")