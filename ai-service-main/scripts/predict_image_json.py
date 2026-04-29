import argparse
import json
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms


def build_model() -> nn.Module:
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 1)
    return model


def load_checkpoint(checkpoint_path: str, device: torch.device) -> nn.Module:
    model = build_model().to(device)
    state = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state)
    model.eval()
    return model


def predict_image_to_json(
    image_path: str,
    model: nn.Module,
    device: torch.device,
    threshold: float = 0.75,
) -> dict:
    preprocess = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    image = Image.open(image_path).convert("RGB")
    x = preprocess(image).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(x).squeeze(1)
        prob_violence = float(torch.sigmoid(logits).item())

    result = "violence" if prob_violence >= threshold else "non-violence"
    confidence = prob_violence if result == "violence" else (1.0 - prob_violence)

    return {
        "result": result,
        "confidence": round(confidence, 4),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Predict violence/non-violence from one image and return JSON.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to model .pt file")
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    parser.add_argument("--threshold", type=float, default=0.75, help="Decision threshold for violence class")
    return parser.parse_args()


def main():
    args = parse_args()
    image_path = Path(args.image)
    checkpoint_path = Path(args.checkpoint)

    if not checkpoint_path.exists():
        raise RuntimeError(f"Checkpoint not found: {checkpoint_path}")
    if not image_path.exists():
        raise RuntimeError(f"Image not found: {image_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_checkpoint(str(checkpoint_path), device)
    output = predict_image_to_json(str(image_path), model, device, threshold=args.threshold)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
