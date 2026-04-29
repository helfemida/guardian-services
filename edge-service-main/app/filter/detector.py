from dataclasses import dataclass
import os
from pathlib import Path
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class PersonDetection:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float


@dataclass(frozen=True)
class PersonDetectionBatch:
    detections: list[PersonDetection]
    raw_count: int = 0
    rejected_confidence_count: int = 0
    rejected_box_size_count: int = 0

    @staticmethod
    def empty() -> "PersonDetectionBatch":
        return PersonDetectionBatch(detections=[])


class PersonDetector(Protocol):
    def detect(self, frame: np.ndarray) -> list[PersonDetection]:
        ...


def _passes_detection_confidence(confidence: float, threshold: float) -> bool:
    if threshold <= 0:
        return confidence > 0.0
    return confidence >= threshold


class YoloPersonDetector:
    PERSON_CLASS_ID = 0

    def __init__(self, model_path: str, confidence: float, min_box_height_ratio: float) -> None:
        _prepare_ultralytics_environment()
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("ultralytics is required for ENABLE_PERSON_GATING=true") from exc

        self._model = YOLO(model_path)
        self.confidence = confidence
        self.min_box_height_ratio = min_box_height_ratio

    def detect(self, frame: np.ndarray) -> list[PersonDetection]:
        return self.inspect(frame).detections

    def inspect(self, frame: np.ndarray) -> PersonDetectionBatch:
        results = self._model.predict(
            source=frame,
            conf=1e-6,
            classes=[self.PERSON_CLASS_ID],
            device="cpu",
            verbose=False,
        )

        if not results:
            return PersonDetectionBatch.empty()

        boxes = getattr(results[0], "boxes", None)
        if boxes is None or len(boxes) == 0:
            return PersonDetectionBatch.empty()

        xyxy_values = boxes.xyxy.cpu().tolist()
        conf_values = boxes.conf.cpu().tolist()
        cls_values = boxes.cls.cpu().tolist()

        detections: list[PersonDetection] = []
        raw_count = 0
        rejected_confidence_count = 0
        rejected_box_size_count = 0
        for bbox, conf, cls_id in zip(xyxy_values, conf_values, cls_values, strict=False):
            if int(cls_id) != self.PERSON_CLASS_ID:
                continue
            raw_count += 1
            if not _passes_detection_confidence(float(conf), self.confidence):
                rejected_confidence_count += 1
                continue
            box_height = float(bbox[3]) - float(bbox[1])
            box_height_ratio = box_height / float(frame.shape[0]) if frame.shape[0] > 0 else 0.0
            if box_height <= 0 or box_height_ratio < self.min_box_height_ratio:
                rejected_box_size_count += 1
                continue
            detections.append(
                PersonDetection(
                    x1=float(bbox[0]),
                    y1=float(bbox[1]),
                    x2=float(bbox[2]),
                    y2=float(bbox[3]),
                    confidence=float(conf),
                )
            )
        return PersonDetectionBatch(
            detections=detections,
            raw_count=raw_count,
            rejected_confidence_count=rejected_confidence_count,
            rejected_box_size_count=rejected_box_size_count,
        )


def _prepare_ultralytics_environment() -> None:
    if "YOLO_CONFIG_DIR" in os.environ:
        return

    config_dir = (Path.cwd() / "data" / "ultralytics").resolve()
    config_dir.mkdir(parents=True, exist_ok=True)
    os.environ["YOLO_CONFIG_DIR"] = str(config_dir)
