from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class FrameSample:
    ts: float
    frame: np.ndarray


@dataclass
class Chunk:
    captured_at: datetime
    fps: float
    frames: list[np.ndarray]
    duration_sec: float
    start_ts: float
    end_ts: float


class ChunkBuilder:
    def __init__(self, fps: float, chunk_duration_sec: int) -> None:
        self.fps = float(fps)
        self.chunk_duration_sec = float(chunk_duration_sec)
        self._min_interval = 1.0 / self.fps if self.fps > 0 else 0.0
        self._active_frames: list[FrameSample] = []
        self._is_recording = False
        self._chunk_window_start_ts: float | None = None
        self._last_output_ts: float | None = None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start(self, seed_frames: Iterable[FrameSample] | float, frame: np.ndarray | None = None) -> bool:
        if self._is_recording:
            return False

        frames = self._normalize_seed_frames(seed_frames, frame)
        if not frames:
            return False

        self._is_recording = True
        self._chunk_window_start_ts = frames[0].ts
        self._last_output_ts = None
        self._active_frames = []
        for sample in frames:
            self._append_frame(sample)
        return bool(self._active_frames)

    def push(self, sample: FrameSample | float, frame: np.ndarray | None = None) -> Chunk | None:
        if not self._is_recording:
            return None

        normalized = self._normalize_sample(sample, frame)
        self._append_frame(normalized)
        return self._emit_ready_chunk()

    def finish(self) -> Chunk | None:
        if not self._is_recording:
            return None

        self._is_recording = False
        if not self._active_frames:
            self._chunk_window_start_ts = None
            self._last_output_ts = None
            return None

        frames = self._active_frames
        self._active_frames = []
        self._chunk_window_start_ts = None
        self._last_output_ts = None
        return self._build_chunk(frames)

    def _emit_ready_chunk(self) -> Chunk | None:
        if not self._active_frames or self._chunk_window_start_ts is None:
            return None

        boundary_ts = self._chunk_window_start_ts + self.chunk_duration_sec
        latest_ts = self._active_frames[-1].ts
        if latest_ts < boundary_ts:
            return None

        ready_count = 0
        for sample in self._active_frames:
            if sample.ts < boundary_ts:
                ready_count += 1
                continue
            break

        if ready_count <= 0:
            self._chunk_window_start_ts = boundary_ts
            return None

        frames = self._active_frames[:ready_count]
        self._active_frames = self._active_frames[ready_count:]
        self._chunk_window_start_ts = boundary_ts
        return self._build_chunk(frames)

    def _append_frame(self, sample: FrameSample) -> None:
        if self._last_output_ts is None:
            self._active_frames.append(FrameSample(sample.ts, sample.frame.copy()))
            self._last_output_ts = sample.ts
            return

        if sample.ts <= self._last_output_ts:
            return

        if self._min_interval > 0 and sample.ts - self._last_output_ts < (self._min_interval * 0.95):
            return

        self._active_frames.append(FrameSample(sample.ts, sample.frame.copy()))
        self._last_output_ts = sample.ts

    def _build_chunk(self, frames: list[FrameSample]) -> Chunk:
        first_ts = frames[0].ts
        last_ts = frames[-1].ts
        duration_sec = _estimate_duration_sec(frames, self.fps)
        effective_fps = len(frames) / duration_sec if duration_sec > 0 else self.fps
        return Chunk(
            captured_at=datetime.fromtimestamp(first_ts, tz=timezone.utc),
            fps=float(effective_fps),
            frames=[sample.frame for sample in frames],
            duration_sec=float(duration_sec),
            start_ts=first_ts,
            end_ts=last_ts,
        )

    @staticmethod
    def _normalize_sample(sample: FrameSample | float, frame: np.ndarray | None) -> FrameSample:
        if isinstance(sample, FrameSample):
            return sample
        if frame is None:
            raise ValueError("frame is required when sample timestamp is passed directly")
        return FrameSample(ts=float(sample), frame=frame)

    def _normalize_seed_frames(
        self,
        seed_frames: Iterable[FrameSample] | float,
        frame: np.ndarray | None,
    ) -> list[FrameSample]:
        if isinstance(seed_frames, (int, float)):
            if frame is None:
                raise ValueError("frame is required when seed timestamp is passed directly")
            return [FrameSample(ts=float(seed_frames), frame=frame)]

        frames = list(seed_frames)
        frames.sort(key=lambda sample: sample.ts)
        return frames


def _estimate_duration_sec(frames: list[FrameSample], nominal_fps: float) -> float:
    if not frames:
        raise ValueError("cannot estimate duration for empty frame list")

    nominal_interval = 1.0 / nominal_fps if nominal_fps > 0 else 0.0
    if len(frames) == 1:
        return nominal_interval if nominal_interval > 0 else 0.0

    observed_range = frames[-1].ts - frames[0].ts
    observed_interval = observed_range / float(len(frames) - 1) if len(frames) > 1 else 0.0
    frame_interval = observed_interval if observed_interval > 0 else nominal_interval
    if frame_interval <= 0:
        frame_interval = 1e-6
    return observed_range + frame_interval
