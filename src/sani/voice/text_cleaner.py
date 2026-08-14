"""Text Cleaning Subsystem to ensure TTS sounds human and natural."""

import re


def clean_text_for_speech(text: str) -> str:
    """Clean markdown formatting, code blocks, URLs, and symbols for natural human speech."""
    if not text:
        return ""

    # Remove code blocks ```...```
    text = re.sub(r"```[\s\S]*?```", " Code snippet omitted. ", text)
    
    # Remove inline code `...`
    text = re.sub(r"`([^`]+)`", r"\1", text)
    
    # Remove markdown headers (# Header)
    text = re.sub(r"#+\s*", "", text)
    
    # Remove bold/italic (*text* or **text** or _text_)
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
    
    # Remove markdown links [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    
    # Remove raw URLs
    text = re.sub(r"https?://\S+", "link", text)
    
    # Remove bullet points/dashes at line start
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    
    # Normalize multiple whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text
