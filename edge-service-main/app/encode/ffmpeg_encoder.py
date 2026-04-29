import subprocess
from dataclasses import dataclass
from pathlib import Path
import shutil

from app.chunk.chunk_builder import Chunk


@dataclass(frozen=True)
class EncodedClip:
    path: Path
    encoder: str


class FfmpegEncoder:
    CODEC_CHAIN = ["h264_qsv", "h264_nvenc", "libx264"]

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_executable = self._resolve_ffmpeg_executable()

    def encode(self, chunk: Chunk, file_stem: str) -> EncodedClip:
        if not chunk.frames:
            raise ValueError("cannot encode empty chunk")

        frame_height, frame_width = chunk.frames[0].shape[:2]
        output_path = self.output_dir / f"{file_stem}.mp4"
        last_error: Exception | None = None
        for codec in self.CODEC_CHAIN:
            try:
                cmd = [
                    self.ffmpeg_executable,
                    "-y",
                    "-f",
                    "rawvideo",
                    "-pix_fmt",
                    "bgr24",
                    "-s",
                    f"{frame_width}x{frame_height}",
                    "-r",
                    str(chunk.fps),
                    "-i",
                    "pipe:0",
                    "-an",
                    "-c:v",
                    codec,
                    "-pix_fmt",
                    "yuv420p",
                    str(output_path),
                ]
                self._run_ffmpeg(cmd, chunk)
                return EncodedClip(path=output_path, encoder=codec)
            except Exception as exc:
                output_path.unlink(missing_ok=True)
                last_error = exc

        raise RuntimeError("ffmpeg encode failed for all codecs") from last_error

    @staticmethod
    def _resolve_ffmpeg_executable() -> str:
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            return system_ffmpeg

        try:
            import imageio_ffmpeg
        except ImportError:
            return "ffmpeg"
        return imageio_ffmpeg.get_ffmpeg_exe()

    @staticmethod
    def _run_ffmpeg(cmd: list[str], chunk: Chunk) -> None:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        try:
            assert process.stdin is not None
            for frame in chunk.frames:
                process.stdin.write(frame.tobytes())
            process.stdin.close()
            stderr_output = process.stderr.read() if process.stderr is not None else b""
            return_code = process.wait()
        except Exception:
            process.kill()
            process.wait()
            raise

        if return_code != 0:
            raise RuntimeError(stderr_output.decode("utf-8", errors="ignore").strip() or "ffmpeg exited with non-zero status")
