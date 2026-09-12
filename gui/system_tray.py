"""
<vibe_check>
Komponen/Widget  : gui/system_tray.py (System Tray Icon & Context Menu)
Tujuan Pengguna  : Menjaga Wellmy-Ai tetap aktif di background OS tray tanpa mengganggu layar utama
Layout Strategy  : Tray icon dinamis resolusi tinggi (QPixmap/QPainter monogram) dan menu QSS kustom
Color Tokens     : bg_elevated (#1E2333), brand_primary (#6B7FD7), mint (#4ECDC4), panic (#FF5252)
Animation Plan   : Tray notifications (balloons) dan instant context menu trigger
Typography       : Space Grotesk / Segoe UI
Anti-Slop Check  : Icon dibuat secara dinamis anti-blur, menu terintegrasi dengan failsafe, keluar secara anggun
</vibe_check>

System Tray Manager untuk Wellmy-Ai.
Menyediakan akses cepat dari taskbar Windows, toggle HUD, autoclicker, dan failsafe reset.
"""

from typing import Callable, Optional

from PyQt6.QtCore import QObject, Qt
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from agent.safety import is_aborted, reset_emergency_stop, trigger_emergency_stop
from gui.styles import TOKENS


def create_default_tray_icon(is_panic: bool = False) -> QIcon:
    """
    Membuat QIcon elegan beresolusi tinggi secara prosedural (tanpa ketergantungan file eksternal).
    - Mode Normal: Lingkaran gelap elegan dengan aksen Indigo (#6B7FD7) dan inisial 'W' emas/mint.
    - Mode Panic: Lingkaran merah menyala (#FF5252).
    """
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Lingkaran Dasar
    bg_color = QColor(TOKENS["status_panic"]) if is_panic else QColor(TOKENS["bg_elevated"])
    border_color = QColor(TOKENS["border_panic"]) if is_panic else QColor(TOKENS["brand_primary"])

    painter.setBrush(bg_color)
    pen = QPen(border_color, 4)
    painter.setPen(pen)
    painter.drawEllipse(4, 4, size - 8, size - 8)

    # Inisial Monogram 'W' (Wellmy)
    painter.setPen(QColor(TOKENS["text_primary"]))
    font = QFont("Segoe UI", 26, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "W")

    painter.end()
    return QIcon(pixmap)


class SystemTrayManager(QObject):
    """
    Mengelola System Tray Icon, Context Menu, dan interaksi taskbar.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        on_show_hud: Optional[Callable[[], None]] = None,
        on_open_autoclicker: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.on_show_hud = on_show_hud
        self.on_open_autoclicker = on_open_autoclicker
        self.on_exit = on_exit

        self.tray_icon = QSystemTrayIcon(parent)
        self.normal_icon = create_default_tray_icon(is_panic=False)
        self.panic_icon = create_default_tray_icon(is_panic=True)

        self.tray_icon.setIcon(self.normal_icon)
        self.tray_icon.setToolTip("Wellmy-Ai — Desktop Operator Active")

        self._build_context_menu()
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _build_context_menu(self) -> None:
        self.menu = QMenu()
        self.menu.setObjectName("TrayMenu")

        # Show HUD
        self.action_hud = QAction("👑 Tampilkan Wellmy HUD", self.menu)
        if self.on_show_hud:
            self.action_hud.triggered.connect(self.on_show_hud)
        self.menu.addAction(self.action_hud)

        # Autoclicker
        self.action_autoclicker = QAction("⚡ Buka Autoclicker", self.menu)
        if self.on_open_autoclicker:
            self.action_autoclicker.triggered.connect(self.on_open_autoclicker)
        self.menu.addAction(self.action_autoclicker)

        self.menu.addSeparator()

        # Emergency Trigger
        self.action_emergency = QAction("🚨 Emergency Stop (Ctrl+Shift+Q)", self.menu)
        self.action_emergency.triggered.connect(lambda: trigger_emergency_stop("Tray manual emergency trigger"))
        self.menu.addAction(self.action_emergency)

        # Reset Emergency
        self.action_reset = QAction("🔄 Reset Emergency Status", self.menu)
        self.action_reset.triggered.connect(self._handle_reset)
        self.menu.addAction(self.action_reset)

        self.menu.addSeparator()

        # Exit
        self.action_exit = QAction("✕ Keluar dari Wellmy-Ai", self.menu)
        if self.on_exit:
            self.action_exit.triggered.connect(self.on_exit)
        self.menu.addAction(self.action_exit)

        self.tray_icon.setContextMenu(self.menu)

    def show(self) -> None:
        self.tray_icon.show()

    def set_panic_state(self, is_panic: bool) -> None:
        if is_panic:
            self.tray_icon.setIcon(self.panic_icon)
            self.tray_icon.setToolTip("🚨 Wellmy-Ai: EMERGENCY ACTIVE")
        else:
            self.tray_icon.setIcon(self.normal_icon)
            self.tray_icon.setToolTip("Wellmy-Ai — Desktop Operator Active")

    def show_notification(self, title: str, message: str) -> None:
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def _handle_reset(self) -> None:
        reset_emergency_stop()
        self.set_panic_state(False)
        self.show_notification("Wellmy-Ai", "Status darurat telah di-reset. Sistem kembali aman.")

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        # Klik kiri atau double-click menampilkan / menyembunyikan HUD
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if self.on_show_hud:
                self.on_show_hud()
