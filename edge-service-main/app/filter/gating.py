import logging
import threading
from collections import deque
from dataclasses import dataclass

import cv2
import numpy as np

from app.chunk.chunk_builder import Chunk, ChunkBuilder, FrameSample
from app.config import Settings
from app.filter.detector import (
    PersonDetection,
    PersonDetectionBatch,
    PersonDetector,
    YoloPersonDetector,
)
from app.health.metrics import Metrics

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MotionAnalysis:
    motion_detected: bool


@dataclass(frozen=True)
class TriggerEvaluation:
    motion_detected: bool
    person_detected: bool


class MotionAnalyzer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._prev_gray: np.ndarray | None = None

    def analyze(self, frame: np.ndarray) -> MotionAnalysis:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if self._prev_gray is None:
            self._prev_gray = gray
            return MotionAnalysis(motion_detected=False)

        delta = cv2.absdiff(self._prev_gray, gray)
        _, thresh = cv2.threshold(delta, self.settings.motion_threshold, 255, cv2.THRESH_BINARY)
        self._prev_gray = gray
        thresh = cv2.erode(thresh, None, iterations=1)
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return MotionAnalysis(motion_detected=False)

        frame_area = float(thresh.shape[0] * thresh.shape[1])
        if frame_area <= 0:
            return MotionAnalysis(motion_detected=False)

        largest_ratio = max(cv2.contourArea(contour) for contour in contours) / frame_area
        return MotionAnalysis(
            motion_detected=self.settings.motion_min_ratio <= largest_ratio <= self.settings.motion_global_max_ratio,
        )


class TriggerEvaluator:
    def __init__(
        self,
        settings: Settings,
        metrics: Metrics | None = None,
        detector: PersonDetector | None = None,
    ) -> None:
        self.settings = settings
        self.metrics = metrics
        self.detector = detector if detector is not None else self._build_detector(settings)
        self.motion_analyzer = MotionAnalyzer(settings)

    def evaluate(self, frame: np.ndarray, *, recording_active: bool) -> TriggerEvaluation:
        if self.metrics is not None:
            self.metrics.trigger_checks_total += 1
            self.metrics.frames_sampled_total += 1

        motion = self.motion_analyzer.analyze(frame)
        if motion.motion_detected and self.metrics is not None:
            self.metrics.motion_pass_total += 1

        person_batch = self._detect_person(frame, should_check=recording_active or motion.motion_detected)
        person_detected = len(person_batch.detections) >= 1
        if self.metrics is not None and self.settings.enable_person_gating:
            self.metrics.raw_person_detections_total += person_batch.raw_count
            self.metrics.person_rejected_confidence_total += person_batch.rejected_confidence_count
            self.metrics.person_rejected_box_size_total += person_batch.rejected_box_size_count
            self.metrics.person_accepted_total += len(person_batch.detections)
        if person_detected and self.metrics is not None and self.settings.enable_person_gating:
            self.metrics.person_pass_total += 1

        return TriggerEvaluation(
            motion_detected=motion.motion_detected,
            person_detected=person_detected,
        )

    def _detect_person(self, frame: np.ndarray, *, should_check: bool) -> PersonDetectionBatch:
        if not self.settings.enable_person_gating:
            return PersonDetectionBatch.empty()
        if not should_check:
            return PersonDetectionBatch.empty()

        inspect_fn = getattr(self.detector, "inspect", None)
        if callable(inspect_fn):
            return inspect_fn(frame)

        detections = self.detector.detect(frame)
        return PersonDetectionBatch(detections=list(detections), raw_count=len(detections))

    @staticmethod
    def _build_detector(settings: Settings) -> PersonDetector:
        if not settings.enable_person_gating:
            return _DisabledPersonDetector()
        return YoloPersonDetector(
            settings.person_model_path,
            settings.person_detector_confidence,
            settings.person_min_box_height_ratio,
        )


