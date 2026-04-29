import argparse
import base64
import json
import logging
import os
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

import cv2
import torch
import torch.nn as nn
import requests
from kafka import KafkaConsumer, KafkaProducer
from PIL import Image
from torchvision import models, transforms


LOGGER = logging.getLogger("kafka_inference_worker")


def build_model() -> nn.Module:
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 1)
    return model


def load_checkpoint(checkpoint_path: Path, device: torch.device) -> nn.Module:
    if not checkpoint_path.exists():
        raise RuntimeError(f"Checkpoint not found: {checkpoint_path}")
    model = build_model().to(device)
    state = torch.load(str(checkpoint_path), map_location=device)
    model.load_state_dict(state)
    model.eval()
    return model


def build_transform():
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )


def infer_pil_image(
    image: Image.Image,
    model: nn.Module,
    device: torch.device,
    preprocess,
    threshold: float,
) -> Tuple[str, float, float]:
    x = preprocess(image.convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(x).squeeze(1)
        prob_violence = float(torch.sigmoid(logits).item())
    label = "violence" if prob_violence >= threshold else "non-violence"
    confidence = prob_violence if label == "violence" else (1.0 - prob_violence)
    return label, confidence, prob_violence


def resolve_media_url(event: Dict[str, Any], media_url_template: str) -> Optional[str]:
    direct = event.get("media_url")
    if direct:
        return str(direct)

    bucket = event.get("bucket")
    object_key = event.get("object_key")
    if bucket and object_key and media_url_template:
        key = str(object_key).lstrip("/")
        return media_url_template.format(bucket=bucket, object_key=key)

    return None


def decode_image_from_event(event: Dict[str, Any], media_url_template: str) -> Image.Image:
    image_path = event.get("image_path")
    image_b64 = event.get("image_base64")
    media_url = resolve_media_url(event, media_url_template)
    media_type = str(event.get("media_type") or event.get("content_type") or "").lower()

    if image_path:
        image_file = Path(image_path)
        if not image_file.exists():
            raise RuntimeError(f"image_path does not exist: {image_file}")
        return Image.open(image_file).convert("RGB")

    if image_b64:
        raw = base64.b64decode(image_b64)
        return Image.open(BytesIO(raw)).convert("RGB")

    if media_url:
        # If media is an image URL, infer directly.
        if media_type.startswith("image/") or media_url.lower().endswith((".jpg", ".jpeg", ".png")):
            response = requests.get(media_url, timeout=15)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")

        # For video URL, extract a frame from the middle of the stream.
        if media_type.startswith("video/") or media_url.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
            cap = cv2.VideoCapture(media_url)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open video URL: {media_url}")
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if frame_count > 2:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
            ok, frame = cap.read()
            cap.release()
            if not ok or frame is None:
                raise RuntimeError(f"Cannot extract frame from video URL: {media_url}")
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb)

        raise RuntimeError(
            "Unsupported media_url format. Provide media_type=image/* or video/*, "
            "or URL ending with known image/video extension."
        )

    raise RuntimeError(
        "Message must include one of: image_path, image_base64, media_url, "
        "or pair bucket+object_key (with --media-url-template configured)."
    )


DEFAULT_FACILITY_ID = "7e7b1d4a-8b2d-4a5c-a3b1-6c4d9a3c2a01"
DEFAULT_CAMERA_ID = "3a1e9c2f-0b3e-4c5d-9a8f-11c2a3b4c5d6"


