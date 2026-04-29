import asyncio
import json
import socket

import pytest

from app.contracts.raw_event import RawMediaEvent
from app.messaging.kafka_producer import (
    KafkaRawProducer,
    _KAFKA_HOST_ALIAS_MAP,
    _ORIGINAL_GETADDRINFO,
    _parse_host_aliases,
    _patched_getaddrinfo,
)


class DummySettings:
    kafka_bootstrap_servers = "kafka:29092"
    kafka_client_id = "edge-service"
    kafka_topic_raw = "raw-media-events"
    kafka_host_aliases = None
    camera_id = "camera-1"


class FakeProducer:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.started = False
        self.stopped = False
        self.sent: list[dict[str, object]] = []

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def send_and_wait(self, topic: str, key: bytes, value: bytes) -> None:
        self.sent.append({"topic": topic, "key": key, "value": value})


def test_kafka_producer_publishes_raw_event(monkeypatch) -> None:
    created: dict[str, object] = {}

    def fake_aiokafka_producer(**kwargs) -> FakeProducer:
        producer = FakeProducer(**kwargs)
        created["producer"] = producer
        return producer

    monkeypatch.setattr("app.messaging.kafka_producer.AIOKafkaProducer", fake_aiokafka_producer)

    kafka = KafkaRawProducer(DummySettings())
    event = RawMediaEvent(
        facility_id="facility-1",
        camera_id="camera-1",
        bucket="violence-media",
        object_key="f47ac10b/c9876a5e/2026-04-16/9999999999_chunk.mp4",
        duration_sec=4.0,
        captured_at="2026-04-16T00:00:00.000Z",
        edge_ingested_at="2026-04-16T00:00:01.000Z",
    )

    asyncio.run(kafka.publish(event))

    producer = created["producer"]
    assert producer.kwargs == {
        "bootstrap_servers": "kafka:29092",
        "acks": "all",
        "client_id": "edge-service",
    }
    assert producer.started is True
    assert producer.sent[0]["topic"] == "raw-media-events"
    assert producer.sent[0]["key"] == b"camera-1"
    assert json.loads(producer.sent[0]["value"].decode("utf-8"))["bucket"] == "violence-media"


def test_parse_kafka_host_aliases() -> None:
    assert _parse_host_aliases("kafka=10.0.0.5, broker=10.0.0.6") == {
        "kafka": "10.0.0.5",
        "broker": "10.0.0.6",
    }


def test_parse_kafka_host_aliases_rejects_invalid_entry() -> None:
    with pytest.raises(ValueError):
        _parse_host_aliases("kafka")


def test_patched_getaddrinfo_uses_alias_map(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_getaddrinfo(host, port, *args, **kwargs):
        captured["host"] = host
        captured["port"] = port
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", port))]

    monkeypatch.setattr("app.messaging.kafka_producer._ORIGINAL_GETADDRINFO", fake_getaddrinfo)
    _KAFKA_HOST_ALIAS_MAP.clear()
    _KAFKA_HOST_ALIAS_MAP["kafka"] = "10.0.0.5"

    result = _patched_getaddrinfo("kafka", 29092)

    assert captured == {"host": "10.0.0.5", "port": 29092}
    assert result[0][4] == ("10.0.0.5", 29092)
    _KAFKA_HOST_ALIAS_MAP.clear()
