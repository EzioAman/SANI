"""Smart Intent Classifier for Voice Conversations.

Distinguishes between natural conversation talk vs system control commands
(voice model switching, microphone hardware settings, exit session).
"""

from enum import Enum, auto
import re


class IntentCategory(Enum):
    """Voice Intent Categories."""
    CHAT = auto()          # Natural conversation talk -> routed to SANIAgent.chat()
    CONFIG_VOICE = auto()  # Voice options / voice model switching
    CONFIG_MIC = auto()    # Microphone options / input device switching
    EXIT = auto()          # Exit / pause voice loop


class SmartIntentClassifier:
    """Classifies voice transcriptions into IntentCategory."""

    VOICE_KEYWORDS = ["voice", "voices", "आवाज़", "आवाज", "बोल"]
    MIC_KEYWORDS = ["mic", "microphone", "माइक्रोफोन", "माइक"]
    ACTION_KEYWORDS = [
        "option", "options", "list", "change", "switch", "show",
        "ऑप्शन", "विकल्प", "बदलो", "दिखाओ", "दिखा", "बताओ", "लगाओ", "set", "use"
    ]
    EXIT_KEYWORDS = [
        "exit", "quit", "goodbye", "stop listening", "end chat",
        "exit voice chat", "exit voice", "take 5", "take a break",
        "pause voice", "bye", "shut down", "please exit",
        "can you please stop listening", "stop listening now",
        "अलविदा", "बंद करो", "स्टॉप", "सुनना बंद करो", "जा रही हूँ", "बंद कर रही हूँ"
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

        # 1. Exit Intent
        if any(kw in low for kw in self.EXIT_KEYWORDS):
            return IntentCategory.EXIT

        # 2. Microphone Configuration Intent
        if any(m in low for m in self.MIC_KEYWORDS) and any(a in low for a in self.ACTION_KEYWORDS):
            return IntentCategory.CONFIG_MIC
        if re.search(r"(?:switch|change|set)\s+(?:mic|microphone|माइक|माइक्रोफोन)\s+(?:to\s+)?\d+", low):
            return IntentCategory.CONFIG_MIC

        # 3. Voice Configuration Intent
        if any(v in low for v in self.VOICE_KEYWORDS) and any(a in low for a in self.ACTION_KEYWORDS):
            return IntentCategory.CONFIG_VOICE
        for alias in self.KNOWN_VOICE_ALIASES:
            if re.search(r"\b" + re.escape(alias) + r"\b", low):
                if any(act in low for act in ["voice", "switch", "change", "set", "use", "speak", "आवाज़", "आवाज", "बोल", "लगाओ", "बदलो"]):
                    return IntentCategory.CONFIG_VOICE

        # Default: Natural Conversation Talk
        return IntentCategory.CHAT
