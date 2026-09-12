"""
<vibe_check>
Komponen/Widget  : gui/main_hud.py (Main Floating Spotlight HUD)
Tujuan Pengguna  : Antarmuka utama Wellmy-Ai melayang di layar, elegan, responsif, dan mudah diakses
Layout Strategy  : Spotlight bar frameless dengan background transparan, drag-to-move, drawer ekspansi
Color Tokens     : bg_translucent (#0F1117 @ 92%), border_subtle, brand_primary (#6B7FD7), mint (#4ECDC4)
Animation Plan   : Smooth fade-in saat HUD muncul (QPropertyAnimation opacity), expandable drawer
Typography       : Space Grotesk, Segoe UI, JetBrains Mono
Anti-Slop Check  : Frameless Window, no titlebar jadul Windows, rounded acrylic corners, keyboard shortcuts
</vibe_check>

Main HUD (Heads-Up Display) untuk Wellmy-Ai Desktop Operator.
Menerapkan Spotlight-style bar dengan status badge, input perintah, drawer autoclicker, dan draggable container.
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont, QIcon, QMouseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from agent.brain import WellmyBrain
from agent.voice.audio_player import AudioPlayer
from agent.voice.tts_engine import TTSEngine
from gui.agent_worker import AgentWorker, TTSWorker
from gui.autoclicker_view import AutoclickerView
from gui.panic_badge import PanicBadge
from gui.styles import GLOBAL_STYLESHEET, TOKENS
from gui.waveform_widget import WaveformWidget


class MainHUD(QWidget):
    """
    Spotlight HUD melayang (frameless, translucent, stays on top).
    Menjadi titik interaksi sentral antara pengguna dan Wellmy-Ai.
    """

    command_submitted = pyqtSignal(str)
    voice_toggle_requested = pyqtSignal()

    def __init__(self, brain: Optional[WellmyBrain] = None):
        super().__init__()
        self._drag_pos: Optional[QPoint] = None
        self._autoclicker_expanded = False
        self.brain = brain or WellmyBrain()
        self._active_worker: Optional[AgentWorker] = None
        self._active_tts_worker: Optional[TTSWorker] = None

        # Voice & Sound Engine
        self.tts_engine = TTSEngine()
        self.audio_player = AudioPlayer(self)
        self.voice_output_enabled = False

        self._init_window_flags()
        self._init_ui()
        self._init_voice_system()
        self._init_animations()

    def _init_voice_system(self) -> None:
        """Menghubungkan sinyal audio player ke visualizer waveform."""
        self.audio_player.playback_started.connect(
            lambda: self.waveform.set_state(WaveformWidget.STATE_SPEAKING)
        )
        self.audio_player.playback_finished.connect(
            lambda: self.waveform.set_state(
                WaveformWidget.STATE_IDLE if self.voice_output_enabled else WaveformWidget.STATE_MUTED
            )
        )
        self.audio_player.amplitude_changed.connect(self.waveform.set_amplitude)

    def _init_window_flags(self) -> None:
        # Gunakan FramelessWindowHint dan WindowStaysOnTopHint tanpa Tool flag
        # agar aplikasi tetap muncul di Windows Taskbar dan Alt+Tab
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(GLOBAL_STYLESHEET)
        
        # Set icon resmi pada window agar taskbar menampilkan logo Wellmy
        from gui.system_tray import create_default_tray_icon
        self.setWindowIcon(create_default_tray_icon(is_panic=False))
        self.setWindowTitle("Wellmy-Ai Desktop Operator")
        self.resize(680, 72)

    def _init_ui(self) -> None:
        # Layout terluar dengan margin untuk drop shadow effect
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)
        outer_layout.setSpacing(0)

        # Kontainer Utama Ber-Border & Acrylic Translucent
        self.container = QFrame(self)
        self.container.setObjectName("MainHUDContainer")

        # Soft ambient shadow
        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(14, 10, 14, 10)
        self.container_layout.setSpacing(10)

        # -------------------------------------------------------------
        # 1. TOP BAR (Command Line, Status, Actions)
        # -------------------------------------------------------------
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(10)

        # Persona Emblem / Logo
        self.avatar_badge = QLabel("👑", self.container)
        self.avatar_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {TOKENS["bg_overlay"]};
                border: 1px solid {TOKENS["border_active"]};
                border-radius: 18px;
                padding: 4px 8px;
                font-size: 16px;
            }}
        """)
        self.avatar_badge.setToolTip("Wellmy Ernest — Noblewoman AI Desktop Operator")
        top_bar.addWidget(self.avatar_badge)

        # Command Input Field
        self.command_input = QLineEdit(self.container)
        self.command_input.setObjectName("CommandInput")
        self.command_input.setPlaceholderText("Beri perintah atau tanyakan sesuatu pada Wellmy...")
        self.command_input.returnPressed.connect(self._on_command_return)
        top_bar.addWidget(self.command_input, 1)

        # Mic Action Button (Voice Output Toggle)
        self.mic_btn = QPushButton("🎙️", self.container)
        self.mic_btn.setProperty("class", "IconButton")
        self.mic_btn.setToolTip("Mode Suara: NONAKTIF (Klik untuk mengaktifkan)")
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.clicked.connect(self._on_mic_clicked)
        top_bar.addWidget(self.mic_btn)

        # Waveform Audio Visualizer
        self.waveform = WaveformWidget(self.container)
        self.waveform.set_state(WaveformWidget.STATE_MUTED)
        top_bar.addWidget(self.waveform)

        # Autoclicker Drawer Toggle Button
        self.clicker_toggle_btn = QPushButton("⚡", self.container)
        self.clicker_toggle_btn.setProperty("class", "IconButton")
        self.clicker_toggle_btn.setToolTip("Buka / Tutup Panel Autoclicker")
        self.clicker_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicker_toggle_btn.clicked.connect(self.toggle_autoclicker_drawer)
        top_bar.addWidget(self.clicker_toggle_btn)

        # Panic Status Badge
        self.panic_badge = PanicBadge(self.container)
        top_bar.addWidget(self.panic_badge)

        # Minimize / Hide Button
        self.hide_btn = QPushButton("✕", self.container)
        self.hide_btn.setProperty("class", "IconButton")
        self.hide_btn.setStyleSheet(f"color: {TOKENS['text_muted']}; font-size: 13px; font-weight: bold;")
        self.hide_btn.setToolTip("Sembunyikan ke System Tray (Tekan ESC)")
        self.hide_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hide_btn.clicked.connect(self.hide)
        top_bar.addWidget(self.hide_btn)

        self.container_layout.addLayout(top_bar)

        # -------------------------------------------------------------
        # 2. DRAWER: Response / Status Output Area
        # -------------------------------------------------------------
        self.response_card = QFrame(self.container)
        self.response_card.setObjectName("ResponseCard")
        self.response_card.setStyleSheet(f"""
            #ResponseCard {{
                background-color: {TOKENS["bg_surface"]};
                border: 1px solid {TOKENS["border_subtle"]};
                border-radius: 12px;
                padding: 10px 14px;
            }}
        """)
        response_layout = QVBoxLayout(self.response_card)
        response_layout.setContentsMargins(8, 8, 8, 8)
        self.response_label = QLabel("Wellmy siap mendampingi Anda. Tekan ⚡ untuk autoclicker atau ketik perintah.", self.response_card)
        self.response_label.setStyleSheet(f"color: {TOKENS['text_secondary']}; font-size: 12px; line-height: 1.4;")
        self.response_label.setWordWrap(True)
        response_layout.addWidget(self.response_label)
        self.response_card.hide()  # Disembunyikan secara default
        self.container_layout.addWidget(self.response_card)

        # -------------------------------------------------------------
        # 3. DRAWER: Autoclicker View
        # -------------------------------------------------------------
        self.autoclicker_view = AutoclickerView(self.container)
        self.autoclicker_view.hide()
        self.container_layout.addWidget(self.autoclicker_view)

        outer_layout.addWidget(self.container)

    def _init_animations(self) -> None:
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(240)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_animated(self) -> None:
        """Menampilkan HUD dengan animasi fade-in halus."""
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()
        self.command_input.setFocus()

        self._fade_anim.stop()
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

    def toggle_autoclicker_drawer(self) -> None:
        """Membuka atau menutup drawer Autoclicker."""
        if self._autoclicker_expanded:
            self.autoclicker_view.hide()
            self._autoclicker_expanded = False
            self.clicker_toggle_btn.setStyleSheet("")
            self.adjustSize()
        else:
            self.autoclicker_view.show()
            self._autoclicker_expanded = True
            self.clicker_toggle_btn.setStyleSheet(f"background-color: {TOKENS['bg_overlay']}; border-color: {TOKENS['brand_secondary']};")
            self.adjustSize()

    def set_response_text(self, text: str) -> None:
        """Memperbarui teks respon/status pada drawer pesan."""
        self.response_label.setText(text)
        self.response_card.show()
        self.adjustSize()

    def _on_command_return(self) -> None:
        text = self.command_input.text().strip()
        if not text:
            return

        self.command_input.clear()
        self.command_submitted.emit(text)

        # Jika worker sebelumnya masih berjalan, cegah overlapping
        if self._active_worker and self._active_worker.isRunning():
            self.set_response_text(f"Tuanku, titah sebelumnya masih diproses. Mohon tunggu sejenak.")
            return

        # Tampilkan status awal
        self.set_response_text(f"👑 Wellmy sedang merenungkan titah Anda...")

        # Luncurkan background AgentWorker
        self._active_worker = AgentWorker(self.brain, text)
        self._active_worker.status_signal.connect(self._on_worker_status)
        self._active_worker.response_signal.connect(self._on_worker_response)
        self._active_worker.error_signal.connect(self._on_worker_error)
        self._active_worker.start()

    def _on_worker_status(self, status: str) -> None:
        self.set_response_text(f"💭 {status}")

    def _on_worker_response(self, response: str) -> None:
        self.set_response_text(response)
        if self.voice_output_enabled:
            self.speak(response)

    def _on_worker_error(self, err_msg: str) -> None:
        self.set_response_text(f"⚠️ {err_msg}")

    def speak(self, text: str) -> None:
        """Mensintesis dan memutar suara Wellmy secara non-blocking di background thread."""
        if not text.strip():
            return

        # Batalkan task TTS sebelumnya jika masih berlangsung
        if self._active_tts_worker and self._active_tts_worker.isRunning():
            self._active_tts_worker.terminate()
            self._active_tts_worker.wait(100)

        self._active_tts_worker = TTSWorker(self.tts_engine, text)
        self._active_tts_worker.audio_ready.connect(
            lambda audio_path: self.audio_player.play_file(Path(audio_path))
        )
        self._active_tts_worker.start()

    def _on_mic_clicked(self) -> None:
        """Toggle mode suara aktif / nonaktif."""
        self.voice_output_enabled = not self.voice_output_enabled
        self.voice_toggle_requested.emit()

        if self.voice_output_enabled:
            self.mic_btn.setStyleSheet(f"color: #A882DD; font-size: 14px; font-weight: bold; background: {TOKENS['bg_overlay']};")
            self.mic_btn.setToolTip("Mode Suara: AKTIF (Klik untuk menonaktifkan)")
            self.waveform.set_state(WaveformWidget.STATE_IDLE)
            self.set_response_text("🎙️ Mode suara anggun Wellmy (WaveNet) diaktifkan.")
            self.speak("Mode suara telah aktif, Tuanku. Wellmy siap mendampingi Anda.")
        else:
            self.mic_btn.setStyleSheet("")
            self.mic_btn.setToolTip("Mode Suara: NONAKTIF (Klik untuk mengaktifkan)")
            self.audio_player.stop_immediately()
            self.waveform.set_state(WaveformWidget.STATE_MUTED)
            self.set_response_text("🔇 Mode suara Wellmy dinonaktifkan.")

    # -------------------------------------------------------------
    # Mouse Dragging Support (Bisa digeser ke mana saja di layar)
    # -------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None
        event.accept()

    def keyPressEvent(self, event) -> None:
        # Tekan ESC untuk menyembunyikan HUD ke tray
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)