def build_alert_event(
    source_event: Dict[str, Any],
    label: str,
    confidence: float,
    prob_violence: float,
    threshold: float,
    model_name: str,
    facility_id: str,
    camera_id: str,
) -> Dict[str, Any]:
    inferred_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return {
        "schema_version": "1.0",
        "alert_id": str(uuid4()),
        "source_event_id": source_event.get("event_id"),
        "facility_id": facility_id,
        "camera_id": camera_id,
        "bucket": source_event.get("bucket"),
        "object_key": source_event.get("object_key"),
        "violence_score": round(prob_violence, 6),
        "threshold": threshold,
        "model_name": model_name,
        "inferred_at": inferred_at,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Consume raw-media-events, run model inference, publish violence alerts."
    )
    parser.add_argument("--bootstrap-servers", default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092"))
    parser.add_argument("--input-topic", default=os.getenv("KAFKA_INPUT_TOPIC", "raw-media-events"))
    parser.add_argument("--output-topic", default=os.getenv("KAFKA_OUTPUT_TOPIC", "violence-alerts"))
    parser.add_argument("--error-topic", default=os.getenv("KAFKA_ERROR_TOPIC", "raw-media-events-errors"))
    parser.add_argument("--group-id", default=os.getenv("KAFKA_GROUP_ID", "violence-inference-worker"))
    parser.add_argument("--checkpoint", default=os.getenv("MODEL_CHECKPOINT", "model/resnet50_best.pt"))
    parser.add_argument("--model-name", default=os.getenv("MODEL_NAME", "resnet50-v1"))
    parser.add_argument(
        "--facility-id",
        default=os.getenv("FACILITY_ID", DEFAULT_FACILITY_ID),
        help="Always written to violence-alerts JSON (default: deployment facility).",
    )
    parser.add_argument(
        "--camera-id",
        default=os.getenv("CAMERA_ID", DEFAULT_CAMERA_ID),
        help="Always written to violence-alerts JSON (default: deployment camera).",
    )
    parser.add_argument("--threshold", type=float, default=float(os.getenv("MODEL_THRESHOLD", "0.75")))
    parser.add_argument(
        "--media-url-template",
        default=os.getenv("MEDIA_URL_TEMPLATE", ""),
        help="Template for object storage URLs, e.g. http://host:9000/{bucket}/{object_key}",
    )
    parser.add_argument(
        "--auto-offset-reset",
        choices=("earliest", "latest"),
        default=os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
    )
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint_path = Path(args.checkpoint)
    model = load_checkpoint(checkpoint_path, device)
    preprocess = build_transform()

    consumer = KafkaConsumer(
        args.input_topic,
        bootstrap_servers=args.bootstrap_servers,
        group_id=args.group_id,
        enable_auto_commit=False,
        auto_offset_reset=args.auto_offset_reset,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )
    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        acks="all",
        retries=5,
    )

    LOGGER.info(
        "Worker started: input=%s output=%s bootstrap=%s checkpoint=%s device=%s",
        args.input_topic,
        args.output_topic,
        args.bootstrap_servers,
        checkpoint_path,
        device,
    )

    try:
        for msg in consumer:
            event = msg.value if isinstance(msg.value, dict) else {}
            event["_source_topic"] = msg.topic

            try:
                image = decode_image_from_event(event, args.media_url_template)
                label, confidence, prob_violence = infer_pil_image(
                    image=image,
                    model=model,
                    device=device,
                    preprocess=preprocess,
                    threshold=args.threshold,
                )
                alert = build_alert_event(
                    source_event=event,
                    label=label,
                    confidence=confidence,
                    prob_violence=prob_violence,
                    threshold=args.threshold,
                    model_name=args.model_name,
                    facility_id=args.facility_id,
                    camera_id=args.camera_id,
                )
                producer.send(args.output_topic, alert).get(timeout=10)
                consumer.commit()
                LOGGER.info(
                    "Processed source_event_id=%s violence_score=%.4f threshold=%.2f",
                    alert.get("source_event_id"),
                    alert["violence_score"],
                    alert["threshold"],
                )
            except Exception as exc:
                error_payload = {
                    "event_id": event.get("event_id"),
                    "source_topic": msg.topic,
                    "error": str(exc),
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                    "raw_event": event,
                }
                try:
                    producer.send(args.error_topic, error_payload).get(timeout=10)
                except Exception:
                    LOGGER.exception(
                        "Failed to publish error payload to error topic '%s'.",
                        args.error_topic,
                    )
                consumer.commit()
                LOGGER.exception("Failed to process message, sent to error topic.")
                time.sleep(0.1)
    finally:
        consumer.close()
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
