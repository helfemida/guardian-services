# Edge-service runbook

## 1. Setup
- Copy `.env.example` to `.env` and fill real values.
- Ensure `ffmpeg` is available in `PATH`.
- Install deps: `python -m pip install -r requirements.txt`.
- Place the YOLO mini person detector at `PERSON_MODEL_PATH` (default `./data/models/yolov8n.pt`).

## 2. Start service
- Run: `python -m app.main`.
- Service reads RTSP, checks for motion, runs the configured person detector on motion frames, and writes accepted chunks to `LOCAL_MEDIA_DIR`.
- Upload and publish order is strict: MinIO PUT first, then Kafka publish.

## 3. Key runtime artifacts
- SQLite outbox: `OFFLINE_DB_PATH`.
- Local chunks: `LOCAL_MEDIA_DIR`.
- Event topic: `KAFKA_TOPIC_RAW` (default `raw-media-events`).
- Default model path: `PERSON_MODEL_PATH=./data/models/yolov8n.pt`.

## 4. Recovery behavior
- MinIO failure: outbox state `pending_upload`.
- Kafka failure after upload: outbox state `uploaded_pending_kafka`.
- Replay worker retries FIFO and marks records `done` or `failed`.
