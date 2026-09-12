"""
<vibe_check>
Komponen/Widget  : gui/panic_badge.py (Panic & Safety Status Indicator Badge)
Tujuan Pengguna  : Menampilkan status keamanan sistem secara instan dan elegan (Safe vs Emergency Active)
Layout Strategy  : Compact pill badge dengan pulsating glow saat darurat dan status dot real-time
Color Tokens     : status_safe (#4ECDC4), status_panic (#FF5252), bg_overlay (#252A3D), text_primary (#F0F2F8)
Animation Plan   : Smooth color transitions dan thread-safe event bridge ke Qt GUI loop
Typography       : Space Grotesk / monospace status tag
Anti-Slop Check  : Bebas dari tombol default Windows, layout rapi, thread-safe signal bridge
</vibe_check>

Panic Badge Widget untuk Wellmy-Ai Desktop Operator.
Memantau status global emergency stop (Ctrl+Shift+Q) secara real-time dan thread-safe.
"""

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolTip,
    QWidget,
)

from agent.safety import is_aborted, register_emergency_callback, reset_emergency_stop
from gui.styles import TOKENS


class SafetySignalBridge(QObject):
    """Bridge thread-safe antara background listener pynput dan Qt GUI thread."""
    emergency_signal = pyqtSignal(str)
    reset_signal = pyqtSignal()


class PanicBadge(QFrame):
    """
    Status indicator badge:
    - Hijau (#4ECDC4): System Armed & Safe
    - Merah (#FF5252): Emergency Active (Failsafe Terpicu)
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("PanicBadge")

        self._bridge = SafetySignalBridge()
        self._bridge.emergency_signal.connect(self._on_emergency_gui)
        self._bridge.reset_signal.connect(self._on_reset_gui)

        self._init_ui()
        self._setup_safety_callback()
        self.refresh_status()

    def _init_ui(self) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Status Keamanan Operator.\nTekan Ctrl+Shift+Q kapan saja untuk Emergency Stop.\nKlik untuk reset status darurat.")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        # Status Dot
        self.status_dot = QLabel("●", self)
        self.status_dot.setObjectName("StatusDot")
        self.status_dot.setFixedWidth(14)
        self.status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Status Label Text
        self.status_text = QLabel("ARMED", self)
        self.status_text.setObjectName("StatusText")
        self.status_text.setStyleSheet("font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")

        layout.addWidget(self.status_dot)
        layout.addWidget(self.status_text)

    def _setup_safety_callback(self) -> None:
        def on_emergency(reason: str) -> None:
            self._bridge.emergency_signal.emit(reason)

        register_emergency_callback(on_emergency)

    def _on_emergency_gui(self, reason: str) -> None:
        self.set_panic_state(True, reason)

    def _on_reset_gui(self) -> None:
        self.set_panic_state(False)

    def set_panic_state(self, is_panic: bool, reason: str = "") -> None:
        if is_panic:
            self.setStyleSheet(f"""
                #PanicBadge {{
                    background-color: {TOKENS["status_panic_bg"]};
                    border: 1px solid {TOKENS["border_panic"]};
                    border-radius: 12px;
                }}
            """)
            self.status_dot.setStyleSheet(f"color: {TOKENS['status_panic']}; font-size: 14px;")
            self.status_text.setText("EMERGENCY ACTIVE")
            self.status_text.setStyleSheet(f"color: {TOKENS['status_panic']}; font-size: 11px; font-weight: 700;")
            tip_reason = f" ({reason})" if reason else ""
            self.setToolTip(f"🚨 EMERGENCY STOP AKTIF{tip_reason}!\nOperator mouse/keyboard diblokir.\nKlik badge ini untuk reset.")
        else:
            self.setStyleSheet(f"""
                #PanicBadge {{
                    background-color: {TOKENS["bg_overlay"]};
                    border: 1px solid {TOKENS["border_subtle"]};
                    border-radius: 12px;
                }}
                #PanicBadge:hover {{
                    border-color: {TOKENS["status_safe"]};
                }}
            """)
            self.status_dot.setStyleSheet(f"color: {TOKENS['status_safe']}; font-size: 14px;")
            self.status_text.setText("ARMED")
            self.status_text.setStyleSheet(f"color: {TOKENS['text_secondary']}; font-size: 11px; font-weight: 700;")
            self.setToolTip("Status: ARMED & SAFE.\nTekan Ctrl+Shift+Q kapan saja untuk Emergency Stop.")

    def refresh_status(self) -> None:
        self.set_panic_state(is_aborted())

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if is_aborted():
                reset_emergency_stop()
                self._bridge.reset_signal.emit()
            event.accept()
        else:
            super().mousePressEvent(event)
