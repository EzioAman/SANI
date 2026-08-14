"""Speech-to-Text (STT) Subsystem utilizing Gemini Multimodal Audio Processing with Retry."""

import time
from google import genai
from google.genai import types
from sani.config import get_config


class GeminiSTTProvider:
    """Transcribes audio bytes to text using Gemini audio capabilities via Chat API with retry logic."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-3.1-flash-lite") -> None:
        self.config = get_config()
        self.api_key = api_key or self.config.gemini_api_key or self.config.openai_api_key
        self.model = model
        self._client: genai.Client | None = None

        if self.api_key:
            self._client = genai.Client(api_key=self.api_key)

    def speech_to_text(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """Convert recorded audio bytes into transcribed text string with retry backoff."""
        if not audio_bytes or len(audio_bytes) < 100:
            return ""

        if not self._client:
            return "[Mock STT Transcript: Hello SANI]"

        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        prompt = (
            "Listen to the user audio and output ONLY the exact spoken transcription text. "
            "Do not add commentary, metadata, or punctuation notes."
        )

        for attempt in range(3):
            try:
                chat = self._client.chats.create(model=self.model)
                response = chat.send_message([audio_part, prompt])
                return (response.text or "").strip()
            except Exception as e:
                err_str = str(e)
                if ("503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str) and attempt < 2:
                    print(f"[STT Notice: High demand 503 error, retrying STT attempt {attempt + 2}/3...]")
                    time.sleep(1.0 * (attempt + 1))
                    continue
                print(f"[STT Error: {e}]")
                return ""

        return ""
