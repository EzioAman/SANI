"""Text-to-Speech (TTS) Subsystem with Human-like Neural Voices and Automatic Multilingual Routing."""

import asyncio
import io
import re
import edge_tts
import pyttsx3
from sani.voice.text_cleaner import clean_text_for_speech


AVAILABLE_VOICES: dict[str, str] = {
    # English names & phonetic aliases
    "andrew": "en-US-AndrewNeural",
    "androo": "en-US-AndrewNeural",
    "aria": "en-US-AriaNeural",
    "arya": "en-US-AriaNeural",
    "aariya": "en-US-AriaNeural",
    "guy": "en-US-GuyNeural",
    "jenny": "en-US-JennyNeural",
    "christopher": "en-US-ChristopherNeural",
    "chris": "en-US-ChristopherNeural",
    "neerja": "en-IN-NeerjaNeural",
    "nirja": "en-IN-NeerjaNeural",
    "prabhat": "en-IN-PrabhatNeural",
    "prabat": "en-IN-PrabhatNeural",
    "swara": "hi-IN-SwaraNeural",
    "madhur": "hi-IN-MadhurNeural",
    # Hindi script aliases
    "प्रभात": "en-IN-PrabhatNeural",
    "नीरजा": "en-IN-NeerjaNeural",
    "आर्या": "en-US-AriaNeural",
    "एंड्रयू": "en-US-AndrewNeural",
    "स्वरा": "hi-IN-SwaraNeural",
    "मधुर": "hi-IN-MadhurNeural",
}


class EdgeTTSProvider:
    """Human-like Text-to-Speech using warm conversational neural voices with automatic language routing."""

    def __init__(self, voice: str = "en-US-AndrewNeural") -> None:
        self.voice = voice
        self._offline_engine: pyttsx3.Engine | None = None

    @staticmethod
    def get_available_voices() -> dict[str, str]:
        """Return dict of friendly voice names to voice identifiers."""
        return {
            "Andrew": "Male, Warm Conversational (US)",
            "Aria": "Female, Natural Conversational (US)",
            "Guy": "Male, Clear Professional (US)",
            "Jenny": "Female, Expressive (US)",
            "Christopher": "Male, Deep Conversational (US)",
            "Neerja": "Female, Natural Accent (India)",
            "Prabhat": "Male, Natural Accent (India)",
            "Swara": "Female, Natural Hindi / English (India)",
            "Madhur": "Male, Natural Hindi / English (India)",
        }

    def set_voice(self, voice_name_or_id: str) -> str:
        """Switch active TTS voice model."""
        key = voice_name_or_id.lower().strip()
        if key in AVAILABLE_VOICES:
            self.voice = AVAILABLE_VOICES[key]
        else:
            self.voice = voice_name_or_id
        return self.voice

    async def _generate_edge_tts_bytes(self, text: str, voice: str) -> bytes:
        clean_text = clean_text_for_speech(text)
        if not clean_text:
            return b""

        communicate = edge_tts.Communicate(clean_text, voice, rate="+0%", pitch="+0Hz")
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        return audio_stream.getvalue()

    def text_to_speech(self, text: str) -> bytes:
        """Synthesize text string into natural human-sounding audio bytes."""
        clean_text = clean_text_for_speech(text)
        if not clean_text:
            return b""

        # Detect Hindi / Devanagari script and auto-route to a Hindi-compatible voice model
        target_voice = self.voice
        if re.search(r"[\u0900-\u097F]", clean_text):
            if "en-US" in self.voice or "en-GB" in self.voice:
                if any(female_name in self.voice for female_name in ["Aria", "Jenny"]):
                    target_voice = "hi-IN-SwaraNeural"
                else:
                    target_voice = "hi-IN-MadhurNeural"

        try:
            return asyncio.run(self._generate_edge_tts_bytes(clean_text, voice=target_voice))
        except Exception as e:
            print(f"[TTS Notice: Falling back to offline TTS - {e}]")
            return self._speak_offline(clean_text)

    def _speak_offline(self, text: str) -> bytes:
        try:
            if self._offline_engine is None:
                self._offline_engine = pyttsx3.init()
                self._offline_engine.setProperty("rate", 170)
            self._offline_engine.say(text)
            self._offline_engine.runAndWait()
        except Exception as exc:
            # A missing/locked SAPI voice must not crash the conversation loop.
            print(f"[TTS Warning: Offline fallback unavailable - {exc}]")
        return b""
