import torch
import numpy as np
from model import ProofModelV2  # MLP model with 5 input features

# === Load the trained model weights ===
def load_proof_model():
    model = ProofModelV2()
    model.load_state_dict(torch.load("proofmodel_v2.pth", map_location=torch.device("cpu")))
    model.eval()
    return model

proof_model = load_proof_model()

# === Run inference and return score (0–100) ===
def predict_confidence_score(features, model):
    """
    features = list of 5 floats:
        [texture_score, lighting_score, upload_hour, tap_count, score_drift]
    """
    tensor = torch.tensor(np.array(features), dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        output = model(tensor)
        score = float(output.item()) * 100
        return round(min(score, 99.9), 2)