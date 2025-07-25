# scripts/augment_real_photos.py
from PIL import Image
import os
import torchvision.transforms as T

input_dir = "data/real"
output_dir = "data/real_augmented"
os.makedirs(output_dir, exist_ok=True)

transform = T.Compose([
    T.RandomRotation(10),
    T.RandomResizedCrop(224, scale=(0.8, 1.0)),
    T.ColorJitter(brightness=0.2, contrast=0.2),
    T.RandomHorizontalFlip(),
])

for img_file in os.listdir(input_dir):
    img_path = os.path.join(input_dir, img_file)
    img = Image.open(img_path).convert("RGB")
    for i in range(3):  # Generate 3 augmentations per photo
        aug = transform(img)
        aug.save(f"{output_dir}/{img_file.replace('.jpg','')}_aug{i}.jpg")

print("✅ Real photo augmentations saved.")