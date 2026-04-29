import os

import pytest

from app.config import Settings, load_settings, prime_videoio_environment


def test_settings_validation_chunk_duration() -> None:
    with pytest.raises(ValueError):
        Settings(
            rtsp_url="rtsp://x",
            camera_id="c",
            facility_id="f",
            minio_endpoint="http://m",
            minio_access_key="a",
            minio_secret_key="s",
            kafka_bootstrap_servers="localhost:9092",
            chunk_duration_sec=6,
        )


def test_settings_default_to_yolo_person_detector() -> None:
    settings = Settings(
        rtsp_url="rtsp://x",
        camera_id="c",
        facility_id="f",
        minio_endpoint="http://m",
        minio_access_key="a",
        minio_secret_key="s",
        kafka_bootstrap_servers="localhost:9092",
    )

    assert settings.person_model_path == "./data/models/yolov8n.pt"
    assert settings.person_detector_confidence == 0.25
    assert settings.person_min_box_height_ratio == 0.05
    assert settings.motion_global_max_ratio == 0.75
    assert settings.capture_fps == 20
    assert settings.trigger_fps == 5
    assert settings.output_fps == 20
    assert settings.prebuffer_sec == 0.5
    assert settings.person_grace_sec == 0.5


def test_settings_fall_back_to_target_fps_when_explicitly_set() -> None:
    settings = Settings(
        rtsp_url="rtsp://x",
        camera_id="c",
        facility_id="f",
        minio_endpoint="http://m",
        minio_access_key="a",
        minio_secret_key="s",
        kafka_bootstrap_servers="localhost:9092",
        target_fps=4,
    )

    assert settings.capture_fps == 4
    assert settings.trigger_fps == 4
    assert settings.output_fps == 4


def test_settings_allow_zero_person_detector_confidence() -> None:
    settings = Settings(
        rtsp_url="rtsp://x",
        camera_id="c",
        facility_id="f",
        minio_endpoint="http://m",
        minio_access_key="a",
        minio_secret_key="s",
        kafka_bootstrap_servers="localhost:9092",
        person_detector_confidence=0.0,
    )

    assert settings.person_detector_confidence == 0.0


def test_settings_allow_zero_min_box_height_ratio() -> None:
    settings = Settings(
        rtsp_url="rtsp://x",
        camera_id="c",
        facility_id="f",
        minio_endpoint="http://m",
        minio_access_key="a",
        minio_secret_key="s",
        kafka_bootstrap_servers="localhost:9092",
        person_min_box_height_ratio=0.0,
    )

    assert settings.person_min_box_height_ratio == 0.0


def test_settings_allow_custom_person_model_path() -> None:
    settings = Settings(
        rtsp_url="rtsp://x",
        camera_id="c",
        facility_id="f",
        minio_endpoint="http://m",
        minio_access_key="a",
        minio_secret_key="s",
        kafka_bootstrap_servers="localhost:9092",
        person_model_path="./data/models/custom-yolo.pt",
    )

    assert settings.person_model_path == "./data/models/custom-yolo.pt"


def test_settings_validate_motion_global_max_ratio_above_motion_min_ratio() -> None:
    with pytest.raises(ValueError):
        Settings(
            rtsp_url="rtsp://x",
            camera_id="c",
            facility_id="f",
            minio_endpoint="http://m",
            minio_access_key="a",
            minio_secret_key="s",
            kafka_bootstrap_servers="localhost:9092",
            motion_min_ratio=0.05,
            motion_global_max_ratio=0.05,
        )


def test_settings_allow_kafka_host_aliases() -> None:
    settings = Settings(
        rtsp_url="rtsp://x",
        camera_id="c",
        facility_id="f",
        minio_endpoint="http://m",
        minio_access_key="a",
        minio_secret_key="s",
        kafka_bootstrap_servers="localhost:9092",
        kafka_host_aliases="kafka=10.0.0.5,broker=10.0.0.6",
    )

    assert settings.kafka_host_aliases == "kafka=10.0.0.5,broker=10.0.0.6"


def test_load_settings_yaml_overlay_with_env_precedence(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    yaml_path = tmp_path / "settings.yaml"
    yaml_path.write_text(
        "\n".join(
            [
                "RTSP_URL: rtsp://yaml/cam0",
                "CAMERA_ID: yaml-camera",
                "FACILITY_ID: yaml-facility",
                "MINIO_ENDPOINT: http://yaml-minio:9000",
                "MINIO_ACCESS_KEY: yaml-access",
                "MINIO_SECRET_KEY: yaml-secret",
                "KAFKA_BOOTSTRAP_SERVERS: yaml-kafka:9092",
            ]
        ),
        encoding="utf-8",
    )

    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SETTINGS_YAML=settings.yaml",
                "RTSP_URL=rtsp://dotenv/cam0",
                "MINIO_ACCESS_KEY=dotenv-access",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("CAMERA_ID", "env-camera")
    settings = load_settings(env_path)

    assert settings.rtsp_url == "rtsp://dotenv/cam0"
    assert settings.camera_id == "env-camera"
    assert settings.facility_id == "yaml-facility"
    assert settings.minio_access_key == "dotenv-access"


def test_prime_videoio_environment_prefers_rtsp_transport(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "RTSP_URL=rtsp://dotenv/cam0",
                "CAMERA_ID=cam",
                "FACILITY_ID=facility",
                "MINIO_ENDPOINT=http://minio:9000",
                "MINIO_ACCESS_KEY=access",
                "MINIO_SECRET_KEY=secret",
                "KAFKA_BOOTSTRAP_SERVERS=kafka:9092",
                "RTSP_TRANSPORT=tcp",
                "YOLO_CONFIG_DIR=./runtime/ultralytics",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.delenv("OPENCV_FFMPEG_CAPTURE_OPTIONS", raising=False)
    monkeypatch.delenv("YOLO_CONFIG_DIR", raising=False)

    prime_videoio_environment(env_path)

    assert os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] == "rtsp_transport;tcp"
    assert os.environ["YOLO_CONFIG_DIR"] == str((tmp_path / "runtime" / "ultralytics").resolve())
