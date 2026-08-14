"""Abstract Interface for Replaceable Model Providers (Commandment 6)."""

from abc import ABC, abstractmethod
from typing import Any
import openai
from google import genai
from google.genai import types


class LLMProvider(ABC):
    """Abstract interface for LLM inference (OpenAI, Gemini, Azure, Local models)."""

    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: str = "", tools: list[Any] | None = None) -> str:
        """Generate response text from model."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini model provider implementation using official google-genai Chat interface."""

    def __init__(self, api_key: str, model: str = "gemini-3.1-flash-lite") -> None:
        self.api_key = api_key
        self.model = model
        self._client: genai.Client | None = None
        self._chat: Any = None
        self._current_system_prompt: str = ""

        if self.api_key:
            self._client = genai.Client(api_key=self.api_key)

    def _get_chat(self, system_prompt: str) -> Any:
        """Create or reuse Chat session with system instruction."""
        if not self._client:
            return None
        if self._chat is None or self._current_system_prompt != system_prompt:
            config_obj = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None
            )
            try:
                self._chat = self._client.chats.create(
                    model=self.model,
                    config=config_obj,
                )
            except Exception:
                # Fallback model if target model is unavailable
                self._chat = self._client.chats.create(
                    model="gemini-3.1-flash-lite",
                    config=config_obj,
                )
            self._current_system_prompt = system_prompt
        return self._chat

    def generate_response(self, prompt: str, system_prompt: str = "", tools: list[Any] | None = None) -> str:
        if not self._client:
            return (
                "[System Notice: Gemini API key is missing. Set GEMINI_API_KEY in your .env file.]"
            )

        try:
            chat_session = self._get_chat(system_prompt)
            response = chat_session.send_message(prompt)
            return response.text or ""
        except Exception as e:
            err_str = str(e)
            if "PERMISSION_DENIED" in err_str or "403" in err_str:
                return (
                    f"[Gemini API Error: Permission Denied (403). "
                    f"Please check that your GEMINI_API_KEY in .env is a valid key from Google AI Studio (https://aistudio.google.com/app/apikey). Details: {err_str}]"
                )
            if "INVALID_ARGUMENT" in err_str or "API_KEY_INVALID" in err_str or "400" in err_str:
                return (
                    f"[Gemini API Error: API Key Invalid (400). "
                    f"The key in .env was rejected by Google. Details: {err_str}]"
                )
            if "404" in err_str or "NOT_FOUND" in err_str:
                try:
                    config_obj = types.GenerateContentConfig(
                        system_instruction=system_prompt if system_prompt else None
                    )
                    fallback_chat = self._client.chats.create(
                        model="gemini-3.1-flash-lite",
                        config=config_obj,
                    )
                    response = fallback_chat.send_message(prompt)
                    return response.text or ""
                except Exception as fb_err:
                    return f"[Gemini API Error: {fb_err}]"
            return f"[Gemini API Error: {err_str}]"


class OpenAIProvider(LLMProvider):
    """OpenAI model provider implementation utilizing official OpenAI SDK."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self.api_key = api_key
        self.model = model
        self._client: openai.OpenAI | None = None

        if self.api_key:
            self._client = openai.OpenAI(api_key=self.api_key)

    def generate_response(self, prompt: str, system_prompt: str = "", tools: list[Any] | None = None) -> str:
        if not self._client:
            return (
                "[System Notice: OpenAI API key is missing. Set OPENAI_API_KEY in your environment or .env file to enable live model testing.]"
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI API Error: {e}]"
