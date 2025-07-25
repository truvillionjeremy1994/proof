# scripts/augment_spoof_photos.py
from PIL import Image
import os
import torchvision.transforms as T

input_dir = "data/spoof"
output_dir = "data/spoof_augmented"
os.makedirs(output_dir, exist_ok=True)

transform = T.Compose([
    T.GaussianBlur(3),
    T.RandomAffine(degrees=5, translate=(0.05, 0.05), scale=(0.95, 1.05)),
    T.RandomPerspective(distortion_scale=0.5, p=0.7),
])

for img_file in os.listdir(input_dir):
    img_path = os.path.join(input_dir, img_file)
    img = Image.open(img_path).convert("RGB")
    for i in range(3):
        aug = transform(img)
        aug.save(f"{output_dir}/{img_file.replace('.jpg','')}_aug{i}.jpg")

print("✅ Spoof photo augmentations saved.")