import sys
sys.path.append("..")

# benchmark.py
import os
import pandas as pd
import torch
from torchvision import transforms
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from model import ProofModel
from sklearn.metrics import classification_report, confusion_matrix

class ProofDataset(Dataset):
    def __init__(self, csv_file, root_dir, transform=None):
        self.data = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.transform = transform
        self.label_map = {"real": 1, "spoof": 0}

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        img_path = os.path.join(self.root_dir, row["filename"])
        image = Image.open(img_path).convert("RGB")
        label = self.label_map[row["label"]]
        if self.transform:
            image = self.transform(image)
        return image, label, row["filename"]

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

dataset = ProofDataset("labels.csv", "data", transform)
loader = DataLoader(dataset, batch_size=32)

model = ProofModel()
model.load_state_dict(torch.load("checkpoints/proof_model_v1_6.pth", map_location=torch.device('cpu')))
model.eval()

all_preds = []
all_labels = []
all_names = []

with torch.no_grad():
    for images, labels, filenames in loader:
        outputs = torch.sigmoid(model(images)).squeeze()
        preds = (outputs > 0.5).int()
        all_preds.extend(preds.tolist())
        all_labels.extend(labels.tolist())
        all_names.extend(filenames)

# Save predictions to CSV
results = pd.DataFrame({
    "filename": all_names,
    "label": all_labels,
    "predicted": all_preds
})
results.to_csv("benchmark_results.csv", index=False)

# Print metrics
print("\n--- Classification Report ---")
print(classification_report(all_labels, all_preds, target_names=["spoof", "real"]))
print("--- Confusion Matrix ---")
print(confusion_matrix(all_labels, all_preds))