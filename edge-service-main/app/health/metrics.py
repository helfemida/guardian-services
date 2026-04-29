from dataclasses import dataclass


@dataclass
class Metrics:
    frames_captured_total: int = 0
    frames_sampled_total: int = 0
    motion_pass_total: int = 0
    person_pass_total: int = 0
    raw_person_detections_total: int = 0
    person_rejected_confidence_total: int = 0
    person_rejected_box_size_total: int = 0
    person_accepted_total: int = 0
    triggers_total: int = 0
    chunks_created_total: int = 0
    encode_failures_total: int = 0
    upload_failures_total: int = 0
    kafka_failures_total: int = 0
    replayed_total: int = 0
    reconnect_attempts_total: int = 0
    rtsp_connected: bool = False
    outbox_pending_count: int = 0
    trigger_checks_total: int = 0
    trigger_loop_lag_sec: float = 0.0
    raw_chunk_queue_size: int = 0
    last_encode_latency_sec: float = 0.0
    effective_chunk_fps: float = 0.0
    delivery_attempt_failures_total: int = 0
    overload_block_total: int = 0
