import cv2

from app.capture.rtsp_reader import RtspReader
from app.config import Settings
from app.health.metrics import Metrics


class FakeCapture:
    def set(self, prop: int, value: int) -> bool:
        self.last_set = (prop, value)
        return True


def test_default_capture_factory_uses_rtsp_timeouts(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    def fake_video_capture(url: str, api_preference: int, params: list[int]) -> FakeCapture:
        recorded["url"] = url
        recorded["api_preference"] = api_preference
        recorded["params"] = params
        return FakeCapture()

    monkeypatch.setattr(cv2, "VideoCapture", fake_video_capture)

    capture = RtspReader._default_capture_factory(_settings())

    assert isinstance(capture, FakeCapture)
    assert recorded == {
        "url": "rtsp://camera",
        "api_preference": cv2.CAP_FFMPEG,
        "params": [
            cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,
            4000,
            cv2.CAP_PROP_READ_TIMEOUT_MSEC,
            9000,
        ],
    }


def _settings() -> Settings:
    return Settings(
        rtsp_url="rtsp://camera",
        rtsp_open_timeout_ms=4000,
        rtsp_read_timeout_ms=9000,
        camera_id="camera-1",
        facility_id="facility-1",
        minio_endpoint="http://minio:9000",
        minio_access_key="access",
        minio_secret_key="secret",
        kafka_bootstrap_servers="localhost:9092",
    )
