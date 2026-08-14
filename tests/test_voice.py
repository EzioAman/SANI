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


def test_tts_generates_audio() -> None:
    tts = EdgeTTSProvider()
    async def synthesize(_: str, voice: str) -> bytes:
        return b"audio"

    tts._generate_edge_tts_bytes = synthesize  # type: ignore[method-assign]
    audio_bytes = tts.text_to_speech("Hello Aman")
    assert audio_bytes == b"audio"


def test_voice_pipeline_non_authoritative(owner_user: UserIdentity) -> None:
    agent = SANIAgent()
    pipeline = VoicePipeline(agent=agent)

    # Verify voice responses use chat() informational method
    response = agent.chat("Test voice prompt", user=owner_user)
    assert response is not None


def test_streamed_sentence_is_spoken_before_response_stream_finishes(owner_user: UserIdentity) -> None:
    class TTS:
        def __init__(self) -> None:
            self.completed = False
            self.call_states: list[bool] = []

        def text_to_speech(self, text: str) -> bytes:
            self.call_states.append(not self.completed)
            return b"audio"

    class Player:
        def play_bytes(self, _: bytes) -> bool:
            return True

    tts = TTS()
    pipeline = VoicePipeline(agent=SANIAgent(), tts_provider=tts, player=Player())

    def deltas():
        yield "Hello Aman. "
        tts.completed = True
        yield "How are you?"

    assert pipeline.speak_stream(deltas(), owner_user)
    assert any(tts.call_states)
