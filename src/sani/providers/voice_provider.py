"""Abstract Interface for Replaceable Voice Providers (Commandment 7)."""

from abc import ABC, abstractmethod


class VoiceProvider(ABC):
    """Abstract interface for Speech-to-Text (STT) and Text-to-Speech (TTS)."""

    @abstractmethod
    def speech_to_text(self, audio_bytes: bytes) -> str:
        """Convert audio stream/bytes into transcribed text."""
        pass

    @abstractmethod
    def text_to_speech(self, text: str) -> bytes:
        """Synthesize text into audio bytes."""
        pass

    @abstractmethod
    def is_interrupted(self) -> bool:
        """Check if incoming user speech interrupted current TTS audio playback."""
        pass


class DefaultVoiceProvider(VoiceProvider):
    """Fallback / Mock voice provider implementation."""

    def speech_to_text(self, audio_bytes: bytes) -> str:
        return "[Audio Transcribed]"

    def text_to_speech(self, text: str) -> bytes:
        return b"[Mock Audio Bytes]"

    def is_interrupted(self) -> bool:
        return False
