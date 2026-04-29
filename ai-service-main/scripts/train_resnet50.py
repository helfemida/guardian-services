import argparse
import copy
import json
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import models, transforms


class FramesDataset(Dataset):
    def __init__(self, records, transform):
        self.records = records
        self.transform = transform

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        image_path, label, _group = self.records[idx]
        image = Image.open(image_path).convert("RGB")
        image = self.transform(image)
        return image, torch.tensor(label, dtype=torch.float32)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def build_model() -> nn.Module:
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, 1)
    return model


def collect_records(split_root: Path):
    records = []
    image_patterns = ("*.jpg", "*.jpeg", "*.png")
    for split in ("train", "val", "test"):
        for label_name, label_idx in (("non_violence", 0), ("violence", 1)):
            folder = split_root / split / label_name
            if not folder.exists():
                continue
            for pattern in image_patterns:
                for image_path in folder.rglob(pattern):
                    group = image_path.stem.split("_f")[0]
                    records.append((str(image_path), label_idx, group, split))
    return records


def split_train_eval(records, use_test=False):
    train_records = [(p, y, g) for p, y, g, s in records if s == "train"]
    eval_split = "test" if use_test else "val"
    eval_records = [(p, y, g) for p, y, g, s in records if s == eval_split]
    if not train_records:
        raise RuntimeError("Train split is empty. Add files to train/non_violence and train/violence.")
    if not eval_records:
        raise RuntimeError(f"{eval_split} split is empty. Add files to {eval_split}/non_violence and {eval_split}/violence.")
    return train_records, eval_records


def make_loaders(train_records, val_records, batch_size):
    train_transform = transforms.Compose(
        [
            transforms.Resize((256, 256)),
            transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1, hue=0.02),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    eval_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    train_ds = FramesDataset(train_records, train_transform)
    val_ds = FramesDataset(val_records, eval_transform)

    labels = np.array([label for _, label, _ in train_records])
    class_counts = np.bincount(labels, minlength=2)
    if class_counts[0] == 0 or class_counts[1] == 0:
        raise RuntimeError(
            "Both classes must be present in train split. "
            f"Found non_violence={int(class_counts[0])}, violence={int(class_counts[1])}."
        )
    class_weights = 1.0 / np.maximum(class_counts, 1)
    sample_weights = class_weights[labels]
    sampler = WeightedRandomSampler(
        weights=torch.as_tensor(sample_weights, dtype=torch.double),
        num_samples=len(sample_weights),
        replacement=True,
    )

    pin_memory = torch.cuda.is_available()
    train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler, num_workers=2, pin_memory=pin_memory)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=pin_memory)

    pos_weight = torch.tensor([class_counts[0] / max(class_counts[1], 1)], dtype=torch.float32)
    return train_loader, val_loader, pos_weight


def evaluate(model, loader, device, threshold=0.35):
    model.eval()
    probs = []
    labels = []
    with torch.no_grad():
        for images, targets in loader:
            images = images.to(device, non_blocking=True)
            logits = model(images).squeeze(1)
            batch_probs = torch.sigmoid(logits).cpu().numpy().tolist()
            probs.extend(batch_probs)
            labels.extend(targets.numpy().astype(int).tolist())

    if not labels:
        raise RuntimeError("Evaluation split has no samples. Cannot compute metrics.")
    preds = [1 if p >= threshold else 0 for p in probs]
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, labels=[1], average=None, zero_division=0
    )
    return {
        "precision_violence": float(precision[0]),
        "recall_violence": float(recall[0]),
        "f1_violence": float(f1[0]),
    }


def train_once(train_records, val_records, args, fold_name="single"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if not train_records:
        raise RuntimeError("No training records found.")
    if not val_records:
        raise RuntimeError("No validation records found.")
    train_loader, val_loader, pos_weight = make_loaders(train_records, val_records, args.batch_size)
    model = build_model().to(device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight.to(device))
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)

    best_metric = -1.0
    best_state = copy.deepcopy(model.state_dict())
    best_epoch = 0
    epochs_without_improve = 0

    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        for images, targets in train_loader:
            images = images.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)
            logits = model(images).squeeze(1)
            loss = criterion(logits, targets)
            loss.backward()
            optimizer.step()
            running_loss += float(loss.item())

        metrics = evaluate(model, val_loader, device, threshold=args.threshold)
        recall = metrics["recall_violence"]
        print(
            f"[{fold_name}] epoch={epoch + 1}/{args.epochs} "
            f"loss={running_loss / max(len(train_loader), 1):.4f} "
            f"recall={recall:.4f} precision={metrics['precision_violence']:.4f}"
        )
        if recall > (best_metric + args.early_stopping_min_delta):
            best_metric = recall
            best_state = copy.deepcopy(model.state_dict())
            best_epoch = epoch + 1
            epochs_without_improve = 0
        else:
            epochs_without_improve += 1

        if (epoch + 1) >= args.min_epochs and epochs_without_improve >= args.early_stopping_patience:
            print(
                f"[{fold_name}] early stopping at epoch {epoch + 1} "
                f"(best_epoch={best_epoch}, best_recall={best_metric:.4f})"
            )
            break

    model.load_state_dict(best_state)
    final_metrics = evaluate(model, val_loader, device, threshold=args.threshold)
    return model, final_metrics


