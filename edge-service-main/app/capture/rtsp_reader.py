import logging
import random
import time
from collections.abc import Callable

import cv2
import numpy as np

from app.config import Settings
from app.health.metrics import Metrics

logger = logging.getLogger(__name__)


class RtspReader:
    def __init__(
        self,
        settings: Settings,
        metrics: Metrics,
        capture_factory: Callable[[Settings], cv2.VideoCapture] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self.settings = settings
        self.metrics = metrics
        self._capture_factory = capture_factory or self._default_capture_factory
        self._sleep_fn = sleep_fn or time.sleep
        self._capture: cv2.VideoCapture | None = None
        self._retry_delay = self.settings.retry_base_sec
        self._min_interval = 1.0 / float(self.settings.capture_fps)
        self._last_yield_at = 0.0

    @staticmethod
    def _default_capture_factory(settings: Settings) -> cv2.VideoCapture:
        capture = cv2.VideoCapture(
            settings.rtsp_url,
            cv2.CAP_FFMPEG,
            [
                cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,
                settings.rtsp_open_timeout_ms,
                cv2.CAP_PROP_READ_TIMEOUT_MSEC,
                settings.rtsp_read_timeout_ms,
            ],
        )
        try:
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        return capture

    def _connect(self) -> cv2.VideoCapture:
        return self._capture_factory(self.settings)

    def next_frame(self) -> tuple[float, np.ndarray]:
        while True:
            if self._capture is None or not self._capture.isOpened():
                self._capture = self._connect()
                if not self._capture.isOpened():
                    self.metrics.rtsp_connected = False
                    self.metrics.reconnect_attempts_total += 1
                    sleep_for = self._retry_delay + random.uniform(0, self._retry_delay * 0.2)
                    logger.warning("rtsp_connect_failed", extra={"event_id": "", "camera_id": self.settings.camera_id})
                    self._sleep_fn(sleep_for)
                    self._retry_delay = min(self._retry_delay * 2, 30)
                    continue
                self._retry_delay = self.settings.retry_base_sec
                self.metrics.rtsp_connected = True
                logger.info(
                    "rtsp_connected capture_fps=%s open_timeout_ms=%s read_timeout_ms=%s",
                    self.settings.capture_fps,
                    self.settings.rtsp_open_timeout_ms,
                    self.settings.rtsp_read_timeout_ms,
                    extra={"event_id": "", "camera_id": self.settings.camera_id},
                )

            ok, frame = self._capture.read()
            frame_ts = time.time()
            if not ok or frame is None:
                self.metrics.rtsp_connected = False
                self.metrics.reconnect_attempts_total += 1
                logger.warning("rtsp_stream_lost", extra={"event_id": "", "camera_id": self.settings.camera_id})
                self._capture.release()
                self._capture = None
                continue

            if frame_ts - self._last_yield_at < self._min_interval:
                continue

            self._last_yield_at = frame_ts
            return frame_ts, frame
