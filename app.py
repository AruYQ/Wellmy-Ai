"""
Wellmy-Ai Desktop Operator — Main Application Entrypoint
Menginisialisasi QApplication, Spotlight HUD, System Tray, dan Safety Emergency Listener.
"""

import logging
import signal
import sys

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication

from agent.safety import init_safety_listener, register_emergency_callback
from config import config
from gui.main_hud import MainHUD
from gui.system_tray import SystemTrayManager


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger("WellmyAi.App")
    logger.info("Memulai Wellmy-Ai Desktop Operator...")

    # Izinkan pemrosesan sinyal Ctrl+C di terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setApplicationName("Wellmy-Ai")
    app.setApplicationDisplayName("Wellmy-Ai Desktop Operator")
    # Tetap berjalan di background (System Tray) meskipun jendela utama ditutup
    app.setQuitOnLastWindowClosed(False)

    # 1. Inisialisasi Safety Panic Listener (Ctrl+Shift+Q)
    safety_listener = init_safety_listener(config.emergency_hotkey)
    logger.info(f"Safety Panic Listener aktif ({config.emergency_hotkey})")

    # 2. Inisialisasi Main HUD Window
    hud = MainHUD()

    # Posisikan HUD di tengah layar (horizontal) dan ~12% dari batas atas layar
    screen = app.primaryScreen().geometry()
    hud_x = max(0, (screen.width() - hud.width()) // 2)
    hud_y = max(0, int(screen.height() * 0.12))
    hud.move(hud_x, hud_y)

    # 3. Interaksi System Tray
    def toggle_hud() -> None:
        if hud.isVisible():
            hud.hide()
        else:
            hud.show_animated()

    def open_autoclicker() -> None:
        hud.show_animated()
        if not hud._autoclicker_expanded:
            hud.toggle_autoclicker_drawer()

    def exit_application() -> None:
        logger.info("Menutup Wellmy-Ai secara aman...")
        if safety_listener:
            safety_listener.stop()
        if hud.autoclicker_view.worker and hud.autoclicker_view.worker.isRunning():
            hud.autoclicker_view.worker.stop()
        app.quit()

    tray_manager = SystemTrayManager(
        parent=None,
        on_show_hud=toggle_hud,
        on_open_autoclicker=open_autoclicker,
        on_exit=exit_application,
    )
    tray_manager.show()

    # Daftarkan callback darurat untuk sinkronisasi ikon tray
    register_emergency_callback(lambda reason: tray_manager.set_panic_state(True))

    # Timer periodik agar Python dapat menangani sinyal OS (seperti Ctrl+C di konsol)
    sig_timer = QTimer()
    sig_timer.timeout.connect(lambda: None)
    sig_timer.start(250)

    # Tampilkan HUD saat pertama kali diluncurkan
    hud.show_animated()
    logger.info("Wellmy-Ai Desktop Operator siap beroperasi.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
