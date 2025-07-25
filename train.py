import os
import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from torch import nn, optim
from model import ProofModel

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
        return image, label

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

dataset = ProofDataset(csv_file="labels.csv", root_dir="data", transform=transform)
train_set, val_set = train_test_split(dataset, test_size=0.2)
train_loader = DataLoader(train_set, batch_size=16, shuffle=True)
val_loader = DataLoader(val_set, batch_size=16)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ProofModel().to(device)
criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(model.parameters(), lr=0.0003)

for epoch in range(10):
    model.train()
    total_loss = 0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.float().to(device).unsqueeze(1)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"Epoch {epoch+1}, Loss: {total_loss:.4f}")

    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = torch.sigmoid(model(images)).squeeze()
            preds = (outputs > 0.5).int()
            correct += (preds == labels).sum().item()
            total += labels.size(0)
    print(f"Validation Accuracy: {correct / total:.2f}")

os.makedirs("checkpoints", exist_ok=True)
torch.save(model.state_dict(), "checkpoints/proof_model_v1_6.pth")
print("✅ Model saved to checkpoints/proof_model_v1_6.pth")