"""Headless Audio Player Subsystem with Balanced Real-time Interruption (Barge-in)."""

import io
import numpy as np
import sounddevice as sd
import soundfile as sf

try:
    import miniaudio
except ImportError:
    miniaudio = None


class AudioPlayer:
    """Plays audio streams headlessly with balanced real-time microphone interruption detection."""

    def __init__(self, interruption_threshold_rms: float = 0.055, sample_rate: int = 16000) -> None:
        self.interruption_threshold_rms = interruption_threshold_rms
        self.sample_rate = sample_rate
        self._is_playing = False
        self._interrupted = False

    def _decode_audio(self, audio_bytes: bytes) -> tuple[np.ndarray, int, int]:
        """Decode MP3/WAV audio bytes into (pcm_array, sample_rate, channels)."""
        # Strategy 1: soundfile (PySoundFile)
        try:
            audio_data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")
            nchannels = 1 if audio_data.ndim == 1 else audio_data.shape[1]
            return audio_data, sr, nchannels
        except Exception:
            pass

        # Strategy 2: miniaudio fallback
        if miniaudio is not None:
            decoded = miniaudio.decode(audio_bytes)
            pcm_array = np.frombuffer(decoded.samples, dtype=np.int16).astype(np.float32) / 32768.0
            if decoded.nchannels > 1:
                pcm_array = pcm_array.reshape(-1, decoded.nchannels)
            return pcm_array, decoded.sample_rate, decoded.nchannels

        raise ValueError("Unable to decode audio bytes: soundfile and miniaudio failed.")

    def play_bytes(self, audio_bytes: bytes) -> bool:
        """Play audio bytes headlessly while monitoring microphone for user interruption.
        
        Returns:
            True if audio played to full completion.
            False if playback was interrupted by user speech.
        """
        if not audio_bytes or len(audio_bytes) < 10:
            return True

        try:
            pcm_array, playback_sample_rate, nchannels = self._decode_audio(audio_bytes)

            chunk_size = int(playback_sample_rate * 0.05)  # 50ms playback chunks
            mic_chunk_size = int(self.sample_rate * 0.05)  # 50ms mic chunks

            self._is_playing = True
            self._interrupted = False
            consecutive_user_speech_chunks = 0

            total_samples = len(pcm_array)
            position = 0
            # Ignore mic interruption during initial 350ms playback chunk to prevent speaker echo false-positives
            grace_period_samples = int(playback_sample_rate * 0.35)

            with sd.OutputStream(samplerate=playback_sample_rate, channels=nchannels, dtype="float32") as out_stream, \
                 sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32") as mic_stream:

                while position < total_samples and self._is_playing:
                    # 1. Check microphone input for user speech (barge-in interruption) after grace period
                    if position > grace_period_samples:
                        try:
                            mic_chunk, _ = mic_stream.read(mic_chunk_size)
                            rms = np.sqrt(np.mean(mic_chunk**2))

                            if rms > self.interruption_threshold_rms:
                                consecutive_user_speech_chunks += 1
                                if consecutive_user_speech_chunks >= 2:
                                    print("\n[Voice] Interrupted by Aman! Stopping speech immediately...")
                                    self._interrupted = True
                                    self._is_playing = False
                                    sd.stop()
                                    return False  # Interrupted!
                            else:
                                consecutive_user_speech_chunks = 0
                        except Exception:
                            pass

                    # 2. Stream 50ms chunk to speakers headlessly
                    end_pos = min(position + chunk_size, total_samples)
                    playback_chunk = pcm_array[position:end_pos]
                    out_stream.write(playback_chunk)
                    position = end_pos

            return not self._interrupted

        except Exception as e:
            print(f"[Player Error: {e}]")
            return True

    def stop(self) -> None:
        """Halt playback immediately."""
        self._is_playing = False
        self._interrupted = True
        sd.stop()
