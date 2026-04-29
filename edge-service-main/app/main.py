import asyncio
import logging
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

from app.chunk.chunk_builder import Chunk
from app.config import Settings, load_settings, prime_videoio_environment
from app.contracts.raw_event import RawMediaEvent, utc_isoformat
from app.encode.ffmpeg_encoder import EncodedClip, FfmpegEncoder
from app.health.metrics import Metrics
from app.logging import configure_logging
from app.messaging.kafka_producer import KafkaRawProducer
from app.outbox.replay_worker import ReplayWorker
from app.outbox.sqlite_outbox import SqliteOutbox
from app.storage.minio_client import MinioClient

prime_videoio_environment()

from app.capture.rtsp_reader import RtspReader
from app.filter.gating import RecordingCoordinator, TriggerEvaluator

logger = logging.getLogger(__name__)


def build_object_key(settings: Settings, captured_at: datetime, event_id: str) -> str:
    captured_utc = captured_at.astimezone(timezone.utc)
    date_part = captured_utc.strftime("%Y-%m-%d")
    unix_ms = int(captured_utc.timestamp() * 1000)
    facility_prefix = _object_key_prefix(settings.facility_id)
    camera_prefix = _object_key_prefix(settings.camera_id)
    return f"{facility_prefix}/{camera_prefix}/{date_part}/{unix_ms}_{event_id}_chunk.mp4"


def _object_key_prefix(identifier: str) -> str:
    return identifier.split("-", 1)[0]


async def _run_capture_worker(
    reader: RtspReader,
    coordinator: RecordingCoordinator,
    chunk_queue: asyncio.Queue[Chunk | None],
    metrics: Metrics,
) -> None:
    while True:
        ts, frame = await asyncio.to_thread(reader.next_frame)
        chunk = coordinator.ingest_frame(ts, frame)
        if chunk is None:
            continue
        await _queue_chunk(chunk_queue, chunk, metrics)


async def _run_trigger_loop(
    settings: Settings,
    evaluator: TriggerEvaluator,
    coordinator: RecordingCoordinator,
    chunk_queue: asyncio.Queue[Chunk | None],
    metrics: Metrics,
) -> None:
    loop = asyncio.get_running_loop()
    interval_sec = 1.0 / float(settings.trigger_fps)
    next_tick = loop.time()
    last_processed_ts = -1.0

    while True:
        now = loop.time()
        if now < next_tick:
            await asyncio.sleep(next_tick - now)
        tick_started = loop.time()
        metrics.trigger_loop_lag_sec = max(0.0, tick_started - next_tick)

        sample = coordinator.latest_frame()
        recording_active = coordinator.is_recording()
        if sample is not None and sample.ts > last_processed_ts:
            evaluation = await asyncio.to_thread(
                evaluator.evaluate,
                sample.frame,
                recording_active=recording_active,
            )
            chunk = coordinator.handle_trigger_evaluation(sample.ts, evaluation)
            if chunk is not None:
                await _queue_chunk(chunk_queue, chunk, metrics)
            last_processed_ts = sample.ts

        next_tick += interval_sec


async def _run_encode_worker(
    queue: asyncio.Queue[Chunk | None],
    settings: Settings,
    metrics: Metrics,
    encoder: FfmpegEncoder,
    outbox: SqliteOutbox,
) -> None:
    while True:
        chunk = await queue.get()
        metrics.raw_chunk_queue_size = queue.qsize()
        try:
            if chunk is None:
                return
            await _encode_and_stage_chunk(
                chunk,
                settings=settings,
                metrics=metrics,
                encoder=encoder,
                outbox=outbox,
            )
        finally:
            queue.task_done()


