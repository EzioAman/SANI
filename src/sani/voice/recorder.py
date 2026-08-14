"""Audio Recording Subsystem with Microphone Selection & Silence Detection."""

import io
import wave
import numpy as np
import sounddevice as sd


class AudioRecorder:
    """Captures audio from microphone with device selection & automatic silence detection."""

    def __init__(
        self,
        device_index: int | None = None,
        sample_rate: int = 16000,
        channels: int = 1,
        silence_threshold_rms: float = 0.015,
        silence_duration_seconds: float = 1.5,
        max_record_seconds: float = 15.0,
    ) -> None:
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_threshold_rms = silence_threshold_rms
        self.silence_duration_seconds = silence_duration_seconds
        self.max_record_seconds = max_record_seconds

    @staticmethod
    def get_available_microphones() -> list[dict]:
        """Return list of available input microphone devices."""
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
                return f"Default ({info.get('name', 'System Microphone')})"
        except Exception:
            pass
        return "Default Microphone"

    def set_microphone(self, device_index: int) -> str:
        """Switch active microphone input device."""
        self.device_index = device_index
        return self.get_active_microphone_name()

    def record_until_silence(self, prompt_message: str = "Listening...") -> bytes:
        """Record audio from active microphone until user stops speaking or max time is reached."""
        print(f"\n[Voice] {prompt_message}")
        
        chunk_size = int(self.sample_rate * 0.1)  # 100ms chunks
        audio_chunks = []
        silent_chunks = 0
        max_silent_chunks = int(self.silence_duration_seconds / 0.1)
        max_total_chunks = int(self.max_record_seconds / 0.1)
        has_speech_started = False

        stream_kwargs = {
            "samplerate": self.sample_rate,
            "channels": self.channels,
            "dtype": "float32",
        }
        if self.device_index is not None:
            stream_kwargs["device"] = self.device_index

        with sd.InputStream(**stream_kwargs) as stream:
            for _ in range(max_total_chunks):
                chunk, overflow = stream.read(chunk_size)
                audio_chunks.append(chunk)

                # Calculate Root Mean Square (RMS) volume
                rms = np.sqrt(np.mean(chunk**2))

                if rms > self.silence_threshold_rms:
                    has_speech_started = True
                    silent_chunks = 0
                elif has_speech_started:
                    silent_chunks += 1
                    if silent_chunks >= max_silent_chunks:
                        print("[Voice] Silence detected. Processing speech...")
                        break

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
