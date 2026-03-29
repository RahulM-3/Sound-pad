import sys
import atexit
from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QFont, QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSlider, QScrollArea, QGridLayout,
    QFileDialog, QInputDialog, QMessageBox, QFrame, QSizePolicy, QMenu, QDialog,
    QListWidget, QListWidgetItem
)

from player import AudioPlayer
from profile_manager import ProfileManager
from crop_dialog import CropDialog
from device_switcher import get_current_device_index, get_cable_device_index, set_device_by_index
from icons import get_icon

COLS = 5

STYLESHEET = """
* { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; }
QMainWindow, QWidget#centralWidget, QScrollArea, QScrollArea > QWidget > QWidget { 
    background-color: #0F111A; 
    color: #E2E8F0; 
}
QLabel { background: transparent; color: #E2E8F0; }

#headerBar {
    background: #151822;
    border-bottom: 1px solid #232736;
}
#toolBar { background-color: #12141D; border-bottom: 1px solid #1C1F2B; }
#playerBar { background-color: #151822; border-top: 1px solid #232736; }

QPushButton {
    background-color: #1E2130; color: #E2E8F0;
    border: 1px solid #32384D; border-radius: 8px;
    padding: 6px 14px; font-size: 13px; font-weight: 500;
}
QPushButton:hover { background-color: #2D3247; border-color: #6366F1; }
QPushButton:pressed { background-color: #4338CA; border-color: #8B5CF6; }

#uploadBtn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
    border: none; color: white; font-weight: 600;
    border-radius: 8px; padding: 7px 18px;
}
#uploadBtn:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8B5CF6, stop:1 #A855F7);
}

#soundCard {
    background-color: #1A1D27; border: 1px solid #232736; border-radius: 12px;
}
#soundCard:hover { background-color: #232736; border-color: #6366F1; }
#soundCard[active="true"] { background-color: #1B173B; border: 2px solid #8B5CF6; }

#cardPlayBtn {
    background: #2D3247; border: 1px solid #32384D;
    border-radius: 20px; color: white; margin: 4px;
}
#cardPlayBtn:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #6366F1, stop:1 #8B5CF6);
    border: none;
}
#soundCard[active="true"] #cardPlayBtn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #8B5CF6, stop:1 #A855F7);
    border: none;
}

#mainPlayBtn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #6366F1, stop:1 #8B5CF6);
    border: none; border-radius: 23px; color: white;
}
#mainPlayBtn:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #8B5CF6, stop:1 #A855F7);
}

QScrollBar:vertical { background: #0F111A; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #32384D; border-radius: 5px; min-height: 40px; margin: 2px; }
QScrollBar::handle:vertical:hover { background: #444B66; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QSlider::groove:horizontal { height: 6px; background: #232736; border-radius: 3px; }
QSlider::handle:horizontal {
    background: #8B5CF6; width: 16px; height: 16px;
    margin: -5px 0; border-radius: 8px; border: 2px solid #151822;
}
QSlider::handle:horizontal:hover { background: #A855F7; }
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
    border-radius: 3px;
}

QComboBox {
    background-color: #1E2130; color: #E2E8F0;
    border: 1px solid #32384D; border-radius: 8px;
    padding: 6px 14px; font-size: 13px; font-weight: 500;
}
QComboBox:hover {
    background-color: #232736; border-color: #6366F1;
}
QComboBox::drop-down { 
    border: none; width: 34px; 
}
QComboBox::down-arrow {
    image: url("{DOWN_ARROW}");
    width: 14px; height: 14px;
}
QComboBox QAbstractItemView {
    background-color: #1A1D27; color: #E2E8F0; 
    border: none;
    outline: none;
}
QComboBox QAbstractItemView::item {
    min-height: 32px; padding-left: 12px;
}
QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover {
    background-color: #6366F1; color: white;
}

QDialog { background-color: #0F111A; color: #E2E8F0; }
QLineEdit {
    background-color: #1E2130; color: #E2E8F0; border: 1px solid #32384D;
    border-radius: 6px; padding: 6px; font-size: 13px;
}
QLineEdit:focus { border: 1px solid #6366F1; background-color: #232736; }
QMenu {
    background-color: #1A1D27; border: 1px solid #32384D; border-radius: 6px;
    color: #E2E8F0; padding: 6px;
}
QMenu::item { padding: 6px 20px; border-radius: 4px; font-size: 13px; }
QMenu::item:selected { background-color: #4338CA; }
QMessageBox, QInputDialog { background-color: #0F111A; }
"""


# ── Styled ComboBox ──────────────────────────────────────────

