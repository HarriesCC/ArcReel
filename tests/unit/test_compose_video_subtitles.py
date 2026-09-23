"""单集字幕使用真实媒体边界与统一语义规则。"""

import pytest

from tests.unit.test_compose_video_filter_graph import compose_video


def scene(*texts: str) -> dict:
    return {
        "scene_id": "E1S01",
        "duration_seconds": 99,
        "utterances": [{"kind": "dialogue", "speaker": "陆沉", "text": text} for text in texts],
    }


def test_subtitles_follow_actual_boundaries_including_silent_scenes():
    result = compose_video.build_episode_srt([scene("快走", "别回头啊"), scene(), scene("门关上")], [3, 2, 1.25])
    assert result == (
        "1\n00:00:00,000 --> 00:00:01,000\n快走\n\n"
        "2\n00:00:01,000 --> 00:00:03,000\n别回头啊\n\n"
        "3\n00:00:05,000 --> 00:00:06,250\n门关上\n"
    )


def test_voiceover_requires_presentation_audio():
    voiceover = {"scene_id": "E1S01", "utterances": [{"kind": "voiceover", "speaker": None, "text": "夜幕降临"}]}
    with pytest.raises(ValueError, match="需要配音"):
        compose_video.build_episode_srt([voiceover], [3])


@pytest.mark.parametrize("duration", [0, -1, float("nan"), float("inf")])
def test_invalid_media_duration_rejected(duration):
    with pytest.raises(ValueError, match="实际片段时长"):
        compose_video.build_episode_srt([scene("走")], [duration])


def test_subtitle_text_cannot_inject_formatting_or_extra_cues():
    result = compose_video.build_episode_srt([scene("{\\an8}<i>快走</i>\n\n再见")], [2])
    assert "{\\an8}" not in result
    assert "<i>" not in result
    assert "&lt;i&gt;快走&lt;/i&gt; 再见" in result
    assert result.count(" --> ") == 1
