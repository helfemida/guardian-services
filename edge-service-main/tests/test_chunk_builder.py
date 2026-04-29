from app.chunk.chunk_builder import ChunkBuilder, FrameSample


def test_chunk_builder_emits_fixed_size_chunk_from_trigger_time() -> None:
    builder = ChunkBuilder(fps=2, chunk_duration_sec=4)
    assert builder.start([_sample(0.5, 1)]) is True

    chunk = None
    for ts in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5):
        chunk = builder.push(_sample(ts, int(ts * 10)))

    assert chunk is not None
    assert chunk.duration_sec == 4.0
    assert len(chunk.frames) == 8
    assert chunk.fps == 2.0
    assert builder.is_recording is True


def test_chunk_builder_emits_back_to_back_chunks_while_recording() -> None:
    builder = ChunkBuilder(fps=2, chunk_duration_sec=4)
    assert builder.start([_sample(0.0, 0)]) is True

    emitted = []
    for ts in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0):
        chunk = builder.push(_sample(ts, int(ts * 10)))
        if chunk is not None:
            emitted.append(chunk)

    assert len(emitted) == 2
    assert all(chunk.duration_sec == 4.0 for chunk in emitted)
    assert all(chunk.fps == 2.0 for chunk in emitted)
    assert builder.is_recording is True


def test_chunk_builder_flushes_partial_chunk_when_recording_stops() -> None:
    builder = ChunkBuilder(fps=2, chunk_duration_sec=4)
    assert builder.start([_sample(1.0, 1)]) is True

    for ts in (1.5, 2.0, 2.5):
        assert builder.push(_sample(ts, int(ts * 10))) is None

    chunk = builder.finish()

    assert chunk is not None
    assert chunk.duration_sec == 2.0
    assert len(chunk.frames) == 4
    assert chunk.fps == 2.0
    assert builder.is_recording is False


def test_chunk_builder_reports_best_effort_fps_when_capture_is_irregular() -> None:
    builder = ChunkBuilder(fps=20, chunk_duration_sec=4)
    assert builder.start([_sample(0.0, 0)]) is True

    for ts in (0.08, 0.17, 0.26, 0.35):
        assert builder.push(_sample(ts, int(ts * 100))) is None

    chunk = builder.finish()

    assert chunk is not None
    assert chunk.duration_sec > 0.0
    assert chunk.fps < 20.0


def _sample(ts: float, value: int) -> FrameSample:
    import numpy as np

    return FrameSample(ts=ts, frame=np.full((8, 8, 3), value, dtype=np.uint8))
