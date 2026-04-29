import asyncio
import logging
import socket

from aiokafka import AIOKafkaProducer

from app.config import Settings
from app.contracts.raw_event import RawMediaEvent

logger = logging.getLogger(__name__)
_ORIGINAL_GETADDRINFO = socket.getaddrinfo
_KAFKA_HOST_ALIAS_MAP: dict[str, str] = {}


def _parse_host_aliases(raw_aliases: str | None) -> dict[str, str]:
    if raw_aliases is None:
        return {}

    aliases: dict[str, str] = {}
    for raw_entry in raw_aliases.split(","):
        entry = raw_entry.strip()
        if not entry:
            continue
        host, separator, target = entry.partition("=")
        if not separator or not host.strip() or not target.strip():
            raise ValueError(f"invalid KAFKA_HOST_ALIASES entry: {entry!r}")
        aliases[host.strip().lower()] = target.strip()
    return aliases


def _patched_getaddrinfo(host, port, *args, **kwargs):
    if isinstance(host, str):
        alias = _KAFKA_HOST_ALIAS_MAP.get(host.lower())
        if alias is not None:
            return _ORIGINAL_GETADDRINFO(alias, port, *args, **kwargs)
    return _ORIGINAL_GETADDRINFO(host, port, *args, **kwargs)


def _install_host_aliases(raw_aliases: str | None) -> dict[str, str]:
    aliases = _parse_host_aliases(raw_aliases)
    if not aliases:
        return {}

    _KAFKA_HOST_ALIAS_MAP.update(aliases)
    if socket.getaddrinfo is not _patched_getaddrinfo:
        socket.getaddrinfo = _patched_getaddrinfo
    return aliases


class KafkaRawProducer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        installed_aliases = _install_host_aliases(settings.kafka_host_aliases)
        if installed_aliases:
            logger.info(
                "kafka_host_aliases_installed aliases=%s",
                installed_aliases,
                extra={"event_id": "", "camera_id": settings.camera_id},
            )
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            acks="all",
            client_id=settings.kafka_client_id,
        )
        self._started = False

    async def start(self) -> None:
        if not self._started:
            await self._producer.start()
            self._started = True

    async def stop(self) -> None:
        if self._started:
            await self._producer.stop()
            self._started = False

    async def publish(self, event: RawMediaEvent) -> None:
        if not self._started:
            await self.start()
        payload = event.model_dump_json().encode("utf-8")
        await self._producer.send_and_wait(
            topic=self.settings.kafka_topic_raw,
            key=event.kafka_key(),
            value=payload,
        )
        await asyncio.sleep(0)
