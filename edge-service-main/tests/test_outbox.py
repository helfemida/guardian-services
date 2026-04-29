from pathlib import Path

from app.outbox.sqlite_outbox import SqliteOutbox


def test_outbox_state_transition(tmp_path: Path) -> None:
    outbox = SqliteOutbox(tmp_path / "outbox.db")
    item_id = outbox.add(
        local_media_path=str(tmp_path / "a.mp4"),
        bucket="b",
        object_key="k",
        payload={"event_id": "1"},
        state="pending_upload",
    )
    pending = outbox.get_pending()
    assert pending[0].id == item_id
    outbox.update_state(item_id, "uploaded_pending_kafka")
    assert outbox.get_pending()[0].state == "uploaded_pending_kafka"


def test_outbox_respects_next_attempt_at(tmp_path: Path) -> None:
    outbox = SqliteOutbox(tmp_path / "outbox.db")
    outbox.add(
        local_media_path=str(tmp_path / "a.mp4"),
        bucket="b",
        object_key="k",
        payload={"event_id": "1"},
        state="pending_upload",
        next_attempt_at=10.0,
    )

    assert outbox.get_pending(now_ts=0.0) == []
    assert len(outbox.get_pending(now_ts=10.0)) == 1
