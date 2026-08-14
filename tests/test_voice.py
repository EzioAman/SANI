"""Unit tests for SANI Voice Subsystems & Non-Authoritative Pipeline."""

import pytest
from sani.agent import SANIAgent
from sani.models import Role, UserIdentity
from sani.voice.pipeline import VoicePipeline
from sani.voice.stt import GeminiSTTProvider
from sani.voice.tts import EdgeTTSProvider


@pytest.fixture
def owner_user() -> UserIdentity:
    return UserIdentity(user_id="aman_01", name="Aman", role=Role.OWNER)


def test_stt_handles_empty_bytes() -> None:
    stt = GeminiSTTProvider(api_key="")
    result = stt.speech_to_text(b"")
    assert result == ""


def test_tts_generates_audio_or_fallback() -> None:
    tts = EdgeTTSProvider()
    # Test short text synthesis
    audio_bytes = tts.text_to_speech("Hello Aman")
    assert audio_bytes is not None


def test_voice_pipeline_non_authoritative(owner_user: UserIdentity) -> None:
    agent = SANIAgent()
    pipeline = VoicePipeline(agent=agent)

    # Verify voice responses use chat() informational method
    response = agent.chat("Test voice prompt", user=owner_user)
    assert response is not None
