from botocore.config import Config

from app.storage.minio_client import MinioClient


class DummySettings:
    minio_endpoint = "http://minio:9000"
    minio_access_key = "access"
    minio_secret_key = "secret"
    minio_secure = False
    max_retry_attempts = 3
    retry_base_sec = 1.0


def test_minio_client_disables_proxy_usage(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_boto3_client(service_name: str, **kwargs):
        captured["service_name"] = service_name
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("app.storage.minio_client.boto3.client", fake_boto3_client)

    MinioClient(DummySettings())

    assert captured["service_name"] == "s3"
    config = captured["kwargs"]["config"]
    assert isinstance(config, Config)
    assert config.proxies == {}
