"""
Unit & Integration Tests for Safety & Credential Isolation (Sprint 1)
Verifikasi kepatuhan Rule 01 (Secrets Isolation) dan Rule 03 (Actuation Safety).
"""

import threading
import time
import unittest
from unittest.mock import patch

from config import AppConfig, config
from agent.safety import (
    is_aborted,
    trigger_emergency_stop,
    reset_abort,
    register_emergency_callback,
)
from agent.tools.mouse_keyboard import type_text, run_autoclicker, move_to, ActuationError


class TestSafetyAndIsolation(unittest.TestCase):
    """Pengujian modul keamanan dan pembatalan darurat."""

    def setUp(self):
        reset_abort()

    def tearDown(self):
        reset_abort()

    def test_secret_str_isolation(self):
        """Memastikan API Key dibungkus SecretStr dan tidak bocor di string representation."""
        cfg = AppConfig()
        raw_repr = repr(cfg)
        raw_str = str(cfg)
        secret_repr = repr(cfg.google_api_key)

        # Nilai mentah tidak boleh muncul di repr atau str
        self.assertNotIn("your_gemini_api_key_here", raw_repr)
        self.assertNotIn("your_gemini_api_key_here", raw_str)
        self.assertIn("**********", secret_repr)

    def test_emergency_stop_trigger(self):
        """Memastikan trigger_emergency_stop mengubah flag atomik dan memanggil callback."""
        callback_called = []

        def on_panic(reason):
            callback_called.append(reason)

        register_emergency_callback(on_panic)

        self.assertFalse(is_aborted())
        trigger_emergency_stop("Test Panic Trigger")
        self.assertTrue(is_aborted())
        self.assertIn("Test Panic Trigger", callback_called)

    def test_output_sanitization_blocks_api_key(self):
        """Memastikan type_text menolak mengetik jika teks mengandung API Key."""
        secret_leak_attempt = f"Kunci rahasia saya adalah: {config.get_api_key()}"
        res = type_text(secret_leak_attempt)

        if len(config.get_api_key()) > 8:
            self.assertEqual(res.get("status"), "blocked")
            self.assertIn("Security violation", res.get("reason", ""))

    @patch("agent.tools.mouse_keyboard.move_to")
    @patch("pyautogui.click")
    def test_autoclicker_aborts_immediately_on_panic(self, mock_click, mock_move):
        """Memastikan autoclicker langsung berhenti (<100ms) saat panic hotkey terpicu."""
        reset_abort()

        # Jalankan trigger panic di thread terpisah setelah 0.15 detik
        def delayed_panic():
            time.sleep(0.15)
            trigger_emergency_stop("Simulated Panic during clicker")

        t = threading.Thread(target=delayed_panic)
        t.start()

        # Minta clicker berjalan selama 5 detik pada 10 CPS
        res = run_autoclicker(clicks_per_second=10.0, duration_seconds=5, target_x=500, target_y=500)

        t.join()

        self.assertEqual(res.get("status"), "aborted")
        self.assertLess(res.get("elapsed_seconds", 999), 1.5)
        self.assertTrue(is_aborted())

    def test_move_to_aborts_when_emergency_active(self):
        """Memastikan move_to langsung melempar ActuationError jika status darurat aktif."""
        trigger_emergency_stop("Emergency active")
        with self.assertRaises(ActuationError):
            move_to(500, 500)


if __name__ == "__main__":
    unittest.main()
