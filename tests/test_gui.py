"""
Unit tests untuk modul GUI Wellmy-Ai.
Memvalidasi integrasi gaya, token, bridge failsafe, dan inisialisasi widget.
"""

import os
import unittest

# Gunakan offscreen platform untuk testing tanpa display window fisik
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

# Pastikan instance QApplication aktif untuk pengujian widget
app = QApplication.instance() or QApplication(["test", "-platform", "offscreen"])

from gui.styles import TOKENS, GLOBAL_STYLESHEET
from gui.panic_badge import PanicBadge, SafetySignalBridge
from gui.autoclicker_view import AutoclickerView, AutoclickerWorker
from gui.system_tray import create_default_tray_icon, SystemTrayManager
from gui.main_hud import MainHUD
from agent.safety import reset_emergency_stop, trigger_emergency_stop, is_aborted


class TestGUIComponents(unittest.TestCase):

    def setUp(self):
        reset_emergency_stop()

    def tearDown(self):
        reset_emergency_stop()

    def test_styles_and_tokens(self):
        """Memvalidasi kelengkapan token warna dan QSS global."""
        self.assertIn("bg_base", TOKENS)
        self.assertIn("brand_primary", TOKENS)
        self.assertIn("status_panic", TOKENS)
        self.assertIn("status_safe", TOKENS)
        self.assertIn("#MainHUDContainer", GLOBAL_STYLESHEET)
        self.assertIn("#CommandInput", GLOBAL_STYLESHEET)

    def test_tray_icon_generation(self):
        """Memvalidasi pembuatan procedural tray icon untuk normal dan panic mode."""
        icon_normal = create_default_tray_icon(is_panic=False)
        self.assertFalse(icon_normal.isNull())

        icon_panic = create_default_tray_icon(is_panic=True)
        self.assertFalse(icon_panic.isNull())

    def test_panic_badge_state_transitions(self):
        """Memvalidasi badge keamanan merespon status darurat secara visual."""
        badge = PanicBadge()
        self.assertEqual(badge.status_text.text(), "ARMED")

        # Picu status darurat
        trigger_emergency_stop("Test emergency in GUI")
        badge.refresh_status()
        self.assertEqual(badge.status_text.text(), "EMERGENCY ACTIVE")

        # Reset status darurat
        reset_emergency_stop()
        badge.refresh_status()
        self.assertEqual(badge.status_text.text(), "ARMED")

    def test_autoclicker_view_initialization(self):
        """Memvalidasi kontrol autoclicker view memiliki default yang aman."""
        view = AutoclickerView()
        self.assertEqual(view.cps_slider.value(), 10)
        self.assertEqual(view.dur_spin.value(), 0)
        self.assertEqual(view.status_pill.text(), "IDLE")

        # Test CPS slider update
        view.cps_slider.setValue(25)
        self.assertEqual(view.cps_display.text(), "25 CPS")

    def test_autoclicker_worker_abort_on_start(self):
        """Memvalidasi worker autoclicker tidak memulai eksekusi jika status darurat aktif."""
        trigger_emergency_stop("Pre-existing panic")
        worker = AutoclickerWorker(cps=10, duration_sec=5)

        results = []
        worker.finished_signal.connect(lambda r: results.append(r))
        worker.run()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "aborted")

    def test_main_hud_instantiation(self):
        """Memvalidasi MainHUD terinisialisasi dengan sub-widget lengkap."""
        hud = MainHUD()
        self.assertIsNotNone(hud.command_input)
        self.assertIsNotNone(hud.panic_badge)
        self.assertIsNotNone(hud.autoclicker_view)
        self.assertFalse(hud.autoclicker_view.isVisible())

        # Test drawer toggle (cek status hidden pada child widget)
        self.assertTrue(hud.autoclicker_view.isHidden())
        hud.toggle_autoclicker_drawer()
        self.assertFalse(hud.autoclicker_view.isHidden())
        hud.toggle_autoclicker_drawer()
        self.assertTrue(hud.autoclicker_view.isHidden())


if __name__ == "__main__":
    unittest.main()
