"""Smart Intent Classifier for Voice Conversations.

Distinguishes between natural conversation talk vs explicit system control commands
(voice model switching, microphone settings, exit, project audit, git push),
respecting conversational context and metaphors.
"""

from enum import Enum, auto
import re


class IntentCategory(Enum):
    """Voice Intent Categories."""
    CHAT = auto()           # Natural conversation talk -> routed to SANIAgent.chat()
    CONFIG_VOICE = auto()   # Voice options / voice model switching
    CONFIG_MIC = auto()     # Microphone options / input device switching
    GIT_PUSH = auto()       # Push project code to GitHub
    PROJECT_AUDIT = auto()  # Pre-push code audit & health check
    EXIT = auto()           # Exit / pause voice loop


class SmartIntentClassifier:
    """Classifies voice transcriptions into IntentCategory with conversational context awareness."""

    VOICE_KEYWORDS = ["voice", "voices", "आवाज़", "आवाज", "बोल"]
    MIC_KEYWORDS = ["mic", "microphone", "माइक्रोफोन", "माइक"]
    ACTION_KEYWORDS = [
        "option", "options", "list", "change", "switch", "show",
        "ऑप्शन", "विकल्प", "बदलो", "दिखाओ", "दिखा", "बताओ", "लगाओ", "set", "use"
    ]
    
    EXPLICIT_EXIT_PHRASES = [
        "exit voice chat", "exit voice", "stop listening", "sani stop listening",
        "end chat", "end voice session", "goodbye sani", "bye sani", "shut down voice",
        "please exit", "can you please stop listening", "stop listening now",
        "अलविदा", "सुनना बंद करो", "बंद करो एसएएनआई"
    ]

    GIT_PUSH_KEYWORDS = [
        "push to github", "upload to github", "push project", "push code",
        "upload code", "push the update", "upload project", "push github",
        "गिटहब पर पुश करो", "गिटहब अपलोड"
    ]
    AUDIT_KEYWORDS = [
        "check for missing components", "audit project", "check project",
        "check codebase", "pre-push check", "missing components"
    ]

    KNOWN_VOICE_ALIASES = [
        "andrew", "androo", "aria", "arya", "aariya", "guy", "jenny",
        "christopher", "chris", "neerja", "nirja", "prabhat", "prabat",
        "swara", "madhur", "प्रभात", "नीरजा", "आर्या", "एंड्रयू", "स्वरा", "मधुर"
    ]

    def classify(self, text: str) -> IntentCategory:
        """Classify input text string into an IntentCategory."""
        if not text or not text.strip():
            return IntentCategory.CHAT

        low = text.lower().strip()

        # 1. Explicit Exit Intent
        if any(phrase in low for phrase in self.EXPLICIT_EXIT_PHRASES):
            return IntentCategory.EXIT

        clean_punct = re.sub(r"[^\w\s]", "", low).strip()
        if clean_punct in ("exit", "quit", "goodbye", "bye"):
            return IntentCategory.EXIT

        if clean_punct in ("take 5", "take five", "stop", "sani stop") and not any(kw in low for kw in ["don't", "dont", "lol", "haha", "joking", "or just", "should we"]):
            return IntentCategory.EXIT

        # 2. Hardware / Voice Settings Configuration Intents (Highest Priority System Control)
        if any(v in low for v in self.VOICE_KEYWORDS) and any(a in low for a in self.ACTION_KEYWORDS):
            return IntentCategory.CONFIG_VOICE
        for alias in self.KNOWN_VOICE_ALIASES:
            if re.search(r"\b" + re.escape(alias) + r"\b", low):
                if any(act in low for act in ["voice", "switch", "change", "set", "use", "speak", "आवाज़", "आवाज", "बोल", "लगाओ", "बदलो"]):
                    return IntentCategory.CONFIG_VOICE

        if any(m in low for m in self.MIC_KEYWORDS) and any(a in low for a in self.ACTION_KEYWORDS):
            return IntentCategory.CONFIG_MIC
        if re.search(r"(?:switch|change|set)\s+(?:mic|microphone|माइक|माइक्रोफोन)\s+(?:to\s+)?\d+", low):
            return IntentCategory.CONFIG_MIC

        # 3. Git Push & Audit Intents
        if any(kw in low for kw in self.GIT_PUSH_KEYWORDS):
            return IntentCategory.GIT_PUSH

        if any(kw in low for kw in self.AUDIT_KEYWORDS):
            return IntentCategory.PROJECT_AUDIT

        # Default: Natural Conversation Talk
        return IntentCategory.CHAT
