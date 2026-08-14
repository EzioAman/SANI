"""SANI Continuous Voice Conversation Pipeline with Smart Intent Classification & Interruption Control.

CRITICAL RULE:
Voice inputs in this stage DO NOT have execution authority.
Vocal prompts are routed strictly to SANIAgent.chat() for conversational responses.
ToolRunner is NEVER invoked from the Voice Pipeline in this phase.
"""

import re
import time
from sani.agent import SANIAgent
from sani.models import UserIdentity
from sani.voice.intent import IntentCategory, SmartIntentClassifier
from sani.voice.player import AudioPlayer
from sani.voice.recorder import AudioRecorder
from sani.voice.stt import GeminiSTTProvider
from sani.voice.tts import AVAILABLE_VOICES, EdgeTTSProvider


class VoicePipeline:
    """Orchestrates the Hands-Free Vocal Loop: Microphone -> STT -> Smart Intent -> SANI -> TTS -> Speaker."""

    def __init__(
        self,
        agent: SANIAgent,
        stt_provider: GeminiSTTProvider | None = None,
        tts_provider: EdgeTTSProvider | None = None,
        recorder: AudioRecorder | None = None,
        player: AudioPlayer | None = None,
        intent_classifier: SmartIntentClassifier | None = None,
    ) -> None:
        self.agent = agent
        self.stt_provider = stt_provider or GeminiSTTProvider()
        self.tts_provider = tts_provider or EdgeTTSProvider()
        self.recorder = recorder or AudioRecorder()
        self.player = player or AudioPlayer()
        self.intent_classifier = intent_classifier or SmartIntentClassifier()

    def _handle_voice_commands(self, text: str, category: IntentCategory, user: UserIdentity) -> bool:
        """Handle hands-free vocal configuration commands in English & Hindi/Hinglish."""
        low = text.lower().strip()

        # 1. Microphone Options or Switching
        if category == IntentCategory.CONFIG_MIC:
            match_mic = re.search(r"(?:switch|change|set)\s+(?:mic|microphone|माइक|माइक्रोफोन)\s+(?:to\s+)?(\d+)", low)
            if match_mic:
                try:
                    idx = int(match_mic.group(1))
                    new_mic_name = self.recorder.set_microphone(idx)
                    msg = f"Microphone switched to device {new_mic_name}."
                    print(f"\nSANI (Hardware Settings) > {msg}\n")
                    self.speak_response(msg, user=user)
                    return True
                except Exception as e:
                    msg = f"Could not switch microphone: {e}"
                    print(f"\nSANI > {msg}\n")
                    self.speak_response(msg, user=user)
                    return True
            else:
                mics = AudioRecorder.get_available_microphones()
                if not mics:
                    msg = "No input microphones detected."
                    print(f"\nSANI (Hardware Settings) > {msg}\n")
                    self.speak_response(msg, user=user)
                else:
                    formatted = "\n  [Available Microphones]\n"
                    for m in mics:
                        is_active = "*" if self.recorder.device_index == m["index"] else " "
                        formatted += f"  {is_active} [{m['index']}] {m['name']} ({int(m['sample_rate'])} Hz)\n"
                    formatted += "\n  To switch, say: 'Switch mic to 1'"
                    print(formatted)
                    spoken = f"Available microphones are listed on screen. Say 'switch mic to number' to change device."
                    self.speak_response(spoken, user=user)
                return True

        # 2. Voice Options or Switching
        if category == IntentCategory.CONFIG_VOICE:
            for v_alias in sorted(AVAILABLE_VOICES.keys(), key=len, reverse=True):
                if re.search(r"\b" + re.escape(v_alias) + r"\b", low):
                    canonical_name = "Aria" if v_alias in ("aria", "arya", "aariya", "आर्या") else v_alias.capitalize()
                    self.tts_provider.set_voice(v_alias)
                    msg = f"Voice updated to {canonical_name}."
                    print(f"\nSANI (Voice Settings) > {msg}\n")
                    self.speak_response(msg, user=user)
                    return True

            voices = EdgeTTSProvider.get_available_voices()
            formatted = "\n  [Available Voice Models]\n"
            for name, desc in voices.items():
                is_active = "*" if name.lower() in self.tts_provider.voice.lower() else " "
                formatted += f"  {is_active} • {name:<12} - {desc}\n"
            formatted += "\n  To switch, say: 'Switch voice to Aria' or 'Use Prabhat voice'"
            print(formatted)
            spoken = f"Available voices are: Andrew, Aria, Guy, Jenny, Christopher, Neerja, Prabhat, Swara, and Madhur. Say 'switch voice to' followed by any name."
            self.speak_response(spoken, user=user)
            return True

        return False

    def speak_response(self, text: str, user: UserIdentity) -> bool:
        """Synthesize and stream text response to spoken audio sentence-by-sentence.
        
        Returns True if played to full completion, False if interrupted by user.
        """
        if not text:
            return True

        sentences = [s.strip() for s in re.split(r"(?<=[.!?।\n])\s+", text) if s.strip()]
        if not sentences:
            sentences = [text]

        for sentence in sentences:
            audio_bytes = self.tts_provider.text_to_speech(sentence)
            if audio_bytes:
                played_full = self.player.play_bytes(audio_bytes)
                if not played_full:
                    return False  # Interrupted by user!

        return True

    def process_single_turn(self, user: UserIdentity) -> bool:
        """Run a single vocal interaction turn.
        
        Returns False if session should end, True otherwise.
        """
        # Step 1: Microphone -> Audio Recording
        audio_bytes = self.recorder.record_until_silence(prompt_message=f"Listening to {user.name}...")
        if not audio_bytes:
            return True

        # Step 2: Speech-to-Text (STT)
        user_text = self.stt_provider.speech_to_text(audio_bytes)
        if not user_text or len(user_text.strip()) < 2:
            return True

        print(f"\n{user.name} (Voice) > {user_text}")

        # Step 3: Smart Intent Classification
        category = self.intent_classifier.classify(user_text)

        # Handle Exit Intent
        if category == IntentCategory.EXIT:
            print("[Voice] Exit intent classified. Ending voice session cleanly.")
            self.speak_response(f"Goodbye {user.name}. Going on standby.", user=user)
            return False

        # Handle Hardware / Voice Configuration Intents
        if category in (IntentCategory.CONFIG_VOICE, IntentCategory.CONFIG_MIC):
            if self._handle_voice_commands(user_text, category, user):
                return True

        # Step 4: Natural Conversation (CHAT) -> SANI Core (Informational Chat strictly)
        voice_prompt = (
            f"{user_text}\n\n[System Note for Voice Mode: Respond in a natural, concise, human spoken conversation style (1-3 sentences). Avoid code blocks or bullet lists.]"
        )
        response_text = self.agent.chat(prompt=voice_prompt, user=user)
        print(f"SANI > {response_text}\n")

        # Step 5: Text-to-Speech (TTS) -> Sentence Streamlike Output (with Barge-in Interruption)
        self.speak_response(response_text, user=user)
        return True

    def run_continuous_loop(self, user: UserIdentity) -> None:
        """Run 100% hands-free continuous voice conversation loop."""
        active_mic = self.recorder.get_active_microphone_name()
        active_voice = self.tts_provider.voice

        print(f"==================================================")
        print(f"  SANI Hands-Free Voice Loop Activated")
        print(f"  Owner:              {user.name}")
        print(f"  Active Microphone:  {active_mic}")
        print(f"  Active Voice Model: {active_voice}")
        print(f"  Intent Engine:      Smart Intent Classifier Active")
        print(f"  Barge-In Interruption: ENABLED (Speak anytime to interrupt)")
        print(f"  Exit Commands:      'exit', 'please exit', 'stop listening', 'take 5'")
        print(f"==================================================")
        
        welcome_msg = f"SANI voice loop online. I am listening, {user.name}."
        self.speak_response(welcome_msg, user=user)

        while True:
            try:
                should_continue = self.process_single_turn(user)
                if not should_continue:
                    break
                time.sleep(0.2)
            except (KeyboardInterrupt, EOFError):
                print("\n[Voice] Session ended.")
                break
