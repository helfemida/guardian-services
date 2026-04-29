import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import time

from app.config import Settings
from app.contracts.raw_event import RawMediaEvent, utc_isoformat
from app.health.metrics import Metrics
from app.messaging.kafka_producer import KafkaRawProducer
from app.outbox.sqlite_outbox import OutboxItem, SqliteOutbox
from app.storage.minio_client import MinioClient

logger = logging.getLogger(__name__)


def _safe_unlink(path: Path) -> None:
    path.unlink(missing_ok=True)


class ReplayWorker:
    def __init__(
        self,
        settings: Settings,
        outbox: SqliteOutbox,
        minio: MinioClient,
        producer: KafkaRawProducer,
        metrics: Metrics,
    ) -> None:
        self.settings = settings
        self.outbox = outbox
        self.minio = minio
        self.producer = producer
        self.metrics = metrics
        self._stopped = False

    async def run_forever(self) -> None:
        logger.info("replay_worker_started", extra={"event_id": "", "camera_id": self.settings.camera_id})
        while not self._stopped:
            items = await asyncio.to_thread(self.outbox.get_pending, 20)
            self.metrics.outbox_pending_count = await asyncio.to_thread(self.outbox.pending_count)
            for item in items:
                await self._replay_one(item)
            await asyncio.sleep(self.settings.replay_poll_sec)

    def stop(self) -> None:
        self._stopped = True
        logger.info("replay_worker_stopping", extra={"event_id": "", "camera_id": self.settings.camera_id})

    async def _replay_one(self, item: OutboxItem) -> None:
        current_state = item.state
        try:
            payload = json.loads(item.payload_json)
            if item.state == "pending_upload":
                await asyncio.to_thread(
                    self.minio.upload_file,
                    Path(item.local_media_path),
                    item.object_key,
                    bucket=item.bucket,
                    content_type=payload.get("content_type", "video/mp4"),
                )
                payload["edge_ingested_at"] = utc_isoformat(datetime.now(timezone.utc))
                current_state = "uploaded_pending_kafka"
                await asyncio.to_thread(
                    self.outbox.update_state,
                    item.id,
                    current_state,
                    increment_attempt=False,
                    next_attempt_at=0.0,
                    payload=payload,
                )
                logger.info(
                    "replay_upload_completed bucket=%s object_key=%s",
                    item.bucket,
                    item.object_key,
                    extra={"event_id": payload.get("event_id", ""), "camera_id": payload.get("camera_id", self.settings.camera_id)},
                )

            event = RawMediaEvent(**payload)
            await self.producer.publish(event)
            await asyncio.to_thread(
                self.outbox.update_state,
                item.id,
                "done",
                increment_attempt=False,
                next_attempt_at=0.0,
            )
            await asyncio.to_thread(_safe_unlink, Path(item.local_media_path))
            self.metrics.replayed_total += 1
            logger.info(
                "replay_publish_completed bucket=%s object_key=%s",
                item.bucket,
                item.object_key,
                extra={"event_id": event.event_id, "camera_id": event.camera_id},
            )
        except Exception as exc:
            self.metrics.delivery_attempt_failures_total += 1
            payload = json.loads(item.payload_json)
            logger.warning(
                "replay_failed state=%s object_key=%s error=%s",
                current_state,
                item.object_key,
                exc,
                extra={"event_id": payload.get("event_id", ""), "camera_id": payload.get("camera_id", self.settings.camera_id)},
            )
            next_attempt_count = item.attempt_count + 1
            if next_attempt_count >= self.settings.max_retry_attempts:
                await asyncio.to_thread(
                    self.outbox.update_state,
                    item.id,
                    "failed",
                    last_error=str(exc),
                    increment_attempt=True,
                    next_attempt_at=0.0,
                )
                logger.warning(
                    "replay_marked_failed object_key=%s attempts=%s",
                    item.object_key,
                    next_attempt_count,
                    extra={"event_id": payload.get("event_id", ""), "camera_id": payload.get("camera_id", self.settings.camera_id)},
                )
            else:
                backoff_sec = self.settings.retry_base_sec * (2 ** max(item.attempt_count, 0))
                await asyncio.to_thread(
                    self.outbox.update_state,
                    item.id,
                    current_state,
                    last_error=str(exc),
                    increment_attempt=True,
                    next_attempt_at=time.time() + backoff_sec,
                )
                logger.info(
                    "replay_rescheduled object_key=%s attempts=%s backoff_sec=%.2f",
                    item.object_key,
                    next_attempt_count,
                    backoff_sec,
                    extra={"event_id": payload.get("event_id", ""), "camera_id": payload.get("camera_id", self.settings.camera_id)},
                )
