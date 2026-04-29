# AI Service: Kafka Inference Worker

This service reads media events from Kafka topic `raw-media-events`, runs violence classification using a ResNet50 checkpoint, and publishes inference results to topic `violence-alerts`.

## Topics

- Input topic: `raw-media-events`
- Output topic: `violence-alerts`
- Error topic: `raw-media-events-errors`

## Message contracts

Input event (JSON):

```json
{
  "event_id": "evt-123",
  "source": "camera-1",
  "image_path": "C:/data/frame_001.jpg",
  "meta": {
    "camera_id": "cam-1"
  }
}
```

You can also pass `image_base64` instead of `image_path`.

You can also pass media URL from object storage (for image/video):

```json
{
  "event_id": "evt-video-1",
  "source": "camera-7",
  "media_url": "http://100.100.224.121:9001/browser/violence-media/.../chunk.mp4",
  "media_type": "video/mp4",
  "meta": {
    "camera_id": "cam-7"
  }
}
```

For video URL, worker extracts a frame and runs classification on that frame.

Output event (JSON):

```json
{
  "event_id": "evt-123",
  "source": "camera-1",
  "source_topic": "raw-media-events",
  "label": "violence",
  "confidence": 0.9231,
  "prob_violence": 0.9231,
  "threshold": 0.75,
  "processed_at": "2026-04-17T12:00:00.000000+00:00",
  "model": "resnet50_best.pt",
  "meta": {
    "camera_id": "cam-1"
  }
}
```

## Install

```bash
python3 -m pip install -r requirements.txt
```

## Run worker

```bash
python3 scripts/kafka_inference_worker.py \
  --bootstrap-servers localhost:29092 \
  --checkpoint model/resnet50_best.pt \
  --input-topic raw-media-events \
  --output-topic violence-alerts
```

Environment variables are also supported:

- `KAFKA_BOOTSTRAP_SERVERS` (default: `localhost:29092`)
- `KAFKA_INPUT_TOPIC` (default: `raw-media-events`)
- `KAFKA_OUTPUT_TOPIC` (default: `violence-alerts`)
- `KAFKA_ERROR_TOPIC` (default: `raw-media-events-errors`)
- `KAFKA_GROUP_ID` (default: `violence-inference-worker`)
- `MODEL_CHECKPOINT` (default: `model/resnet50_best.pt`)
- `MODEL_THRESHOLD` (default: `0.75`)

## Send a test message

```bash
python3 scripts/send_test_raw_event.py \
  --bootstrap-servers localhost:29092 \
  --topic raw-media-events \
  --event-id test-1 \
  --image-path path/to/image.jpg
```

## Notes for your Kafka setup

In your screenshot and script, topic names are:

- `raw-media-events`
- `violence-alerts`

Keep this exact name in both producer and worker. If you prefer singular (`violence-alert`), set `KAFKA_OUTPUT_TOPIC=violence-alert` everywhere consistently.
