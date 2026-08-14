"""Voice & Hardware Settings Subsystem with Persistent Storage."""

import json
import os
import sounddevice as sd


SETTINGS_FILE = "voice_settings.json"


class VoiceSettingsManager:
    """Manages persistent voice model and microphone selection across SANI sessions."""

    def __init__(self, workspace_root: str = "E:/Projects/SANI") -> None:
        self.workspace_root = workspace_root
        self.file_path = os.path.join(workspace_root, SETTINGS_FILE)
        self.settings = self.load_settings()

    def load_settings(self) -> dict:
        """Load settings from JSON file or return defaults."""
        defaults = {
            "active_voice": "en-US-AriaNeural",
            "active_mic_index": None,
            "interruption_sensitivity": "balanced",
        }
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    defaults.update(data)
            except Exception:
                pass
        return defaults

    def save_settings(self) -> None:
        """Save settings to JSON file."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"[Settings Warning: Could not save voice_settings.json - {e}]")

    def get_voice(self) -> str:
        return self.settings.get("active_voice", "en-US-AriaNeural")

    def set_voice(self, voice_id: str) -> None:
        self.settings["active_voice"] = voice_id
        self.save_settings()

    def get_mic_index(self) -> int | None:
        return self.settings.get("active_mic_index")

    def set_mic_index(self, index: int | None) -> None:
        self.settings["active_mic_index"] = index
        self.save_settings()

    def test_microphone_hardware_confidence(self, device_index: int | None) -> tuple[bool, str]:
        """Test whether a microphone can open and provide a short audio sample."""
        try:
            devices = sd.query_devices()
            if device_index is not None:
                if device_index < 0 or device_index >= len(devices):
                    return False, f"Device index #{device_index} out of range."
                info = devices[device_index]
                if info.get("max_input_channels", 0) <= 0:
                    return False, f"Device #{device_index} ({info.get('name')}) has no input channels."
            
            # Hardware test stream read
            kwargs = {"samplerate": 16000, "channels": 1, "dtype": "float32"}
            if device_index is not None:
                kwargs["device"] = device_index

            with sd.InputStream(**kwargs) as stream:
                stream.read(1600)  # Read 100ms sample

            dev_name = f"#{device_index}: {devices[device_index]['name']}" if device_index is not None else "System Default Microphone"
            return True, dev_name
        except Exception as e:
            return False, str(e)
