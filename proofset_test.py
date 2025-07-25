import os
import torch
from torchvision import transforms, models
from PIL import Image, ExifTags
import torch.nn as nn
import numpy as np
import cv2
import json
from pillow_heif import register_heif_opener

# Enable .heic image support
register_heif_opener()

# --- Load image function (HEIC supported) ---
def load_image(path):
    return Image.open(path).convert('RGB')

# --- ProofModel architecture ---
class ProofModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.base = models.resnet18(pretrained=False)
        self.base.fc = nn.Linear(self.base.fc.in_features, 1)

    def forward(self, x):
        return self.base(x)

# Load model
model = ProofModel()
model.load_state_dict(torch.load('checkpoints/proof_model_v1_6.pth', map_location='cpu'))
model.eval()

# --- Preprocessing ---
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# --- Forensics scoring functions ---
def compute_depth_score(img_np):
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return min(100, max(0, laplacian_var / 2))

def compute_lighting_score(img_np):
    hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
    brightness = hsv[:, :, 2].mean()
    return min(100, max(0, 100 - abs(brightness - 128) * 0.8))

def compute_texture_score(img_np):
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return min(100, max(0, np.std(laplacian)))

def compute_metadata_score(image):
    try:
        exif = image._getexif()
        if exif is None:
            return 0
        keys = [ExifTags.TAGS.get(tag, tag) for tag in exif]
        count = sum(1 for tag in ['DateTime', 'Model', 'Make', 'ExifImageWidth'] if tag in keys)
        return (count / 4) * 100
    except:
        return 0

# --- Notes logic ---
def generate_notes(depth, lighting, texture, metadata):
    if metadata == 0 and depth > 80 and lighting > 80:
        return "No EXIF — likely screenshot or repost"
    elif texture < 25 and depth > 70:
        return "Low texture — filtered or smoothed face"
    elif depth < 30:
        return "Low sharpness — possibly spoofed or low-quality image"
    elif depth > 90 and lighting > 85 and texture > 80:
        return "High confidence — camera-taken photo"
    else:
        return "Mixed signals — manual review recommended"

# --- Folder + log setup ---
test_folder = 'data/proofset/'
log_file = 'scan_results.jsonl'

with open(log_file, 'a') as log:
    for file in os.listdir(test_folder):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.heic')):
            img_path = os.path.join(test_folder, file)
            image = load_image(img_path)
            img_tensor = transform(image).unsqueeze(0)

            with torch.no_grad():
                output = model(img_tensor)
                score = torch.sigmoid(output).item() * 100

            img_cv = np.array(image)

            depth = round(compute_depth_score(img_cv), 2)
            lighting = round(compute_lighting_score(img_cv), 2)
            texture = round(compute_texture_score(img_cv), 2)
            metadata = round(compute_metadata_score(image), 2)

            trust_score = round((depth * 0.3) + (lighting * 0.2) + (texture * 0.3) + (metadata * 0.2), 2)

            if score >= 90:
                verdict = "✅ REAL"
            elif score >= 70:
                verdict = "⚠️ UNCERTAIN"
            else:
                verdict = "❌ FAKE"

            notes = generate_notes(depth, lighting, texture, metadata)

            print(f"\n📸 {file}")
            print(f"→ RESULT: {score:.2f}% {verdict}")
            print(f"• Depth: {depth}% — 3D layering & sharpness")
            print(f"• Lighting: {lighting}% — Exposure & glare")
            print(f"• Texture: {texture}% — Detail & skin pores")
            print(f"• Metadata: {metadata}% — Timestamp, camera info")
            print(f"• Trust Score: {trust_score}%")
            print(f"• Notes: {notes}")

            log.write(json.dumps({
                "filename": file,
                "result_score": round(score, 2),
                "verdict": verdict.strip('✅❌⚠️ '),
                "depth": depth,
                "lighting": lighting,
                "texture": texture,
                "metadata": metadata,
                "trust_score": trust_score,
                "notes": notes
            }) + '\n')