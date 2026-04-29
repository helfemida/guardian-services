import numpy as np

from app.chunk.chunk_builder import Chunk
from app.encode.ffmpeg_encoder import FfmpegEncoder


def test_encoder_falls_back_until_success(tmp_path, monkeypatch) -> None:
    attempted_codecs: list[str] = []

    def fake_run(cmd: list[str], chunk: Chunk) -> None:
        codec = cmd[cmd.index("-c:v") + 1]
        attempted_codecs.append(codec)
        if codec != "libx264":
            raise RuntimeError("codec not available")

    monkeypatch.setattr(FfmpegEncoder, "_run_ffmpeg", staticmethod(fake_run))
    monkeypatch.setattr(FfmpegEncoder, "_resolve_ffmpeg_executable", staticmethod(lambda: "ffmpeg-test"))

    encoder = FfmpegEncoder(tmp_path)
    clip = encoder.encode(_chunk(), "event-1")

    assert clip.encoder == "libx264"
    assert attempted_codecs == ["h264_qsv", "h264_nvenc", "libx264"]


def test_encoder_uses_imageio_ffmpeg_when_system_ffmpeg_is_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.encode.ffmpeg_encoder.shutil.which", lambda _: None)

    class FakeImageioFfmpeg:
        @staticmethod
        def get_ffmpeg_exe() -> str:
            return "bundled-ffmpeg"

    monkeypatch.setitem(__import__("sys").modules, "imageio_ffmpeg", FakeImageioFfmpeg)

    encoder = FfmpegEncoder(tmp_path)

    assert encoder.ffmpeg_executable == "bundled-ffmpeg"


def _chunk() -> Chunk:
    frame = np.zeros((16, 16, 3), dtype=np.uint8)
    return Chunk(
        captured_at=_utc_now(),
        fps=2,
        frames=[frame.copy(), frame.copy()],
        duration_sec=1.0,
        start_ts=0.0,
        end_ts=1.0,
    )


def _utc_now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)
