import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen


class WaveformWidget(QWidget):
    region_changed = pyqtSignal(float, float)
    seek_requested = pyqtSignal(float)

    HIT_ZONE = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(110)
        self.setMouseTracking(True)
        self._peaks: np.ndarray | None = None
        self._duration: float = 0.0
        self._start: float = 0.0
        self._end: float = 0.0
        self._cursor: float = 0.0
        self._drag: str | None = None

    # ── Public API ───────────────────────────────────────────

    def set_audio(self, data: np.ndarray, sr: int):
        mono = data.mean(axis=1) if data.ndim > 1 else data
        n = max(700, self.width() or 700)
        bs = max(1, len(mono) // n)
        peaks = np.array([np.max(np.abs(mono[i: i + bs])) for i in range(0, len(mono) - bs, bs)], dtype=np.float32)
        if peaks.max() > 0:
            peaks /= peaks.max()
        self._peaks = peaks
        self._duration = len(data) / sr
        self._start = 0.0
        self._end = self._duration
        self._cursor = 0.0
        self.update()
        self.region_changed.emit(self._start, self._end)

    def set_cursor(self, seconds: float):
        self._cursor = seconds
        self.update()

    @property
    def start_time(self) -> float:
        return self._start

    @property
    def end_time(self) -> float:
        return self._end

    # ── Helpers ──────────────────────────────────────────────

    def _tx(self, t: float) -> int:
        return int(t / self._duration * self.width()) if self._duration else 0

    def _xt(self, x: float) -> float:
        return max(0.0, min(x / self.width() * self._duration, self._duration))

    # ── Paint ────────────────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        mid = h // 2
        p.fillRect(0, 0, w, h, QColor("#0e0b1e"))

        if self._peaks is None:
            p.setPen(QColor("#444"))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Loading waveform…")
            return

        sx, ex = self._tx(self._start), self._tx(self._end)
        n = len(self._peaks)

        for i, pk in enumerate(self._peaks):
            x = int(i / n * w)
            amp = int(pk * mid * 0.88)
            color = QColor("#7c3aed") if sx <= x <= ex else QColor("#2d1a52")
            p.setPen(color)
            p.drawLine(x, mid - amp, x, mid + amp)

        # Selection overlay
        p.setOpacity(0.12)
        p.fillRect(sx, 0, ex - sx, h, QColor("#8b5cf6"))
        p.setOpacity(1.0)

        # Start handle (purple)
        p.setPen(QPen(QColor("#a78bfa"), 2))
        p.drawLine(sx, 0, sx, h)
        p.fillRect(sx - 5, 0, 10, 16, QColor("#a78bfa"))

        # End handle (pink)
        p.setPen(QPen(QColor("#f472b6"), 2))
        p.drawLine(ex, 0, ex, h)
        p.fillRect(ex - 5, 0, 10, 16, QColor("#f472b6"))

        # Playback cursor (amber)
        if self._cursor > 0:
            cx = self._tx(self._cursor)
            p.setPen(QPen(QColor("#fbbf24"), 1))
            p.drawLine(cx, 0, cx, h)

    # ── Mouse ────────────────────────────────────────────────

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        x = e.position().x()
        if abs(x - self._tx(self._start)) < self.HIT_ZONE:
            self._drag = "start"
        elif abs(x - self._tx(self._end)) < self.HIT_ZONE:
            self._drag = "end"
        else:
            self.seek_requested.emit(self._xt(x))

    def mouseMoveEvent(self, e):
        x = e.position().x()
        near = abs(x - self._tx(self._start)) < self.HIT_ZONE or abs(x - self._tx(self._end)) < self.HIT_ZONE
        self.setCursor(Qt.CursorShape.SizeHorCursor if near else Qt.CursorShape.CrossCursor)
        if self._drag == "start":
            self._start = min(self._xt(x), self._end - 0.05)
            self.update()
            self.region_changed.emit(self._start, self._end)
        elif self._drag == "end":
            self._end = max(self._xt(x), self._start + 0.05)
            self.update()
            self.region_changed.emit(self._start, self._end)

    def mouseReleaseEvent(self, _):
        self._drag = None
