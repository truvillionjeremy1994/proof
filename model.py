import torch.nn as nn
import torchvision.models as models

class ProofModel(nn.Module):
    def __init__(self):
        super(ProofModel, self).__init__()
        self.base = models.resnet18(pretrained=True)
        self.base.fc = nn.Linear(self.base.fc.in_features, 1)

    def forward(self, x):
        return self.base(x)