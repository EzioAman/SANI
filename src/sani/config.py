"""SANI Configuration Management."""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Automatically load environment variables from .env file if present
load_dotenv()


class SANIConfig(BaseModel):
    """Central configuration for SANI core, model providers, workspace boundaries, and voice settings."""

    # Owner / Primary Authority Settings
    owner_name: str = Field(default="Aman", description="Primary owner and highest authority user.")
    
    # Model Provider Settings
    llm_api_key: str = Field(
        default_factory=lambda: (
            os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        ),
        description="LLM API key loaded from LLM_API_KEY or fallback keys.",
    )
    gemini_api_key: str = Field(
        default_factory=lambda: (
            os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
        ),
        description="Gemini API key loaded from LLM_API_KEY, GEMINI_API_KEY, or GOOGLE_API_KEY.",
    )
    openai_api_key: str = Field(
        default_factory=lambda: os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI API key loaded from LLM_API_KEY or OPENAI_API_KEY.",
    )
    
    # Active Provider and Model Choice
    provider: str = Field(
        default_factory=lambda: (
            "gemini" if (os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) else "openai"
        ),
        description="Active provider choice ('gemini' or 'openai').",
    )
    model_name: str = Field(default="gemini-3.1-flash-lite", description="Default reasoning LLM model name.")
    
    # Storage & Workspace Settings
    workspace_root: Path = Field(
        default_factory=lambda: Path(os.getenv("SANI_WORKSPACE_ROOT", "E:/Projects/SANI")).resolve(),
        description="Allowed root directory for file operations.",
    )
    db_path: Path = Field(
        default_factory=lambda: Path(os.getenv("SANI_DB_PATH", "E:/Projects/SANI/sani_memory.db")).resolve(),
        description="Path to SQLite persistence database.",
    )
    
    # Voice Settings
    voice_enabled: bool = Field(default=False, description="Whether voice I/O is enabled.")
    stt_provider: str = Field(default="whisper", description="Speech-to-text provider name.")
    tts_provider: str = Field(default="openai", description="Text-to-speech provider name.")
    
    # Action Confirmation Settings
    auto_confirm_low_risk: bool = Field(
        default=True, description="Whether low-risk actions can execute without manual confirmation."
    )


_config_instance: SANIConfig | None = None


def get_config() -> SANIConfig:
    """Retrieve singleton SANI configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = SANIConfig()
    return _config_instance
