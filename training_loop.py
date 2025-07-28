import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import pandas as pd
from sklearn.model_selection import train_test_split
import numpy as np

CSV_FILE = "training_dataset.csv"
MODEL_OUTPUT = "proofmodel_v2.pth"
EPOCHS = 10
BATCH_SIZE = 32
LEARNING_RATE = 0.001

class ProofDataset(Dataset):
    def __init__(self, df):
        self.X = df[["texture", "lighting", "upload_hour", "tap_count", "score_drift"]].values.astype(np.float32)
        self.y = (df["label"] == "honest").astype(np.float32).values.reshape(-1, 1)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return torch.tensor(self.X[idx]), torch.tensor(self.y[idx])

class ProofModelV2(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(5, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)

df = pd.read_csv(CSV_FILE).dropna()
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

train_dataset = ProofDataset(train_df)
val_dataset = ProofDataset(val_df)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

model = ProofModelV2()
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

for epoch in range(EPOCHS):
    model.train()
    total_loss = 0
    for inputs, targets in train_loader:
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, targets in val_loader:
            outputs = model(inputs)
            preds = (outputs > 0.5).float()
            correct += (preds == targets).sum().item()
            total += targets.size(0)

    accuracy = 100 * correct / total
    print(f"Epoch {epoch+1}/{EPOCHS} — Loss: {total_loss:.4f} — Val Acc: {accuracy:.2f}%")

torch.save(model.state_dict(), MODEL_OUTPUT)
print(f"\n✅ ProofModel v2 saved to {MODEL_OUTPUT}")