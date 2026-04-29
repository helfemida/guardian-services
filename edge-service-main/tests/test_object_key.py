from datetime import datetime, timezone

from app.main import build_object_key


class DummySettings:
    facility_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    camera_id = "c9876a5e-4b3a-4d2c-9e1f-1234567890ab"


def test_object_key_shape() -> None:
    dt = datetime(2026, 4, 13, tzinfo=timezone.utc)
    key = build_object_key(DummySettings(), dt, "evt")
    assert key == "f47ac10b/c9876a5e/2026-04-13/1776038400000_evt_chunk.mp4"