class StyledComboBox(QComboBox):
    """Custom QComboBox that shows popup below the widget with a clean styled border."""

    def showPopup(self):
        popup = self.findChild(QFrame)
        if popup:
            popup.setWindowFlags(
                popup.windowFlags()
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.NoDropShadowWindowHint
            )

        # Force Qt to place popup below the widget
        view = self.view()
        if view:
            container = view.window()
            container.setWindowFlags(
                Qt.WindowType.Popup 
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.NoDropShadowWindowHint
            )

        super().showPopup()

        # Reposition to always be directly below
        view = self.view()
        if view:
            container = view.window()
            pos = self.mapToGlobal(QPoint(0, self.height()))
            container.move(pos)
            container.setFixedWidth(self.width())


# ── Clickable Slider ─────────────────────────────────────────

class ClickableSlider(QSlider):
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            # First process the normal mouse press to ensure handle logic holds, but we bypass the page step
            val = self.minimum() + ((self.maximum() - self.minimum()) * ev.position().x()) / self.width()
            self.setValue(int(val))
            self.sliderPressed.emit()
            ev.accept()
        else:
            super().mousePressEvent(ev)
            
    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.sliderReleased.emit()
            ev.accept()
        else:
            super().mouseReleaseEvent(ev)

# ── Sound Card ───────────────────────────────────────────────

class SoundCard(QFrame):
    play_clicked = pyqtSignal(str, str)
    delete_clicked = pyqtSignal(str)

    def __init__(self, label: str, file_path: str, parent=None):
        super().__init__(parent)
        self._label = label
        self._file_path = file_path
        self.setObjectName("soundCard")
        self.setFixedSize(130, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._ctx_menu)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(6)
        lay.setContentsMargins(8, 10, 8, 8)

        self.btn = QPushButton()
        self.btn.setIcon(get_icon("play", "#ffffff"))
        self.btn.setIconSize(QSize(18, 18))
        self.btn.setObjectName("cardPlayBtn")
        self.btn.setFixedSize(40, 40)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(lambda: self.play_clicked.emit(self._file_path, self._label))

        lbl = QLabel(self._label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 12px; font-weight: 500; color: #E2E8F0;")
        lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        lay.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(lbl)

    def set_active(self, active: bool):
        icon_name = "pause" if active else "play"
        self.btn.setIcon(get_icon(icon_name, "#ffffff"))
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)

    def _ctx_menu(self, pos):
        menu = QMenu(self)
        act = QAction(get_icon("trash", "#e2e8f0", 16), "Remove from profile", self)
        act.triggered.connect(lambda: self.delete_clicked.emit(self._file_path))
        menu.addAction(act)
        menu.exec(self.mapToGlobal(pos))


