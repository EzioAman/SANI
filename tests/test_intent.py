"""Unit tests for SmartIntentClassifier Subsystem."""

import pytest
from sani.voice.intent import IntentCategory, SmartIntentClassifier


@pytest.fixture
def classifier() -> SmartIntentClassifier:
    return SmartIntentClassifier()


def test_classify_chat_conversations(classifier: SmartIntentClassifier) -> None:
    assert classifier.classify("Hello SANI how are you today?") == IntentCategory.CHAT
    assert classifier.classify("What is the capital of France?") == IntentCategory.CHAT
    assert classifier.classify("नमस्ते अमन कैसे हो?") == IntentCategory.CHAT


def test_classify_voice_config_intents(classifier: SmartIntentClassifier) -> None:
    assert classifier.classify("Switch voice to Arya") == IntentCategory.CONFIG_VOICE
    assert classifier.classify("Can you show me voice options?") == IntentCategory.CONFIG_VOICE
    assert classifier.classify("प्रभात आवाज लगाओ") == IntentCategory.CONFIG_VOICE


def test_classify_mic_config_intents(classifier: SmartIntentClassifier) -> None:
    assert classifier.classify("Show me microphone options") == IntentCategory.CONFIG_MIC
    assert classifier.classify("Switch mic to 1") == IntentCategory.CONFIG_MIC
    assert classifier.classify("माइक्रोफोन के ऑप्शन दिखाओ") == IntentCategory.CONFIG_MIC


def test_classify_exit_intents(classifier: SmartIntentClassifier) -> None:
    assert classifier.classify("Please exit") == IntentCategory.EXIT
    assert classifier.classify("Can you please stop listening?") == IntentCategory.EXIT
    assert classifier.classify("take 5") == IntentCategory.EXIT
    assert classifier.classify("अलविदा") == IntentCategory.EXIT
