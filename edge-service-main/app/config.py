import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Settings(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    rtsp_url: str = Field(alias="RTSP_URL")
    rtsp_transport: str = Field(default="tcp", alias="RTSP_TRANSPORT")
    rtsp_ffmpeg_capture_options: str | None = Field(default=None, alias="RTSP_FFMPEG_CAPTURE_OPTIONS")
    rtsp_open_timeout_ms: int = Field(default=10000, alias="RTSP_OPEN_TIMEOUT_MS")
    rtsp_read_timeout_ms: int = Field(default=15000, alias="RTSP_READ_TIMEOUT_MS")
    camera_id: str = Field(alias="CAMERA_ID")
    facility_id: str = Field(alias="FACILITY_ID")

    target_fps: int | None = Field(default=None, alias="TARGET_FPS")
    capture_fps: int | None = Field(default=None, alias="CAPTURE_FPS")
    trigger_fps: int | None = Field(default=None, alias="TRIGGER_FPS")
    output_fps: int | None = Field(default=None, alias="OUTPUT_FPS")
    chunk_duration_sec: int = Field(default=4, alias="CHUNK_DURATION_SEC")
    prebuffer_sec: float = Field(default=0.5, alias="PREBUFFER_SEC")
    person_grace_sec: float = Field(default=0.5, alias="PERSON_GRACE_SEC")
    motion_threshold: float = Field(default=15.0, alias="MOTION_THRESHOLD")
    motion_min_ratio: float = Field(default=0.01, alias="MOTION_MIN_RATIO")
    motion_global_max_ratio: float = Field(default=0.75, alias="MOTION_GLOBAL_MAX_RATIO")
    enable_person_gating: bool = Field(default=True, alias="ENABLE_PERSON_GATING")
    person_model_path: str = Field(default="./data/models/yolov8n.pt", alias="PERSON_MODEL_PATH")
    person_detector_confidence: float = Field(default=0.25, alias="PERSON_DETECTOR_CONFIDENCE")
    person_min_box_height_ratio: float = Field(default=0.05, alias="PERSON_MIN_BOX_HEIGHT_RATIO")
    yolo_config_dir: Path = Field(default=Path("./data/ultralytics"), alias="YOLO_CONFIG_DIR")

    schema_version: str = Field(default="1.0", alias="SCHEMA_VERSION")

    minio_endpoint: str = Field(alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="violence-media", alias="MINIO_BUCKET")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    kafka_bootstrap_servers: str = Field(alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic_raw: str = Field(default="raw-media-events", alias="KAFKA_TOPIC_RAW")
    kafka_client_id: str = Field(default="edge-service", alias="KAFKA_CLIENT_ID")
    kafka_host_aliases: str | None = Field(default=None, alias="KAFKA_HOST_ALIASES")

    offline_db_path: Path = Field(default=Path("./data/outbox.db"), alias="OFFLINE_DB_PATH")
    local_media_dir: Path = Field(default=Path("./data/chunks"), alias="LOCAL_MEDIA_DIR")

    max_retry_attempts: int = Field(default=5, alias="MAX_RETRY_ATTEMPTS")
    retry_base_sec: float = Field(default=1.0, alias="RETRY_BASE_SEC")
    replay_poll_sec: float = Field(default=2.0, alias="REPLAY_POLL_SEC")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("chunk_duration_sec")
    @classmethod
    def validate_chunk_duration(cls, value: int) -> int:
        if value < 3 or value > 5:
            raise ValueError("CHUNK_DURATION_SEC must be between 3 and 5")
        return value

    @field_validator(
        "target_fps",
        "capture_fps",
        "trigger_fps",
        "output_fps",
        "max_retry_attempts",
        "rtsp_open_timeout_ms",
        "rtsp_read_timeout_ms",
    )
    @classmethod
    def validate_positive_int(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("value must be > 0")
        return value

    @field_validator(
        "prebuffer_sec",
        "person_grace_sec",
        "motion_threshold",
        "motion_min_ratio",
        "retry_base_sec",
        "replay_poll_sec",
    )
    @classmethod
    def validate_positive_float(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("value must be > 0")
        return value

    @field_validator("motion_global_max_ratio")
    @classmethod
    def validate_motion_global_max_ratio(cls, value: float) -> float:
        if value <= 0 or value > 1:
            raise ValueError("MOTION_GLOBAL_MAX_RATIO must be within (0, 1]")
        return value

    @field_validator(
        "person_detector_confidence",
        "person_min_box_height_ratio",
    )
    @classmethod
    def validate_unit_interval(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("value must be within [0, 1]")
        return value

    @field_validator("camera_id", "facility_id", "rtsp_url", "kafka_bootstrap_servers", "minio_endpoint")
    @classmethod
    def validate_required(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("required setting is empty")
        return value.strip()

    @field_validator("person_model_path")
    @classmethod
    def normalize_model_path(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("person detector model path is empty")
        return normalized

    @field_validator("rtsp_transport")
    @classmethod
    def validate_rtsp_transport(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"auto", "tcp", "udp"}:
            raise ValueError("RTSP_TRANSPORT must be one of: auto, tcp, udp")
        return normalized

    @field_validator("rtsp_ffmpeg_capture_options", "kafka_host_aliases")
    @classmethod
    def validate_rtsp_ffmpeg_capture_options(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def normalize_person_detector_settings(self) -> "Settings":
        fallback_fps = self.target_fps
        if self.capture_fps is None:
            self.capture_fps = fallback_fps if fallback_fps is not None else 20
        if self.trigger_fps is None:
            self.trigger_fps = fallback_fps if fallback_fps is not None else 5
        if self.output_fps is None:
            self.output_fps = fallback_fps if fallback_fps is not None else 20
        if self.target_fps is None:
            self.target_fps = self.output_fps
        if self.motion_global_max_ratio <= self.motion_min_ratio:
            raise ValueError("MOTION_GLOBAL_MAX_RATIO must be greater than MOTION_MIN_RATIO")
        return self


def load_settings(env_file: str | Path = ".env") -> Settings:
    merged = _load_merged_settings(env_file)
    return Settings.model_validate(merged)


def prime_videoio_environment(env_file: str | Path = ".env") -> None:
    env_file_path = Path(env_file)
    merged = _load_merged_settings(env_file)
    capture_options = merged.get("RTSP_FFMPEG_CAPTURE_OPTIONS")
    if not capture_options:
        transport = str(merged.get("RTSP_TRANSPORT", "tcp")).strip().lower()
        if transport != "auto":
            capture_options = f"rtsp_transport;{transport}"

    if capture_options and "OPENCV_FFMPEG_CAPTURE_OPTIONS" not in os.environ:
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = str(capture_options)

    if "YOLO_CONFIG_DIR" not in os.environ:
        raw_yolo_dir = merged.get("YOLO_CONFIG_DIR", "./data/ultralytics")
        resolved_yolo_dir = _resolve_path(env_file_path, raw_yolo_dir)
        resolved_yolo_dir.mkdir(parents=True, exist_ok=True)
        os.environ["YOLO_CONFIG_DIR"] = str(resolved_yolo_dir)


def _load_merged_settings(env_file: str | Path) -> dict[str, Any]:
    env_file_path = Path(env_file)
    dotenv_values = _read_dotenv_file(env_file_path)

    yaml_hint = (
        os.environ.get("SETTINGS_YAML")
        or dotenv_values.get("SETTINGS_YAML")
        or os.environ.get("CONFIG_YAML_PATH")
        or dotenv_values.get("CONFIG_YAML_PATH")
    )
    yaml_values = _read_yaml_file(_resolve_path(env_file_path, yaml_hint)) if yaml_hint else {}

    merged: dict[str, Any] = {}
    merged.update(_normalize_known_keys(yaml_values))
    merged.update(_normalize_known_keys(dotenv_values))
    merged.update(_normalize_known_keys(dict(os.environ)))
    return merged


def _normalize_known_keys(values: Mapping[str, Any]) -> dict[str, Any]:
    name_to_alias = {
        name: (field.alias or name)
        for name, field in Settings.model_fields.items()
    }
    aliases = set(name_to_alias.values())
    normalized: dict[str, Any] = {}
    for key, value in values.items():
        if key in aliases:
            normalized[key] = value
        elif key in name_to_alias:
            normalized[name_to_alias[key]] = value
    return normalized


def _read_dotenv_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        value = raw_value.strip()
        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _read_yaml_file(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        yaml = None

    if not path.exists():
        raise FileNotFoundError(f"settings yaml not found: {path}")

    raw_text = path.read_text(encoding="utf-8")
    if yaml is None:
        return _parse_simple_yaml(raw_text)

    data = yaml.safe_load(raw_text) or {}
    if not isinstance(data, dict):
        raise ValueError("SETTINGS_YAML must contain a top-level mapping")
    return data


def _resolve_path(env_file_path: Path, raw_path: str | os.PathLike[str] | None) -> Path:
    if raw_path is None:
        return env_file_path
    path = Path(raw_path)
    if path.is_absolute():
        return path
    base_dir = env_file_path.parent if env_file_path.parent != Path("") else Path.cwd()
    return (base_dir / path).resolve()


def _parse_simple_yaml(raw_text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        value = raw_value.strip()
        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values

