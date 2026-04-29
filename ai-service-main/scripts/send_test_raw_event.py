import argparse
import json
import os
from pathlib import Path

from kafka import KafkaProducer


def parse_args():
    parser = argparse.ArgumentParser(description="Send one test event to raw-media-events.")
    parser.add_argument("--bootstrap-servers", default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092"))
    parser.add_argument("--topic", default=os.getenv("KAFKA_INPUT_TOPIC", "raw-media-events"))
    parser.add_argument("--event-id", default="demo-1")
    parser.add_argument("--image-path", required=True, help="Absolute or relative path to image file")
    parser.add_argument("--source", default="manual-test")
    return parser.parse_args()


def main():
    args = parse_args()
    image_path = Path(args.image_path)
    if not image_path.exists():
        raise RuntimeError(f"Image not found: {image_path}")

    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        acks="all",
        retries=3,
    )

    payload = {
        "event_id": args.event_id,
        "source": args.source,
        "image_path": str(image_path.resolve()),
        "meta": {"note": "manual smoke test"},
    }
    producer.send(args.topic, payload).get(timeout=10)
    producer.flush()
    producer.close()
    print(f"Sent event to topic '{args.topic}': {payload}")


if __name__ == "__main__":
    main()