async def _encode_and_stage_chunk(
    chunk: Chunk,
    *,
    settings: Settings,
    metrics: Metrics,
    encoder: FfmpegEncoder,
    outbox: SqliteOutbox,
) -> None:
    event = RawMediaEvent(
        schema_version=settings.schema_version,
        facility_id=settings.facility_id,
        camera_id=settings.camera_id,
        bucket=settings.minio_bucket,
        object_key="",
        duration_sec=chunk.duration_sec,
        captured_at=utc_isoformat(chunk.captured_at),
    )
    object_key = build_object_key(settings, chunk.captured_at, event.event_id)
    event.object_key = object_key

    encode_started = asyncio.get_running_loop().time()
    encoded_clip: EncodedClip | None = None
    try:
        encoded_clip = await asyncio.to_thread(encoder.encode, chunk, file_stem=event.event_id)
        metrics.last_encode_latency_sec = asyncio.get_running_loop().time() - encode_started
        metrics.chunks_created_total += 1
        metrics.effective_chunk_fps = chunk.fps
        logger.info(
            "alert_chunk_encoded encoder=%s local_path=%s duration_sec=%.2f effective_fps=%.2f",
            encoded_clip.encoder,
            encoded_clip.path,
            chunk.duration_sec,
            chunk.fps,
            extra={"event_id": event.event_id, "camera_id": settings.camera_id},
        )
        await asyncio.to_thread(
            outbox.add,
            local_media_path=str(encoded_clip.path),
            bucket=settings.minio_bucket,
            object_key=object_key,
            payload=event.model_dump(mode="json"),
            state="pending_upload",
        )
        logger.info(
            "alert_chunk_staged object_key=%s duration_sec=%.2f effective_fps=%.2f",
            object_key,
            chunk.duration_sec,
            chunk.fps,
            extra={"event_id": event.event_id, "camera_id": settings.camera_id},
        )
    except Exception:
        metrics.encode_failures_total += 1
        logger.exception(
            "chunk_encode_failed",
            extra={"event_id": event.event_id, "camera_id": settings.camera_id},
        )
        if encoded_clip is not None:
            await asyncio.to_thread(_safe_unlink, encoded_clip.path)


async def _queue_chunk(queue: asyncio.Queue[Chunk | None], chunk: Chunk, metrics: Metrics) -> None:
    if queue.full():
        metrics.overload_block_total += 1
        logger.critical(
            "raw_chunk_queue_blocked queue_size=%s duration_sec=%.2f effective_fps=%.2f",
            queue.qsize(),
            chunk.duration_sec,
            chunk.fps,
        )
    await queue.put(chunk)
    metrics.raw_chunk_queue_size = queue.qsize()


def _safe_unlink(path: Path) -> None:
    path.unlink(missing_ok=True)


async def run() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    metrics = Metrics()

    logger.info(
        "edge_service_starting capture_fps=%s trigger_fps=%s output_fps=%s minio_endpoint=%s kafka_bootstrap=%s topic=%s",
        settings.capture_fps,
        settings.trigger_fps,
        settings.output_fps,
        settings.minio_endpoint,
        settings.kafka_bootstrap_servers,
        settings.kafka_topic_raw,
        extra={"event_id": "", "camera_id": settings.camera_id},
    )

    settings.local_media_dir.mkdir(parents=True, exist_ok=True)

    reader = RtspReader(settings, metrics)
    evaluator = TriggerEvaluator(settings, metrics=metrics)
    coordinator = RecordingCoordinator(settings, metrics=metrics)
    logger.info(
        "person_detector_initialized enabled=%s detector=%s model_path=%s confidence=%.2f min_box_height_ratio=%.3f",
        settings.enable_person_gating,
        type(evaluator.detector).__name__,
        settings.person_model_path,
        settings.person_detector_confidence,
        settings.person_min_box_height_ratio,
        extra={"event_id": "", "camera_id": settings.camera_id},
    )
    encoder = FfmpegEncoder(settings.local_media_dir)
    minio = MinioClient(settings)
    producer = KafkaRawProducer(settings)
    outbox = SqliteOutbox(settings.offline_db_path)
    replay = ReplayWorker(settings, outbox, minio, producer, metrics)
    chunk_queue: asyncio.Queue[Chunk | None] = asyncio.Queue(maxsize=2)

    replay_task = asyncio.create_task(replay.run_forever())
    encode_task = asyncio.create_task(
        _run_encode_worker(
            chunk_queue,
            settings=settings,
            metrics=metrics,
            encoder=encoder,
            outbox=outbox,
        )
    )
    capture_task = asyncio.create_task(_run_capture_worker(reader, coordinator, chunk_queue, metrics))
    trigger_task = asyncio.create_task(_run_trigger_loop(settings, evaluator, coordinator, chunk_queue, metrics))

    try:
        await asyncio.gather(capture_task, trigger_task)
    finally:
        capture_task.cancel()
        trigger_task.cancel()
        with suppress(asyncio.CancelledError):
            await capture_task
        with suppress(asyncio.CancelledError):
            await trigger_task

        final_chunk = coordinator.finish_active_recording()
        if final_chunk is not None:
            await _queue_chunk(chunk_queue, final_chunk, metrics)

        await chunk_queue.put(None)
        await chunk_queue.join()
        with suppress(asyncio.CancelledError):
            await encode_task

        replay.stop()
        replay_task.cancel()
        with suppress(asyncio.CancelledError):
            await replay_task
        await producer.stop()
        logger.info("edge_service_stopped", extra={"event_id": "", "camera_id": settings.camera_id})


if __name__ == "__main__":
    asyncio.run(run())
