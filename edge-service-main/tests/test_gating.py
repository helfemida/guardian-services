from datetime import datetime, timezone

import numpy as np
import pytest

from app.config import Settings
from app.filter.detector import PersonDetection
from app.filter.gating import GatingFilter, RecordingCoordinator, TriggerEvaluation, TriggerEvaluator
from app.health.metrics import Metrics


class FakeDetector:
    def __init__(self, detections: list[PersonDetection]) -> None:
        self._detections = detections
        self.calls = 0

    def detect(self, frame: np.ndarray) -> list[PersonDetection]:
        self.calls += 1
        return list(self._detections)


def test_trigger_evaluator_skips_detector_without_motion_while_idle() -> None:
    metrics = Metrics()
    detector = FakeDetector(_person())
    evaluator = TriggerEvaluator(_settings(), metrics=metrics, detector=detector)

    result_a = evaluator.evaluate(_blank_frame(0), recording_active=False)
    result_b = evaluator.evaluate(_blank_frame(0), recording_active=False)

    assert result_a.motion_detected is False
    assert result_b.motion_detected is False
    assert detector.calls == 0
    assert metrics.trigger_checks_total == 2


def test_trigger_evaluator_runs_detector_while_recording_even_without_motion() -> None:
    detector = FakeDetector(_person())
    evaluator = TriggerEvaluator(_settings(), metrics=Metrics(), detector=detector)

    evaluator.evaluate(_blank_frame(0), recording_active=True)

    assert detector.calls == 1


def test_recording_coordinator_uses_prebuffer_on_start() -> None:
    coordinator = RecordingCoordinator(_settings(prebuffer_sec=0.5), metrics=Metrics())

    for ts in (0.0, 0.1, 0.2):
        assert coordinator.ingest_frame(ts, _moving_frame(int(ts * 10))) is None

    assert coordinator.handle_trigger_evaluation(
        0.2,
        TriggerEvaluation(motion_detected=True, person_detected=True),
    ) is None

    chunk = coordinator.finish_active_recording()

    assert chunk is not None
    assert len(chunk.frames) == 3
    assert chunk.duration_sec == pytest.approx(0.3)
    assert chunk.captured_at == datetime.fromtimestamp(0.0, tz=timezone.utc)


def test_recording_coordinator_respects_grace_period_before_stopping() -> None:
    coordinator = RecordingCoordinator(_settings(person_grace_sec=0.5), metrics=Metrics())

    assert coordinator.ingest_frame(0.0, _moving_frame(0)) is None
    assert coordinator.handle_trigger_evaluation(
        0.0,
        TriggerEvaluation(motion_detected=True, person_detected=True),
    ) is None

    for ts in (0.1, 0.2, 0.3):
        assert coordinator.ingest_frame(ts, _moving_frame(int(ts * 10))) is None

    assert coordinator.handle_trigger_evaluation(
        0.4,
        TriggerEvaluation(motion_detected=False, person_detected=False),
    ) is None
    chunk = coordinator.handle_trigger_evaluation(
        0.6,
        TriggerEvaluation(motion_detected=False, person_detected=False),
    )

    assert chunk is not None
    assert chunk.duration_sec == pytest.approx(0.4)
    assert coordinator.is_recording() is False


def test_gating_filter_uses_yolo_backend_by_default(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class DummyYoloDetector:
        def __init__(self, model_path: str, confidence: float, min_box_height_ratio: float) -> None:
            captured["model_path"] = model_path
            captured["confidence"] = confidence
            captured["min_box_height_ratio"] = min_box_height_ratio

    monkeypatch.setattr("app.filter.gating.YoloPersonDetector", DummyYoloDetector)

    detector = GatingFilter._build_detector(_settings())

    assert isinstance(detector, DummyYoloDetector)
    assert captured == {
        "model_path": "./data/models/yolov8n.pt",
        "confidence": 0.25,
        "min_box_height_ratio": 0.05,
    }


def _settings(**overrides) -> Settings:
    values = {
        "rtsp_url": "rtsp://camera",
        "camera_id": "camera-1",
        "facility_id": "facility-1",
        "minio_endpoint": "http://minio:9000",
        "minio_access_key": "access",
        "minio_secret_key": "secret",
        "kafka_bootstrap_servers": "localhost:9092",
        "output_fps": 10,
        "trigger_fps": 5,
        "capture_fps": 20,
        "chunk_duration_sec": 4,
        "motion_threshold": 10.0,
        "motion_min_ratio": 0.01,
        "motion_global_max_ratio": 0.75,
        "person_model_path": "./data/models/yolov8n.pt",
        "person_detector_confidence": 0.25,
        "person_min_box_height_ratio": 0.05,
        "prebuffer_sec": 0.5,
        "person_grace_sec": 0.5,
    }
    values.update(overrides)
    return Settings(**values)


def _moving_frame(index: int) -> np.ndarray:
    frame = np.zeros((120, 120, 3), dtype=np.uint8)
    start = 5 + (index * 6)
    frame[20:50, start : start + 20] = 255
    return frame


def _blank_frame(value: int) -> np.ndarray:
    return np.full((120, 120, 3), value, dtype=np.uint8)


def _person() -> list[PersonDetection]:
    return [
        PersonDetection(10.0, 10.0, 35.0, 60.0, 0.9),
    ]
