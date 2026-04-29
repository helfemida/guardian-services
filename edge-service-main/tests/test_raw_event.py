import json

from app.contracts.raw_event import RawMediaEvent


def test_raw_event_has_camera_key() -> None:
    event = RawMediaEvent(
        facility_id="f1",
        camera_id="c1",
        bucket="b",
        object_key="k",
        duration_sec=4.0,
        captured_at="2026-04-13T00:00:00+00:00",
    )
    assert event.kafka_key() == b"c1"


def test_raw_event_json_matches_kafka_contract_shape() -> None:
    event = RawMediaEvent(
        schema_version="1.0",
        event_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        facility_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        camera_id="c9876a5e-4b3a-4d2c-9e1f-1234567890ab",
        bucket="violence-media",
        object_key="f47ac10b/c9876a5e/2026-04-12/1701428400_chunk.mp4",
        content_type="video/mp4",
        duration_sec=4.0,
        captured_at="2026-04-12T14:00:00.000Z",
        edge_ingested_at="2026-04-12T14:00:01.200Z",
    )

    payload = json.loads(event.model_dump_json())

    assert payload == {
        "schema_version": "1.0",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "facility_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "camera_id": "c9876a5e-4b3a-4d2c-9e1f-1234567890ab",
        "bucket": "violence-media",
        "object_key": "f47ac10b/c9876a5e/2026-04-12/1701428400_chunk.mp4",
        "content_type": "video/mp4",
        "duration_sec": 4.0,
        "captured_at": "2026-04-12T14:00:00.000Z",
        "edge_ingested_at": "2026-04-12T14:00:01.200Z",
    }
