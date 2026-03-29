import numpy as np
import soundfile as sf
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QApplication
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

from waveform_widget import WaveformWidget
from player import AudioPlayer
from icons import get_icon

class CropDialog(QDialog):
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._data: np.ndarray | None = None
        self._sr: int | None = None
        self._start: float = 0.0
        self._end: float = 0.0
        self._preview = AudioPlayer()
        self._was_playing = False

        self.setWindowTitle("Trim Audio")
        self.setMinimumSize(740, 320)
        self.setModal(True)
        self._build_ui()
        self._load_audio()

        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ── UI ───────────────────────────────────────────────────

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Trim Audio")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #e2e8f0;")
        lay.addWidget(title)

        hint = QLabel("Drag the purple handle (start) or pink handle (end) to trim. "
                      "Click waveform to seek preview.")
        hint.setStyleSheet("color: #94a3b8; font-size: 12px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        self.waveform = WaveformWidget()
        self.waveform.region_changed.connect(self._on_region)
        self.waveform.seek_requested.connect(lambda t: self._preview.seek(t))
        lay.addWidget(self.waveform)

        time_row = QHBoxLayout()
        self.lbl_start = QLabel("Start: 0.00 s")
        self.lbl_start.setStyleSheet("color: #a78bfa; font-weight: bold;")
        self.lbl_dur = QLabel("Duration: 0.00 s")
        self.lbl_dur.setStyleSheet("color: #94a3b8;")
        self.lbl_end = QLabel("End: 0.00 s")
        self.lbl_end.setStyleSheet("color: #f472b6; font-weight: bold;")
        time_row.addWidget(self.lbl_start)
        time_row.addStretch()
        time_row.addWidget(self.lbl_dur)
        time_row.addStretch()
        time_row.addWidget(self.lbl_end)
        lay.addLayout(time_row)

        btn_row = QHBoxLayout()
        self.btn_preview = QPushButton(" Preview Selection")
        self.btn_preview.setIcon(get_icon("play", "#ffffff", 16))
        self.btn_preview.setFixedHeight(36)
        self.btn_preview.clicked.connect(self._toggle_preview)
        btn_row.addWidget(self.btn_preview)
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(36)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton(" Use This Clip")
        btn_ok.setIcon(get_icon("check", "#ffffff", 16))
        btn_ok.setFixedHeight(36)
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self._on_ok)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

    # ── Loading ──────────────────────────────────────────────

    def _load_audio(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            data, sr = sf.read(self.file_path, dtype="float32", always_2d=True)
        except Exception:
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(self.file_path).set_frame_rate(44100).set_channels(2)
                data = np.array(audio.get_array_of_samples(), dtype=np.float32).reshape((-1, 2)) / 32768.0
                sr = 44100
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "Error", f"Cannot load audio:\n{e}")
                self.reject()
                return
        finally:
            QApplication.restoreOverrideCursor()

        self._data, self._sr = data, sr
        self._start, self._end = 0.0, len(data) / sr
        self.waveform.set_audio(data, sr)
        self._update_labels()

    # ── Slots ────────────────────────────────────────────────

    def _on_region(self, s: float, e: float):
        self._start, self._end = s, e
        self._update_labels()

    def _update_labels(self):
        self.lbl_start.setText(f"Start: {self._start:.2f} s")
        self.lbl_end.setText(f"End: {self._end:.2f} s")
        self.lbl_dur.setText(f"Duration: {self._end - self._start:.2f} s")

    def _tick(self):
        playing_now = self._preview.is_playing
        if playing_now:
            self.waveform.set_cursor(self._preview.get_position())
        if self._was_playing and not playing_now:
            self.btn_preview.setText(" Preview Selection")
            self.btn_preview.setIcon(get_icon("play", "#ffffff", 16))
        self._was_playing = playing_now

    def _toggle_preview(self):
        if self._preview.is_playing:
            self._preview.pause()
            self.btn_preview.setText(" Preview Selection")
            self.btn_preview.setIcon(get_icon("play", "#ffffff", 16))
        else:
            if self._data is None:
                return
            sf_idx = int(self._start * self._sr)
            ef_idx = int(self._end * self._sr)
            self._preview.load_array(self._data[sf_idx:ef_idx], self._sr)
            self._preview.play()
            self.btn_preview.setText(" Pause")
            self.btn_preview.setIcon(get_icon("pause", "#ffffff", 16))

    def _on_ok(self):
        self._preview.stop()
        self.accept()

    def get_cropped_data(self):
        sf_idx = int(self._start * self._sr)
        ef_idx = int(self._end * self._sr)
        return self._data[sf_idx:ef_idx], self._sr

    def closeEvent(self, e):
        self._timer.stop()
        self._preview.stop()
        super().closeEvent(e)