def run_cross_validate(all_records, args):
    trainval = [(p, y, g) for p, y, g, s in all_records if s in ("train", "val")]
    if not trainval:
        raise RuntimeError("No train/val records found for cross-validation.")
    X = np.array([r[0] for r in trainval])
    y = np.array([r[1] for r in trainval])
    groups = np.array([r[2] for r in trainval])
    class_counts = np.bincount(y, minlength=2)
    min_class_size = int(class_counts.min()) if class_counts.size else 0
    if args.folds < 2:
        raise RuntimeError("--folds must be >= 2.")
    if args.folds > min_class_size:
        raise RuntimeError(
            f"--folds={args.folds} is too high for class distribution in train+val. "
            f"Minimum class size is {min_class_size}."
        )

    cv = StratifiedGroupKFold(n_splits=args.folds, shuffle=True, random_state=args.seed)
    fold_metrics = []
    out_dir = Path(args.artifacts_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y, groups=groups), start=1):
        train_records = [trainval[i] for i in train_idx]
        val_records = [trainval[i] for i in val_idx]
        model, metrics = train_once(train_records, val_records, args, fold_name=f"fold{fold}")
        fold_metrics.append(metrics)
        torch.save(model.state_dict(), out_dir / f"resnet50_fold{fold}.pt")
        print(f"[fold{fold}] metrics: {metrics}")

    summary = {
        "folds": fold_metrics,
        "mean_recall_violence": float(np.mean([m["recall_violence"] for m in fold_metrics])),
        "mean_precision_violence": float(np.mean([m["precision_violence"] for m in fold_metrics])),
        "mean_f1_violence": float(np.mean([m["f1_violence"] for m in fold_metrics])),
    }
    with (out_dir / "cv_metrics.json").open("w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2)
    print("CV summary:", summary)


def run_single_split(all_records, args):
    train_records, val_records = split_train_eval(all_records, use_test=args.eval_on_test)
    out_dir = Path(args.artifacts_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model, metrics = train_once(train_records, val_records, args, fold_name="single")
    torch.save(model.state_dict(), out_dir / "resnet50_best.pt")
    with (out_dir / "metrics.json").open("w", encoding="utf-8") as fp:
        json.dump(metrics, fp, indent=2)
    print("Final metrics:", metrics)


def parse_args():
    parser = argparse.ArgumentParser(description="Train ResNet50 for violence classification.")
    parser.add_argument("--frames-root", default="data/frames", type=str)
    parser.add_argument("--artifacts-dir", default="artifacts", type=str)
    parser.add_argument("--epochs", default=30, type=int)
    parser.add_argument("--batch-size", default=16, type=int)
    parser.add_argument("--lr", default=1e-4, type=float)
    parser.add_argument("--seed", default=42, type=int)
    parser.add_argument("--threshold", default=0.35, type=float)
    parser.add_argument("--min-epochs", default=5, type=int)
    parser.add_argument("--early-stopping-patience", default=3, type=int)
    parser.add_argument("--early-stopping-min-delta", default=0.001, type=float)
    parser.add_argument("--cross-validate", action="store_true")
    parser.add_argument("--folds", default=5, type=int)
    parser.add_argument("--eval-on-test", action="store_true")
    return parser.parse_args()


def summarize_records(records):
    summary = {split: {"non_violence": 0, "violence": 0} for split in ("train", "val", "test")}
    for _path, label, _group, split in records:
        if split not in summary:
            continue
        class_name = "violence" if label == 1 else "non_violence"
        summary[split][class_name] += 1
    return summary


def main():
    args = parse_args()
    seed_everything(args.seed)

    frames_root = Path(args.frames_root)
    if not frames_root.exists():
        raise RuntimeError(
            f"Frames root not found: {frames_root}. "
            "Pass correct path via --frames-root (example: ai-service/data/frames)."
        )

    all_records = collect_records(frames_root)
    if not all_records:
        raise RuntimeError("No frames found. Run prepare_frames.py first.")
    summary = summarize_records(all_records)
    print("Dataset summary:", json.dumps(summary, indent=2))

    if args.cross_validate:
        run_cross_validate(all_records, args)
    else:
        run_single_split(all_records, args)


if __name__ == "__main__":
    main()
