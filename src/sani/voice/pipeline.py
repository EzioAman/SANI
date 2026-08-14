"""SANI Continuous Voice Conversation Pipeline with Startup Hardware Chooser & Live Volume Display.

CRITICAL RULE:
High-risk operations (such as pushing code to GitHub) require explicit Aman confirmation
evaluated through the SANI AuthorityEngine.
"""

import re
import time
from sani.agent import SANIAgent
from sani.command_router import CommandRouter
from sani.models import InputOrigin, UserIdentity
from sani.tools.git_tool import GitTool
from sani.voice.intent import IntentCategory, SmartIntentClassifier
from sani.voice.player import AudioPlayer
from sani.voice.recorder import AudioRecorder
from sani.voice.settings import VoiceSettingsManager
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
        git_tool: GitTool | None = None,
        settings_mgr: VoiceSettingsManager | None = None,
    ) -> None:
        self.agent = agent
        self.settings_mgr = settings_mgr or VoiceSettingsManager(workspace_root=agent.config.workspace_root)
        
        saved_voice = self.settings_mgr.get_voice()
        saved_mic = self.settings_mgr.get_mic_index()

        self.stt_provider = stt_provider or GeminiSTTProvider()
        self.tts_provider = tts_provider or EdgeTTSProvider(voice=saved_voice)
        self.recorder = recorder or AudioRecorder(device_index=saved_mic)
        self.player = player or AudioPlayer(input_device=saved_mic)
        self.intent_classifier = intent_classifier or SmartIntentClassifier()
        self.command_router = CommandRouter(agent, self.intent_classifier)
        self.git_tool = git_tool or GitTool()

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
                    return False  # Interrupted by user mid-sentence!

        return True

    def speak_stream(self, text_stream, user: UserIdentity) -> bool:
        """Turn genuine provider deltas into clause/sentence-sized TTS requests immediately while printing live text output."""
        print("\nSANI (Voice) > ", end="", flush=True)
        pending = ""
        for delta in text_stream:
            print(delta, end="", flush=True)
            pending += delta
            if len(pending) > 30:
                parts = re.split(r"(?<=[.!?।])\s+|(?:(?<=[,;:—])\s+)", pending)
            else:
                parts = re.split(r"(?<=[.!?।])\s+", pending)
            pending = parts.pop()
            for sentence in parts:
                if sentence.strip() and not self.speak_response(sentence.strip(), user):
                    print()
                    return False
        res = not pending.strip() or self.speak_response(pending.strip(), user)
        print()
        return res

    def display_startup_hardware_and_voice_config(self) -> None:
        """Display active hardware, available microphones, and voice actors at startup."""
        mics = AudioRecorder.get_available_microphones()
        voices = EdgeTTSProvider.get_available_voices()
        active_mic = self.recorder.get_active_microphone_name()
        active_voice = self.tts_provider.voice

        print(f"\n==================================================")
        print(f"  SANI Voice Subsystem Startup Configuration")
        print(f"==================================================")
        print(f"  [Active Settings]")
        print(f"  • Active Microphone:  {active_mic}")
        print(f"  • Active Voice Actor: {active_voice.split('-')[2].replace('Neural', '')} ({active_voice})")
        
        print(f"\n  [Available Microphones]")
        for m in mics[:6]:
            is_act = "*" if self.recorder.device_index == m["index"] else " "
            print(f"  {is_act} [{m['index']}] {m['name']}")

        print(f"\n  [Available Voice Actors]")
        for name, desc in voices.items():
            is_act = "*" if name.lower() in active_voice.lower() else " "
            print(f"  {is_act} • {name:<12} - {desc}")
        print(f"==================================================")

    def _run_project_audit(self, user: UserIdentity) -> None:
        """Report the real repository state without modifying or pushing it."""
        workspace_root = str(self.agent.config.workspace_root)
        branch = self.git_tool.get_current_branch(workspace_root) or "detached HEAD"
        remote_url = self.git_tool.get_remote_url(workspace_root) or "No origin remote configured"
        status_text = self.git_tool.status(workspace_root)
        commit_log = self.git_tool.get_commit_log(workspace_root, count=1) or "No commits found"
        print("\n[SANI Audit Engine] Repository state:")
        print(f"  • Branch: {branch}\n  • Commit: {commit_log}\n  • Remote: {remote_url}\n  • Status: {status_text or 'clean'}")
        state = "is clean" if "nothing to commit" in status_text.lower() else "has local changes"
        self.speak_response(f"Project audit complete. Branch {branch} {state}. I have not changed or pushed anything.", user=user)

    def _execute_handsfree_git_push(self, user: UserIdentity) -> None:
        """Start the shared, voice-origin confirmation flow for a GitHub push."""
        outcome = self.command_router.handle("push the update to github", user, InputOrigin.VOICE)
        self.speak_response(outcome.message, user=user)

    def _handle_voice_commands(self, text: str, category: IntentCategory, user: UserIdentity) -> bool:
        """Handle hands-free vocal configuration & project control commands."""
        low = text.lower().strip()

        # 1. GitHub Push / Project Audit Command
        if category == IntentCategory.GIT_PUSH:
            self._execute_handsfree_git_push(user)
            return True
        if category == IntentCategory.PROJECT_AUDIT:
            self._run_project_audit(user)
            return True

        # 2. Microphone Options or Switching with a short hardware capture check
        if category == IntentCategory.CONFIG_MIC:
            match_mic = re.search(r"(?:switch|change|set)\s+(?:mic|microphone|माइक|माइक्रोफोन)\s+(?:to\s+)?(\d+)", low)
            if match_mic:
                try:
                    idx = int(match_mic.group(1))
                    ok, hardware_info = self.settings_mgr.test_microphone_hardware_confidence(idx)
                    if ok:
                        self.recorder.set_microphone(idx)
                        self.player.input_device = idx
                        self.settings_mgr.set_mic_index(idx)
                        msg = f"Microphone hardware check passed. Active device updated to {hardware_info}."
                        print(f"\nSANI (Hardware Check Passed) > {msg}\n")
                        self.speak_response(msg, user=user)
                    else:
                        msg = f"Hardware test failed for mic index {idx}: {hardware_info}"
                        print(f"\nSANI (Hardware Error) > {msg}\n")
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

        # 3. Voice Options or Switching with Persistent Voice Actor Storage
        if category == IntentCategory.CONFIG_VOICE:
            canonical_map = {
                "en-US-AndrewNeural": "Andrew",
                "en-US-AriaNeural": "Aria",
                "en-US-GuyNeural": "Guy",
                "en-US-JennyNeural": "Jenny",
                "en-US-ChristopherNeural": "Christopher",
                "en-IN-NeerjaNeural": "Neerja",
                "en-IN-PrabhatNeural": "Prabhat",
                "hi-IN-SwaraNeural": "Swara",
                "hi-IN-MadhurNeural": "Madhur",
            }
            for v_alias in sorted(AVAILABLE_VOICES.keys(), key=len, reverse=True):
                if re.search(r"\b" + re.escape(v_alias) + r"\b", low):
                    new_voice_id = self.tts_provider.set_voice(v_alias)
                    self.settings_mgr.set_voice(new_voice_id)
                    canonical_name = canonical_map.get(new_voice_id, v_alias.capitalize())
                    msg = f"Voice actor updated to {canonical_name} and saved to persistent settings."
                    print(f"\nSANI (Voice Settings Saved) > {msg}\n")
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

    def process_single_turn(self, user: UserIdentity) -> bool:
        """Run a single vocal interaction turn.
        
        Returns False if session should end, True otherwise.
        """
        # Step 1: Microphone -> Audio Recording with Live Level Display
        audio_bytes = self.recorder.record_until_silence(prompt_message=f"Awaiting vocal input...")
        if not audio_bytes:
            return True

        # Step 2: Speech-to-Text (STT)
        user_text = self.stt_provider.speech_to_text(audio_bytes)
        if not user_text or len(user_text.strip()) < 2:
            return True

        print(f"\n{user.name} (Voice) > {user_text}")

        # Step 3: Shared intent and command routing. This never lets the model execute tools.
        outcome = self.command_router.handle(user_text, user, InputOrigin.VOICE)
        if outcome.handled:
            print(f"SANI > {outcome.message}")
            self.speak_response(outcome.message, user=user)
            return True
        category = outcome.assessment.category if outcome.assessment else self.intent_classifier.classify(user_text)

        # Handle Exit Intent
        if category == IntentCategory.EXIT:
            print("[Voice] Exit intent classified. Ending voice session cleanly.")
            self.speak_response(f"Goodbye {user.name}. Going on standby.", user=user)
            return False

        # Handle Hardware, Voice & Git Push Configuration Intents
        if category in (IntentCategory.CONFIG_VOICE, IntentCategory.CONFIG_MIC, IntentCategory.GIT_PUSH, IntentCategory.PROJECT_AUDIT):
            if self._handle_voice_commands(user_text, category, user):
                return True

        # Step 4: Natural Conversation (CHAT) -> SANI Core
        voice_prompt = (
            f"{user_text}\n\n[System Note for Voice Mode: Respond in a natural, concise, human spoken conversation style (1-3 sentences). Avoid code blocks or bullet lists.]"
        )
        # Step 5: Gemini/OpenAI provider deltas feed TTS before the response is complete.
        self.speak_stream(self.agent.chat_stream(prompt=voice_prompt, user=user), user=user)
        return True

    def run_continuous_loop(self, user: UserIdentity) -> None:
        """Run 100% hands-free continuous voice conversation loop."""
        self.display_startup_hardware_and_voice_config()

        active_voice = self.tts_provider.voice
        welcome_msg = f"SANI voice loop online. Active voice is {active_voice.split('-')[2].replace('Neural', '')}. I am listening, {user.name}."
        try:
            self.speak_response(welcome_msg, user=user)
        except Exception:
            pass

        while True:
            try:
                should_continue = self.process_single_turn(user)
                if not should_continue:
                    break
                time.sleep(0.2)
            except (KeyboardInterrupt, EOFError):
                print("\n[Voice] Session ended.")
                break