# ── Main Window ──────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._pm = ProfileManager()
        self._player = AudioPlayer()
        self._current_profile: str = ""
        self._active_card: SoundCard | None = None
        self._seeking = False
        self._ended = False
        self._last_upload_dir = ""

        # Dynamically find the virtual mic's index
        cable_index = get_cable_device_index()

        # Check the current Windows default mic
        self._prev_device_index = get_current_device_index()
        cache_file = Path("audio/.last_mic.txt")

        # If the current default IS the virtual cable, the app probably crashed last time.
        # Let's restore the REAL mic from our persistent cache.
        if self._prev_device_index == cable_index and cache_file.exists():
            try:
                self._prev_device_index = int(cache_file.read_text().strip())
            except ValueError:
                pass
        else:
            # We are safe; the current mic is a real user mic. Cache it permanently.
            if self._prev_device_index is not None:
                cache_file.parent.mkdir(exist_ok=True)
                cache_file.write_text(str(self._prev_device_index))
        
        # Failsafe: Ensures the real mic is restored even if the app crashes or is force-killed
        if self._prev_device_index is not None:
            atexit.register(set_device_by_index, self._prev_device_index)
        
        if self._player.virtual_mic_found() and cable_index is not None:
            set_device_by_index(cable_index)

        self.setWindowTitle("Soundpad")
        self.setWindowIcon(get_icon("music", "#8B5CF6", 64))
        self.setMinimumSize(860, 640)
        
        # Inject SVG into stylesheet dynamically via a temporary file 
        # (Qt6 fails to parse bare base64 SVGs correctly on Windows)
        import tempfile
        import os
        from icons import _ICONS
        
        tmp_arrow = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
        svg_code = _ICONS["down_arrow"].format(color="#8B5CF6") # Matching purple style
        tmp_arrow.write(svg_code.encode('utf-8'))
        tmp_arrow.close()
        
        # Cleanup temp file naturally on exit
        atexit.register(lambda path=tmp_arrow.name: os.unlink(path) if os.path.exists(path) else None)

        # Qt requires forward slashes for filesystem paths in QSS
        safe_path = tmp_arrow.name.replace('\\', '/')
        self.setStyleSheet(STYLESHEET.replace("{DOWN_ARROW}", safe_path))
        
        root = QWidget()
        root.setObjectName("centralWidget")
        self.setCentralWidget(root)
        
        self._build_ui(root)
        self._refresh_profiles(select_first=True)

        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ── Build UI ─────────────────────────────────────────────

    def _build_ui(self, root):
        lay = QVBoxLayout(root)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._mk_header())
        lay.addWidget(self._mk_toolbar())
        lay.addWidget(self._mk_grid(), stretch=1)
        lay.addWidget(self._mk_player())

    def _mk_header(self):
        bar = QWidget()
        bar.setObjectName("headerBar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 16, 24, 16)

        logo = QLabel()
        logo.setPixmap(get_icon("music", "#8B5CF6", 28).pixmap(28, 28))
        
        title = QLabel("SOUNDPAD")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC; letter-spacing: 1px;")

        self.lbl_device = QLabel()
        self._refresh_device_label()

        lay.addWidget(logo)
        lay.addSpacing(8)
        lay.addWidget(title)
        lay.addStretch()
        lay.addWidget(self.lbl_device)
        return bar

    def _refresh_device_label(self):
        if self._player.virtual_mic_found():
            self.lbl_device.setText("CABLE Output Live")
            self.lbl_device.setStyleSheet("""
                background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3);
                color: #10B981; font-size: 12px; font-weight: 600; padding: 6px 12px; border-radius: 14px;
            """)
        else:
            self.lbl_device.setText("CABLE Output not found")
            self.lbl_device.setStyleSheet("""
                background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3);
                color: #F59E0B; font-size: 12px; font-weight: 600; padding: 6px 12px; border-radius: 14px;
            """)

    def _mk_toolbar(self):
        bar = QWidget()
        bar.setObjectName("toolBar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 12, 24, 12)
        lay.setSpacing(10)

        lay.addWidget(QLabel("Profile:"))
        self.combo = StyledComboBox()
        self.combo.setFixedWidth(200)
        self.combo.currentTextChanged.connect(self._on_profile_changed)
        lay.addWidget(self.combo)

        btn_new = QPushButton("New")
        btn_new.setIcon(get_icon("plus", "#E2E8F0", 16))
        btn_new.clicked.connect(self._create_profile)
        lay.addWidget(btn_new)

        btn_del = QPushButton("Delete")
        btn_del.setIcon(get_icon("trash", "#E2E8F0", 16))
        btn_del.clicked.connect(self._delete_profile)
        lay.addWidget(btn_del)

        lay.addStretch()

        btn_up = QPushButton("Upload Audio")
        btn_up.setIcon(get_icon("upload", "#ffffff", 18))
        btn_up.setObjectName("uploadBtn")
        btn_up.clicked.connect(self._upload_audio)
        lay.addWidget(btn_up)
        return bar

    def _mk_grid(self):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_w = QWidget()
        self.grid = QGridLayout(self.grid_w)
        self.grid.setSpacing(16)
        self.grid.setContentsMargins(24, 24, 24, 24)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll.setWidget(self.grid_w)
        return self.scroll

    def _mk_player(self):
        bar = QWidget()
        bar.setObjectName("playerBar")
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(24, 16, 24, 18)
        lay.setSpacing(10)

        self.lbl_track = QLabel("No audio selected")
        self.lbl_track.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500;")
        lay.addWidget(self.lbl_track)

        seek_row = QHBoxLayout()
        self.seek = ClickableSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 1000)
        self.seek.sliderPressed.connect(lambda: setattr(self, "_seeking", True))
        self.seek.sliderReleased.connect(self._on_seek_released)
        self.lbl_time = QLabel("0:00 / 0:00")
        self.lbl_time.setStyleSheet("color: #94A3B8; font-size: 12px; min-width: 82px; font-weight: 500;")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        seek_row.addWidget(self.seek)
        seek_row.addWidget(self.lbl_time)
        lay.addLayout(seek_row)

        ctrl = QHBoxLayout()
        self.btn_restart = QPushButton()
        self.btn_restart.setIcon(get_icon("restart", "#E2E8F0", 20))
        self.btn_restart.setFixedSize(40, 40)
        self.btn_restart.setToolTip("Restart")
        self.btn_restart.clicked.connect(self._restart)

        self.btn_play = QPushButton()
        self.btn_play.setIcon(get_icon("play", "#ffffff", 24))
        self.btn_play.setIconSize(QSize(24, 24))
        self.btn_play.setObjectName("mainPlayBtn")
        self.btn_play.setFixedSize(46, 46)
        self.btn_play.clicked.connect(self._toggle_play)

        self.btn_stop = QPushButton()
        self.btn_stop.setIcon(get_icon("stop", "#E2E8F0", 20))
        self.btn_stop.setFixedSize(40, 40)
        self.btn_stop.setToolTip("Stop")
        self.btn_stop.clicked.connect(self._stop)

        mic_icon = QLabel()
        mic_icon.setPixmap(get_icon("mic", "#64748B", 20).pixmap(20, 20))

        self.vol = QSlider(Qt.Orientation.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setValue(80)
        self.vol.setFixedWidth(130)
        self.vol.valueChanged.connect(lambda v: self._player.set_volume(v / 100))
        self._player.set_volume(0.8)

        self.lbl_vol = QLabel("80%")
        self.lbl_vol.setStyleSheet("color: #94A3B8; font-size: 12px; min-width: 36px; font-weight: 500;")
        self.vol.valueChanged.connect(lambda v: self.lbl_vol.setText(f"{v}%"))

        ctrl.addWidget(self.btn_restart)
        ctrl.addWidget(self.btn_play)
        ctrl.addWidget(self.btn_stop)
        ctrl.addSpacing(20)
        ctrl.addWidget(mic_icon)
        ctrl.addWidget(self.vol)
        ctrl.addWidget(self.lbl_vol)
        ctrl.addStretch()
        lay.addLayout(ctrl)
        return bar

    # ── Profile Management ───────────────────────────────────

    def _refresh_profiles(self, select_first=False, select_name=None):
        names = self._pm.get_profile_names()
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(names)
        if select_name and select_name in names:
            self.combo.setCurrentText(select_name)
        elif select_first and names:
            self.combo.setCurrentIndex(0)
        self.combo.blockSignals(False)
        self._on_profile_changed(self.combo.currentText())

    def _on_profile_changed(self, name: str):
        self._current_profile = name
        self._load_profile(name)

    def _load_profile(self, name: str):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._active_card = None

        if not name:
            return

        sounds = self._pm.load_profile(name).get("sounds", [])
        if not sounds:
            ph = QLabel("No sounds yet.\nClick Upload Audio to add some.")
            ph.setStyleSheet("color: #64748B; font-size: 15px; font-weight: 500; padding: 40px;")
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(ph, 0, 0)
            return

        for i, s in enumerate(sounds):
            card = SoundCard(s["label"], s["file"])
            card.play_clicked.connect(self._on_card_play)
            card.delete_clicked.connect(self._on_card_delete)
            self.grid.addWidget(card, i // COLS, i % COLS)

    def _create_profile(self):
        name, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if ok and name.strip():
            name = name.strip()
            if name in self._pm.get_profile_names():
                QMessageBox.warning(self, "Exists", f"'{name}' already exists.")
                return
            self._pm.create_profile(name)
            self._refresh_profiles(select_name=name)

    def _delete_profile(self):
        name = self.combo.currentText()
        if not name:
            return
            
        if name.lower() == "default":
            QMessageBox.warning(self, "Cannot Delete", "The 'Default' profile cannot be deleted.")
            return

        r = QMessageBox.question(self, "Delete Profile",
                                 f"Delete profile '{name}' AND all of its audio files?",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            self._pm.delete_profile(name)
            self._refresh_profiles(select_first=True)

    # ── Upload ───────────────────────────────────────────────

    def _upload_audio(self):
        if not self._current_profile:
            QMessageBox.warning(self, "No Profile", "Select or create a profile first.")
            return

        exts = "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a *.aac *.wma *.aiff *.opus *.webm);;All Files (*.*)"
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Audio Files", self._last_upload_dir, exts)
        if not paths:
            return
            
        self._last_upload_dir = str(Path(paths[0]).parent)

        if len(paths) == 1:
            # Single file Flow: show CropDialog and renaming prompt
            path = paths[0]
            dlg = CropDialog(path, self)
            dlg.setStyleSheet(STYLESHEET)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return

            data, sr = dlg.get_cropped_data()
            label, ok = QInputDialog.getText(self, "Sound Label", "Name for this sound:",
                                             text=Path(path).stem)
            if not ok or not label.strip():
                return
                
            try:
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                self._pm.add_sound(self._current_profile, label.strip(), path, data=data, sr=sr)
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))
            finally:
                QApplication.restoreOverrideCursor()
        else:
            # Multi-file Bulk Import Flow: skip cropping and dialogs
            try:
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                failed_files = []
                for p in paths:
                    label = Path(p).stem
                    try:
                        self._pm.add_sound(self._current_profile, label, p)
                    except Exception:
                        failed_files.append(label)
                if failed_files:
                    QMessageBox.warning(self, "Import Errors", f"Failed to import {len(failed_files)} files.")
            finally:
                QApplication.restoreOverrideCursor()

        self._load_profile(self._current_profile)

    # ── Playback ─────────────────────────────────────────────

    def _on_card_play(self, file_path: str, label: str):
        if self._active_card:
            self._active_card.set_active(False)

        for i in range(self.grid.count()):
            w = self.grid.itemAt(i).widget()
            if isinstance(w, SoundCard) and w._file_path == file_path:
                self._active_card = w
                w.set_active(True)
                break

        try:
            self._player.load(file_path)
            self._player.play()
            self.lbl_track.setText(f"{label}")
            self.lbl_track.setStyleSheet("color: #A78BFA; font-size: 14px; font-weight: 600;")
            self.btn_play.setIcon(get_icon("pause", "#ffffff", 24))
            self._ended = False
        except Exception as e:
            QMessageBox.critical(self, "Playback Error", str(e))

    def _on_card_delete(self, file_path: str):
        r = QMessageBox.question(self, "Remove Sound", "Remove this sound from the profile?",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            if self._active_card and self._active_card._file_path == file_path:
                self._player.stop()
                self._active_card = None
            self._pm.remove_sound(self._current_profile, file_path)
            self._load_profile(self._current_profile)

    def _toggle_play(self):
        if self._player.is_playing:
            self._player.pause()
            self.btn_play.setIcon(get_icon("play", "#ffffff", 24))
        else:
            self._player.resume()
            self.btn_play.setIcon(get_icon("pause", "#ffffff", 24))

    def _stop(self):
        self._player.stop()
        self.btn_play.setIcon(get_icon("play", "#ffffff", 24))
        self.seek.setValue(0)
        self.lbl_time.setText("0:00 / 0:00")
        if self._active_card:
            self._active_card.set_active(False)
            self._active_card = None

    def _restart(self):
        self._player.seek(0)
        if not self._player.is_playing:
            self._player.resume()
            self.btn_play.setIcon(get_icon("pause", "#ffffff", 24))

    def _on_seek_released(self):
        dur = self._player.get_duration()
        if dur > 0:
            self._player.seek(self.seek.value() / 1000 * dur)
            # Auto-play on timeline click/seek as requested
            if not self._player.is_playing:
                self._player.resume()
                self.btn_play.setIcon(get_icon("pause", "#ffffff", 24))
        self._seeking = False

    # ── Timer Tick ───────────────────────────────────────────

    def _tick(self):
        # Handle playback end (set from background thread)
        if self._player._playback_ended_flag and not self._ended:
            self._ended = True
            self._player._playback_ended_flag = False
            self.btn_play.setIcon(get_icon("play", "#ffffff", 24))
            if self._active_card:
                self._active_card.set_active(False)
                self._active_card = None

        # Handle errors from background thread
        if self._player._error_msg:
            QMessageBox.warning(self, "Playback Error", self._player._error_msg)
            self._player._error_msg = None

        if self._player.audio_data is None:
            return

        pos = self._player.get_position()
        dur = self._player.get_duration()

        if not self._seeking and dur > 0:
            self.seek.blockSignals(True)
            self.seek.setValue(int(pos / dur * 1000))
            self.seek.blockSignals(False)

        self.lbl_time.setText(f"{self._fmt(pos)} / {self._fmt(dur)}")
        self.btn_play.setIcon(get_icon("pause" if self._player.is_playing else "play", "#ffffff", 24))

    @staticmethod
    def _fmt(sec: float) -> str:
        m, s = int(sec) // 60, int(sec) % 60
        return f"{m}:{s:02d}"

    def closeEvent(self, e):
        self._player.stop()
        # Restore the audio device index that was active before the app opened
        if hasattr(self, "_prev_device_index") and self._prev_device_index is not None:
            set_device_by_index(self._prev_device_index)
        super().closeEvent(e)


# ── Entry Point ──────────────────────────────────────────────

if __name__ == "__main__":
    import os
    
    # Enable high DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    # Fix Windows taskbar icon to show custom app icon instead of default Python logo
    if os.name == 'nt':
        try:
            import ctypes
            myappid = 'rahul.soundpad.desktop.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setWindowIcon(get_icon("music", "#8B5CF6", 64))
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
