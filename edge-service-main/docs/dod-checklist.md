# DoD checklist

- RTSP reconnect works automatically after stream interruption.
- Chunks are encoded as H.264 mp4 with configured duration.
- Event payload matches `raw-media-events` contract.
- Kafka key is `camera_id`.
- Service enforces `MinIO PUT -> Kafka publish`.
- Offline outbox handles MinIO and Kafka failure branches.
- Replay worker drains pending queue after dependency recovery.
- Unit tests pass locally.
