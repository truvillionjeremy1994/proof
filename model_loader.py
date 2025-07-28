import torch
from model import ProofModel  # or ProofModelV2 if that's the class name you're using
from PIL import Image
from torchvision import transforms

# === Load the trained model weights ===
def load_proof_model():
    model = ProofModel()  # If your class is called ProofModelV2, update this
    model.load_state_dict(torch.load("proofmodel_v2.pth", map_location=torch.device("cpu")))
    model.eval()
    return model

proof_model = load_proof_model()

# === Run inference and return score (0–100) ===
def predict_confidence_score(image_path, model):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])
    image = Image.open(image_path).convert("RGB")
    tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        output = model(tensor)
        score = float(output.item()) * 100  # convert to 0–100%
        return round(min(score, 99.9), 2)