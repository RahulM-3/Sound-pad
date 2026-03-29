import threading
import numpy as np
import sounddevice as sd
import soundfile as sf


class AudioPlayer:
    VIRTUAL_MIC_NAME = "CABLE Input"

    # Larger buffer = smoother at cost of minor latency (~93ms @ 44100)
    BLOCKSIZE = 4096

    def __init__(self):
        self._data: np.ndarray | None = None
        self._sr: int | None = None
        self._pos: int = 0
        self._lock = threading.Lock()
        self.volume: float = 0.8
        self.is_playing: bool = False

        # Thread-safe event flags (read by main thread via timer)
        self._playback_ended_flag: bool = False
        self._error_msg: str | None = None

        self._stream: sd.OutputStream | None = None
        self._output_device = self._find_virtual_mic()

    # ── Device ───────────────────────────────────────────────

    def _find_virtual_mic(self):
        try:
            for i, dev in enumerate(sd.query_devices()):
                if self.VIRTUAL_MIC_NAME.lower() in dev["name"].lower():
                    if dev["max_output_channels"] > 0:
                        return i
        except Exception:
            pass
        return None

    def virtual_mic_found(self) -> bool:
        return self._output_device is not None

    def get_output_devices(self):
        return [(i, d["name"]) for i, d in enumerate(sd.query_devices())
                if d["max_output_channels"] > 0]

    def set_output_device(self, index):
        self._output_device = index

    # ── Loading ──────────────────────────────────────────────

    def load(self, file_path: str) -> float:
        self.stop()
        try:
            data, sr = sf.read(file_path, dtype="float32", always_2d=True)
        except Exception:
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(file_path).set_frame_rate(44100).set_channels(2)
                data = np.array(audio.get_array_of_samples(), dtype=np.float32).reshape((-1, 2)) / 32768.0
                sr = 44100
            except Exception as e:
                raise RuntimeError(f"Cannot load audio: {e}")

        if data.shape[1] == 1:
            data = np.repeat(data, 2, axis=1)

        with self._lock:
            self._data = data
            self._sr = sr
            self._pos = 0
        return len(data) / sr

    def load_array(self, data: np.ndarray, sr: int) -> float:
        self.stop()
        if data.ndim == 1:
            data = np.column_stack([data, data])
        with self._lock:
            self._data = data.astype(np.float32)
            self._sr = sr
            self._pos = 0
        return len(data) / sr

    # ── Callback ─────────────────────────────────────────────

    def _make_callback(self):
        """Returns a PortAudio callback. Called by audio driver on a real-time thread — no allocations, no GIL issues."""
        def callback(outdata: np.ndarray, frames: int, time_info, status):
            with self._lock:
                if self._data is None or self._pos >= len(self._data):
                    outdata[:] = 0
                    self._playback_ended_flag = True
                    raise sd.CallbackStop()

                end = min(self._pos + frames, len(self._data))
                n = end - self._pos
                outdata[:n] = self._data[self._pos:end] * self.volume
                if n < frames:
                    # Pad remaining frames with silence then stop
                    outdata[n:] = 0
                    self._pos = len(self._data)
                    self._playback_ended_flag = True
                    raise sd.CallbackStop()
                self._pos = end
        return callback

    def _on_stream_finished(self):
        self.is_playing = False

    # ── Playback ─────────────────────────────────────────────

    def play(self):
        if self._data is None:
            return
        
        # Stop existing stream without resetting _pos
        self.is_playing = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
            
        self._playback_ended_flag = False

        try:
            self._stream = sd.OutputStream(
                device=self._output_device,
                samplerate=self._sr,
                channels=2,
                dtype="float32",
                blocksize=self.BLOCKSIZE,
                callback=self._make_callback(),
                finished_callback=self._on_stream_finished,
                latency="low",
            )
            self.is_playing = True
            self._stream.start()
        except Exception as e:
            self._error_msg = str(e)
            self.is_playing = False

    def stop(self):
        self.is_playing = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        with self._lock:
            self._pos = 0

    def pause(self):
        self.is_playing = False
        if self._stream is not None:
            try:
                self._stream.stop()
            except Exception:
                pass

    def resume(self):
        if self._data is not None and not self.is_playing:
            if self._stream is not None:
                try:
                    self._stream.start()
                    self.is_playing = True
                    return
                except Exception:
                    pass
            # Stream was closed — restart from current position
            self.play()

    def seek(self, seconds: float):
        was_playing = self.is_playing
        if was_playing:
            self.is_playing = False
            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None

        with self._lock:
            if self._sr and self._data is not None:
                self._pos = max(0, min(int(seconds * self._sr), len(self._data) - 1))

        if was_playing:
            self.play()

    # ── State ────────────────────────────────────────────────

    def get_position(self) -> float:
        with self._lock:
            if self._sr and self._data is not None:
                return self._pos / self._sr
        return 0.0

    def get_duration(self) -> float:
        with self._lock:
            if self._sr and self._data is not None:
                return len(self._data) / self._sr
        return 0.0

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(1.0, vol))

    @property
    def audio_data(self):
        return self._data

    @property
    def sample_rate(self):
        return self._sr
