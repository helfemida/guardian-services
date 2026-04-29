import argparse
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import precision_recall_fscore_support
from torchvision import models, transforms


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate checkpoint on folder with violence/non_violence images.")
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--data-root", type=str, required=True)
    parser.add_argument("--threshold", type=float, default=0.35)
    return parser.parse_args()


def build_model():
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 1)
    return model


def collect_images(data_root: Path):
    records = []
    for class_name, label in (("non_violence", 0), ("violence", 1)):
        class_dir = data_root / class_name
        if not class_dir.exists():
            continue
        for pattern in ("*.jpg", "*.jpeg", "*.png"):
            for p in class_dir.rglob(pattern):
                records.append((p, label))
    return records


def main():
    args = parse_args()
    data_root = Path(args.data_root)
    records = collect_images(data_root)
    if not records:
        raise RuntimeError(
            f"No images found in {data_root}. Expected subfolders: non_violence/ and violence/."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model().to(device)
    state = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(state)
    model.eval()

    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    labels = []
    probs = []
    with torch.no_grad():
        for image_path, label in records:
            image = Image.open(image_path).convert("RGB")
            x = transform(image).unsqueeze(0).to(device)
            logit = model(x).squeeze(1)
            prob = torch.sigmoid(logit).item()
            labels.append(label)
            probs.append(prob)

    preds = [1 if p >= args.threshold else 0 for p in probs]
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, labels=[1], average=None, zero_division=0
    )
    tp = sum(1 for y, p in zip(labels, preds) if y == 1 and p == 1)
    tn = sum(1 for y, p in zip(labels, preds) if y == 0 and p == 0)
    fp = sum(1 for y, p in zip(labels, preds) if y == 0 and p == 1)
    fn = sum(1 for y, p in zip(labels, preds) if y == 1 and p == 0)

    print(f"Samples: {len(records)}")
    print(f"Threshold: {args.threshold}")
    print(f"precision_violence: {float(precision[0]):.4f}")
    print(f"recall_violence: {float(recall[0]):.4f}")
    print(f"f1_violence: {float(f1[0]):.4f}")
    print(f"confusion: TP={tp} FP={fp} FN={fn} TN={tn}")


if __name__ == "__main__":
    main()
