from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class RawMediaEvent(BaseModel):
    schema_version: str = "1.0"
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    facility_id: str
    camera_id: str
    bucket: str
    object_key: str
    content_type: str = "video/mp4"
    duration_sec: float
    captured_at: str
    edge_ingested_at: str = Field(default_factory=lambda: utc_isoformat(datetime.now(timezone.utc)))

    def kafka_key(self) -> bytes:
        return self.camera_id.encode("utf-8")
