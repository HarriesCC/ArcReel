"""真实 FFmpeg 烧录字幕，验证画面变化与原声音轨保留。"""

import hashlib
import shutil
import subprocess

import pytest

from tests.unit.test_compose_video_filter_graph import compose_video


def test_burn_subtitles_preserves_audio_and_changes_only_captioned_frames(tmp_path):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("需要 ffmpeg 和 ffprobe")
    try:
        compose_video.require_subtitle_filter()
    except RuntimeError:
        pytest.skip("需要支持 libass 的 ffmpeg")

    source = tmp_path / "original.mp4"
    output = tmp_path / "captioned.mp4"
    srt = tmp_path / "字幕'含特殊字符.srt"
    subprocess.run(
        compose_video.resolved_command(
            [
                "ffmpeg",
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=black:s=360x640:r=24:d=2",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-shortest",
                str(source),
            ]
        ),
        check=True,
    )
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\n字幕测试 Hello\n", encoding="utf-8")
    compose_video.burn_subtitle_file(source, srt, output, font="sans-serif")

    def audio_hash(path):
        result = subprocess.run(
            compose_video.resolved_command(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(path),
                    "-map",
                    "0:a",
                    "-c:a",
                    "copy",
                    "-f",
                    "adts",
                    "-",
                ]
            ),
            capture_output=True,
            check=True,
        )
        return hashlib.sha256(result.stdout).hexdigest()

    def frame(path, time):
        return subprocess.run(
            compose_video.resolved_command(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-ss",
                    str(time),
                    "-i",
                    str(path),
                    "-frames:v",
                    "1",
                    "-pix_fmt",
                    "gray",
                    "-f",
                    "rawvideo",
                    "-",
                ]
            ),
            capture_output=True,
            check=True,
        ).stdout

    assert audio_hash(source) == audio_hash(output)
    assert max(frame(output, 0.5)) > 200
    assert max(frame(output, 1.5)) < 10
    assert compose_video.probe_media(output)["duration"] == pytest.approx(2, abs=0.05)
