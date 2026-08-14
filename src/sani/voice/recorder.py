"""Audio Recording Subsystem with Live Terminal Volume Meter & Silence Detection."""

import io
import sys
import wave
import numpy as np
import sounddevice as sd


class AudioRecorder:
    """Captures audio from microphone with live ASCII level display & automatic silence detection."""

    def __init__(
        self,
        device_index: int | None = None,
        sample_rate: int = 16000,
        channels: int = 1,
        silence_threshold_rms: float = 0.008,
        silence_duration_seconds: float = 1.0,
        max_wait_for_speech_seconds: float = 5.0,
        max_record_seconds: float = 30.0,
    ) -> None:
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_threshold_rms = silence_threshold_rms
        self.silence_duration_seconds = silence_duration_seconds
        self.max_wait_for_speech_seconds = max_wait_for_speech_seconds
        self.max_record_seconds = max_record_seconds

    @staticmethod
    def get_available_microphones() -> list[dict]:
        """Return list of available input microphone devices."""
        try:
            devices = sd.query_devices()
            input_mics = []
            for idx, dev in enumerate(devices):
                if dev.get("max_input_channels", 0) > 0:
                    input_mics.append({
                        "index": idx,
                        "name": dev.get("name", "Unknown Microphone"),
                        "channels": dev.get("max_input_channels"),
                        "sample_rate": dev.get("default_samplerate"),
                    })
            return input_mics
        except Exception:
            return []

    def get_active_microphone_name(self) -> str:
        """Return name of active input microphone device."""
        if self.device_index is not None:
            try:
                info = sd.query_devices(self.device_index)
                return f"#{self.device_index}: {info.get('name', 'Microphone')}"
            except Exception:
                pass
        try:
            default_input = sd.default.device[0]
            if default_input is not None and default_input >= 0:
                info = sd.query_devices(default_input)
                return f"Default (#{default_input}: {info.get('name', 'System Microphone')})"
        except Exception:
            pass
        return "Default Microphone"

    def set_microphone(self, device_index: int) -> str:
        """Switch active microphone input device."""
        devices = sd.query_devices()
        if device_index < 0 or device_index >= len(devices):
            raise ValueError(f"Microphone index #{device_index} is out of range.")
        if devices[device_index].get("max_input_channels", 0) <= 0:
            raise ValueError(f"Device #{device_index} is not an input microphone.")
        self.device_index = device_index
        return self.get_active_microphone_name()

    def _render_volume_bar(self, rms: float) -> str:
        """Render 10-segment ASCII audio level bar for live terminal visual feedback."""
        max_scale = 0.06
        filled = int(min(rms / max_scale, 1.0) * 10)
        bar = "█" * filled + "░" * (10 - filled)
        return f"[{bar}] RMS: {rms:.3f}"

    def record_until_silence(self, prompt_message: str = "Listening...") -> bytes:
        """Record audio from active microphone with live visual level meter until silence is detected."""
        print(f"\n[Voice Mic: {self.get_active_microphone_name()}] {prompt_message}")
        
        chunk_size = int(self.sample_rate * 0.1)  # 100ms chunks
        audio_chunks = []
        silent_chunks = 0
        max_silent_chunks = int(self.silence_duration_seconds / 0.1)
        max_wait_chunks = int(self.max_wait_for_speech_seconds / 0.1)
        max_total_chunks = int(self.max_record_seconds / 0.1)
        has_speech_started = False

        stream_kwargs = {
            "samplerate": self.sample_rate,
            "channels": self.channels,
            "dtype": "float32",
        }
        if self.device_index is not None:
            stream_kwargs["device"] = self.device_index

        try:
            with sd.InputStream(**stream_kwargs) as stream:
                for _ in range(max_total_chunks):
                    chunk, overflow = stream.read(chunk_size)

                    # Calculate Root Mean Square (RMS) volume
                    rms = float(np.sqrt(np.mean(chunk**2)))

                    # Live terminal audio level meter display
                    level_display = self._render_volume_bar(rms)
                    sys.stdout.write(f"\r  {level_display} | Status: {'Speaking...' if has_speech_started else 'Listening...'}")
                    sys.stdout.flush()

                    if rms > self.silence_threshold_rms:
                        audio_chunks.append(chunk)
                        has_speech_started = True
                        silent_chunks = 0
                    elif has_speech_started:
                        audio_chunks.append(chunk)
                        silent_chunks += 1
                        if silent_chunks >= max_silent_chunks:
                            sys.stdout.write(f"\r  {level_display} | Status: Silence detected. Processing...          \n")
                            sys.stdout.flush()
                            break
                    elif _ >= max_wait_chunks:
                        print("\n[Voice] No speech detected. Continuing to listen.")
                        return b""
        except Exception as e:
            print(f"\n[AudioRecorder Hardware Error: {e}]")
            return b""

        sys.stdout.write("\n")
        if not audio_chunks:
            return b""

        # Combine recorded audio chunks into WAV byte stream
        full_audio = np.concatenate(audio_chunks, axis=0)
        pcm_int16 = (full_audio * 32767).astype(np.int16)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit PCM
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm_int16.tobytes())

        return buffer.getvalue()
