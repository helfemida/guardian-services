import numpy as np

from app.filter.detector import YoloPersonDetector, _passes_detection_confidence


class FakeTensor:
    def __init__(self, values):
        self._values = values

    def cpu(self):
        return self

    def tolist(self):
        return self._values


class FakeBoxes:
    def __init__(self, xyxy, conf, cls):
        self.xyxy = FakeTensor(xyxy)
        self.conf = FakeTensor(conf)
        self.cls = FakeTensor(cls)

    def __len__(self) -> int:
        return len(self.conf.tolist())


class FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes


class FakeModel:
    def __init__(self, results):
        self._results = results
        self.calls = []

    def predict(self, **kwargs):
        self.calls.append(kwargs)
        return self._results


def test_yolo_detector_filters_non_person_low_confidence_and_tiny_boxes() -> None:
    detector = YoloPersonDetector.__new__(YoloPersonDetector)
    detector.confidence = 0.25
    detector.min_box_height_ratio = 0.05
    detector._model = FakeModel(
        [
            FakeResult(
                FakeBoxes(
                    xyxy=[
                        [10.0, 10.0, 35.0, 60.0],
                        [10.0, 10.0, 35.0, 12.0],
                        [10.0, 10.0, 35.0, 60.0],
                    ],
                    conf=[0.9, 0.9, 0.1],
                    cls=[0.0, 0.0, 0.0],
                )
            )
        ]
    )

    batch = detector.inspect(np.zeros((100, 200, 3), dtype=np.uint8))

    assert len(batch.detections) == 1
    assert batch.raw_count == 3
    assert batch.rejected_box_size_count == 1
    assert batch.rejected_confidence_count == 1
    assert batch.detections[0].confidence == 0.9


def test_yolo_detector_ignores_non_person_classes() -> None:
    detector = YoloPersonDetector.__new__(YoloPersonDetector)
    detector.confidence = 0.25
    detector.min_box_height_ratio = 0.05
    detector._model = FakeModel(
        [
            FakeResult(
                FakeBoxes(
                    xyxy=[
                        [10.0, 10.0, 35.0, 60.0],
                        [15.0, 15.0, 45.0, 70.0],
                    ],
                    conf=[0.8, 0.9],
                    cls=[0.0, 2.0],
                )
            )
        ]
    )

    batch = detector.inspect(np.zeros((100, 200, 3), dtype=np.uint8))

    assert len(batch.detections) == 1
    assert batch.raw_count == 1
    assert batch.detections[0].x1 == 10.0


def test_yolo_detector_uses_person_class_only_in_predict_call() -> None:
    detector = YoloPersonDetector.__new__(YoloPersonDetector)
    detector.confidence = 0.25
    detector.min_box_height_ratio = 0.05
    model = FakeModel([])
    detector._model = model

    detector.inspect(np.zeros((32, 48, 3), dtype=np.uint8))

    assert model.calls[0]["classes"] == [YoloPersonDetector.PERSON_CLASS_ID]
    assert model.calls[0]["device"] == "cpu"


def test_detection_confidence_helper_allows_any_positive_score_when_threshold_is_zero() -> None:
    assert _passes_detection_confidence(0.01, 0.0) is True
    assert _passes_detection_confidence(0.0, 0.0) is False
    assert _passes_detection_confidence(0.24, 0.25) is False
    assert _passes_detection_confidence(0.25, 0.25) is True