class RecordingCoordinator:
    def __init__(self, settings: Settings, metrics: Metrics | None = None) -> None:
        self.settings = settings
        self.metrics = metrics
        self.chunk_builder = ChunkBuilder(
            fps=float(settings.output_fps),
            chunk_duration_sec=settings.chunk_duration_sec,
        )
        self._ring_buffer: deque[FrameSample] = deque()
        self._latest_frame: FrameSample | None = None
        self._last_person_hit_ts: float | None = None
        self._lock = threading.Lock()

    def ingest_frame(self, ts: float, frame: np.ndarray) -> Chunk | None:
        sample = FrameSample(ts=ts, frame=frame.copy())
        with self._lock:
            self._latest_frame = sample
            self._ring_buffer.append(sample)
            self._trim_ring_buffer(ts)
            if self.metrics is not None:
                self.metrics.frames_captured_total += 1
            if not self.chunk_builder.is_recording:
                return None
            chunk = self.chunk_builder.push(sample)
            if chunk is not None and self.metrics is not None:
                self.metrics.effective_chunk_fps = chunk.fps
            return chunk

    def latest_frame(self) -> FrameSample | None:
        with self._lock:
            return self._latest_frame

    def is_recording(self) -> bool:
        with self._lock:
            return self.chunk_builder.is_recording

    def handle_trigger_evaluation(self, ts: float, evaluation: TriggerEvaluation) -> Chunk | None:
        with self._lock:
            if not self.chunk_builder.is_recording:
                if not self._should_start_recording(evaluation):
                    return None
                seed_frames = list(self._ring_buffer)
                if not seed_frames and self._latest_frame is not None:
                    seed_frames = [self._latest_frame]
                if self.chunk_builder.start(seed_frames):
                    self._last_person_hit_ts = ts
                    if self.metrics is not None:
                        self.metrics.triggers_total += 1
                    logger.info(
                        "recording_started prebuffer_frames=%s prebuffer_sec=%.2f",
                        len(seed_frames),
                        self.settings.prebuffer_sec,
                    )
                return None

            if self._should_continue_recording(evaluation):
                self._last_person_hit_ts = ts
                return None

            if not self.settings.enable_person_gating:
                return self._finish_recording_locked(reason="motion_stopped")

            if self._last_person_hit_ts is None:
                return self._finish_recording_locked(reason="no_person_hit")

            grace_elapsed = ts - self._last_person_hit_ts
            if grace_elapsed <= self.settings.person_grace_sec:
                return None
            return self._finish_recording_locked(reason="grace_elapsed")

    def finish_active_recording(self) -> Chunk | None:
        with self._lock:
            return self._finish_recording_locked(reason="shutdown")

    def _finish_recording_locked(self, *, reason: str) -> Chunk | None:
        chunk = self.chunk_builder.finish()
        self._last_person_hit_ts = None
        if chunk is not None and self.metrics is not None:
            self.metrics.effective_chunk_fps = chunk.fps
        if chunk is not None:
            logger.info(
                "recording_stopped reason=%s duration_sec=%.2f effective_fps=%.2f",
                reason,
                chunk.duration_sec,
                chunk.fps,
            )
        return chunk

    def _trim_ring_buffer(self, latest_ts: float) -> None:
        cutoff_ts = latest_ts - self.settings.prebuffer_sec
        while self._ring_buffer and self._ring_buffer[0].ts < cutoff_ts:
            self._ring_buffer.popleft()

    def _should_start_recording(self, evaluation: TriggerEvaluation) -> bool:
        if not evaluation.motion_detected:
            return False
        if not self.settings.enable_person_gating:
            return True
        return evaluation.person_detected

    def _should_continue_recording(self, evaluation: TriggerEvaluation) -> bool:
        if not self.settings.enable_person_gating:
            return evaluation.motion_detected
        return evaluation.person_detected


class GatingFilter:
    def __init__(
        self,
        settings: Settings,
        metrics: Metrics | None = None,
        detector: PersonDetector | None = None,
    ) -> None:
        self.settings = settings
        self.metrics = metrics
        self.trigger_evaluator = TriggerEvaluator(settings, metrics=metrics, detector=detector)
        self.detector = self.trigger_evaluator.detector
        self.chunk_builder = ChunkBuilder(
            fps=float(settings.output_fps),
            chunk_duration_sec=settings.chunk_duration_sec,
        )
        self._last_person_hit_ts: float | None = None

    def process_frame(self, ts: float, frame: np.ndarray) -> Chunk | None:
        evaluation = self.trigger_evaluator.evaluate(frame, recording_active=self.chunk_builder.is_recording)

        if not self.chunk_builder.is_recording:
            if not self._should_start_recording(evaluation):
                return None
            if self.chunk_builder.start([FrameSample(ts=ts, frame=frame)]) and self.metrics is not None:
                self.metrics.triggers_total += 1
            self._last_person_hit_ts = ts
            return None

        if self._should_continue_recording(evaluation):
            self._last_person_hit_ts = ts
            chunk = self.chunk_builder.push(FrameSample(ts=ts, frame=frame))
            if chunk is not None and self.metrics is not None:
                self.metrics.effective_chunk_fps = chunk.fps
            return chunk

        if self.settings.enable_person_gating and self._last_person_hit_ts is not None:
            if ts - self._last_person_hit_ts <= self.settings.person_grace_sec:
                chunk = self.chunk_builder.push(FrameSample(ts=ts, frame=frame))
                if chunk is not None and self.metrics is not None:
                    self.metrics.effective_chunk_fps = chunk.fps
                return chunk

        chunk = self._finish_recording()
        if chunk is not None and self.metrics is not None:
            self.metrics.effective_chunk_fps = chunk.fps
        return chunk

    def _should_start_recording(self, evaluation: TriggerEvaluation) -> bool:
        if not evaluation.motion_detected:
            return False
        if not self.settings.enable_person_gating:
            return True
        return evaluation.person_detected

    def _should_continue_recording(self, evaluation: TriggerEvaluation) -> bool:
        if not self.settings.enable_person_gating:
            return evaluation.motion_detected
        return evaluation.person_detected

    def _finish_recording(self) -> Chunk | None:
        self._last_person_hit_ts = None
        return self.chunk_builder.finish()

    @staticmethod
    def _build_detector(settings: Settings) -> PersonDetector:
        return TriggerEvaluator._build_detector(settings)


class _DisabledPersonDetector:
    def detect(self, frame: np.ndarray) -> list[PersonDetection]:
        return []
