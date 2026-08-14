"""Smart Intent Classifier for Voice Conversations.

Distinguishes between natural conversation talk vs system control commands
(voice model switching, microphone settings, exit, project audit, git push).
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

        # 1. Exit Intent
        if any(kw in low for kw in self.EXIT_KEYWORDS):
            return IntentCategory.EXIT

        # 2. Git Push Intent
        if any(kw in low for kw in self.GIT_PUSH_KEYWORDS):
            return IntentCategory.GIT_PUSH

        # 3. Project Audit Intent
        if any(kw in low for kw in self.AUDIT_KEYWORDS):
            return IntentCategory.PROJECT_AUDIT

        # 4. Microphone Configuration Intent
        if any(m in low for m in self.MIC_KEYWORDS) and any(a in low for a in self.ACTION_KEYWORDS):
            return IntentCategory.CONFIG_MIC
        if re.search(r"(?:switch|change|set)\s+(?:mic|microphone|माइक|माइक्रोफोन)\s+(?:to\s+)?\d+", low):
            return IntentCategory.CONFIG_MIC

        # 5. Voice Configuration Intent
        if any(v in low for v in self.VOICE_KEYWORDS) and any(a in low for a in self.ACTION_KEYWORDS):
            return IntentCategory.CONFIG_VOICE
        for alias in self.KNOWN_VOICE_ALIASES:
            if re.search(r"\b" + re.escape(alias) + r"\b", low):
                if any(act in low for act in ["voice", "switch", "change", "set", "use", "speak", "आवाज़", "आवाज", "बोल", "लगाओ", "बदलो"]):
                    return IntentCategory.CONFIG_VOICE

        # Default: Natural Conversation Talk
        return IntentCategory.CHAT
