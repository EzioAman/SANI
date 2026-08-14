"""Deterministic, conservative intent assessment for conversational interfaces."""

from dataclasses import dataclass
from enum import Enum, auto
import re


class IntentCategory(Enum):
    CHAT = auto()
    CONFIG_VOICE = auto()
    CONFIG_MIC = auto()
    GIT_PUSH = auto()
    PROJECT_AUDIT = auto()
    EXIT = auto()


class IntentKind(Enum):
    CONVERSATIONAL = auto()
    INFORMATIONAL = auto()
    EXPLICIT_COMMAND = auto()
    AMBIGUOUS = auto()
    HIGH_RISK_COMMAND = auto()
    CONFIRMATION = auto()
    CANCELLATION = auto()


@dataclass(frozen=True)
class IntentAssessment:
    category: IntentCategory
    kind: IntentKind
    action: str | None = None
    confidence: float = 0.0
    reason: str = ""


class SmartIntentClassifier:
    """Recognize only clear commands; command-like discussion remains conversation."""

    _NEGATED_OR_REPORTED = re.compile(
        r"\b(?:don't|do not|dont|never|not|joking|joke|said|quoted|quote|if|should|why|what happens)\b|[\"']",
        re.IGNORECASE,
    )
    _AMBIGUOUS = re.compile(
        r"^(?:oh\s+)?(?:please\s+)?(?:stop|cancel|abort|shutdown|kill it|that's enough|leave it|forget it|never mind|go ahead|do it|yeah do that|push that)\b",
        re.IGNORECASE,
    )
    _EXIT = re.compile(r"^(?:(?:can you)\s+)?(?:please\s+)?(?:sani,?\s+)?(?:exit(?: voice (?:mode|chat)?)?|stop listening|end voice session)\s*[.!?]?$", re.IGNORECASE)
    _PUSH = re.compile(
        r"\b(?:push|upload)\b.*\bgithub\b"
        r"|\b(?:push|upload)\s+(?:the\s+)?(?:latest\s+)?(?:update|this|changes|code|project|repo|repository|branch\s+\S+)?\s+(?:to\s+)?github\b",
        re.IGNORECASE,
    )
    _AUDIT = re.compile(r"\b(?:audit|check)\s+(?:the\s+)?(?:project|codebase)\b", re.IGNORECASE)
    _VOICE_NAMES = r"(?:andrew|androo|aria|arya|aariya|guy|gai|gi|jenny|jennifer|christopher|chris|neerja|nirja|prabhat|prabat|swara|madhur|प्रभात|नीरजा|आर्या|एंड्रयू|स्वरा|मधुर)"
    
    _VOICE = re.compile(
        r"\b(?:voice|voices)\b.*\b(?:change|switch|set|use|select|list|show|option|options|actor|model|preset|setting|settings)\b"
        r"|\b(?:change|switch|set|use|select|list|show|speak in|speak with)\b.*\b(?:voice|voices|voice actor)\b"
        r"|\b(?:switch|change|set|use|select)\s+(?:to\s+)?(?:the\s+)?(?:voice\s+of\s+)?" + _VOICE_NAMES + r"\b",
        re.IGNORECASE,
    )
    _MIC = re.compile(
        r"\b(?:mic|microphone|microphones)\b.*\b(?:change|switch|set|use|select|list|show|option|options|input|device|setting|settings)\b"
        r"|\b(?:change|switch|set|use|select|list|show)\b.*\b(?:mic|microphone|microphones)\b",
        re.IGNORECASE,
    )

    def assess(self, text: str) -> IntentAssessment:
        value = text.strip()
        if not value:
            return IntentAssessment(IntentCategory.CHAT, IntentKind.CONVERSATIONAL)
        low = value.lower()
        if self._NEGATED_OR_REPORTED.search(value) and any(word in low for word in ("push", "upload", "stop", "exit")):
            return IntentAssessment(IntentCategory.CHAT, IntentKind.CONVERSATIONAL, reason="negated, quoted, or hypothetical")
        if self._EXIT.fullmatch(value):
            return IntentAssessment(IntentCategory.EXIT, IntentKind.EXPLICIT_COMMAND, "exit_voice", 1.0, "direct exit phrase")
        if low in {"take 5", "take five", "अलविदा"}:
            return IntentAssessment(IntentCategory.EXIT, IntentKind.EXPLICIT_COMMAND, "exit_voice", 0.9, "explicit break request")
        if self._PUSH.search(value):
            return IntentAssessment(IntentCategory.GIT_PUSH, IntentKind.HIGH_RISK_COMMAND, "git_push", 1.0, "direct GitHub push request")
        if self._AUDIT.search(value):
            return IntentAssessment(IntentCategory.PROJECT_AUDIT, IntentKind.INFORMATIONAL, "project_audit", 0.95)
        if re.fullmatch(r"(?:can you )?show me voice options\??", low) or "आवाज लगाओ" in low:
            return IntentAssessment(IntentCategory.CONFIG_VOICE, IntentKind.INFORMATIONAL, "set_voice", 0.9)
        if re.fullmatch(r"show me (?:microphone|mic) options\??", low) or "माइक्रोफोन के ऑप्शन" in low:
            return IntentAssessment(IntentCategory.CONFIG_MIC, IntentKind.INFORMATIONAL, "set_microphone", 0.9)
        if self._VOICE.search(value):
            return IntentAssessment(IntentCategory.CONFIG_VOICE, IntentKind.EXPLICIT_COMMAND, "set_voice", 0.9)
        if self._MIC.search(value):
            return IntentAssessment(IntentCategory.CONFIG_MIC, IntentKind.EXPLICIT_COMMAND, "set_microphone", 0.9)
        if self._AMBIGUOUS.search(value):
            return IntentAssessment(IntentCategory.CHAT, IntentKind.AMBIGUOUS, confidence=0.45, reason="command needs context")
        return IntentAssessment(IntentCategory.CHAT, IntentKind.CONVERSATIONAL)

    def classify(self, text: str) -> IntentCategory:
        """Compatibility API; callers requiring safety context use :meth:`assess`."""
        return self.assess(text).category
