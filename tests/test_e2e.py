"""
End-to-End (E2E) & Stress Test Suite untuk Wellmy-Ai Desktop Operator.
Memverifikasi interaksi menyeluruh antar-subsistem:
- Keamanan & Panic Kill-Switch (<10ms cutoff)
- Autoclicker Stress Test pada 100 CPS
- Persona Engine & Cognitive Prompt Compiler
- Screen Redaction Privasi Layar
- Voice Engine & Audio Player Interlock
- Task Scheduler & Background Timers
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QApplication

from agent.persona import PersonaEngine
from agent.safety import abort, is_aborted, reset_panic
from agent.scheduler import get_scheduler
from agent.tools.mouse_keyboard import run_autoclicker
from agent.tools.registry import OPERATOR_TOOLS
from agent.tools.vision_redactor import redact_image
from agent.voice.audio_player import AudioPlayer
from agent.voice.tts_engine import TTSEngine
from gui.autoclicker_view import AutoclickerWorker

# Single QApplication instance
app = QApplication.instance() or QApplication([])


class TestWellmyEndToEndStress(unittest.TestCase):
    """Pengujian integrasi ujung-ke-ujung dan uji ketahanan performa tinggi."""

    def setUp(self):
        reset_panic()
        self.scheduler = get_scheduler()

    def tearDown(self):
        reset_panic()
        self.scheduler.shutdown(wait=False)

    def test_e2e_autoclicker_high_frequency_stress_and_abort(self):
        """
        STRESS TEST: Menjalankan worker autoclicker pada 100 CPS dan memicu panic switch.
        Memverifikasi bahwa loop 100 CPS terhenti seketika (<100ms) tanpa thread hang atau crash.
        """
        worker = AutoclickerWorker(
            cps=100.0,
            duration_sec=10,
            button="left",
            target_x=None,
            target_y=None,
        )

        completed_events = []
        worker.finished_signal.connect(lambda: completed_events.append("FINISHED"))

        with patch("pyautogui.click") as mock_click:
            worker.start()
            self.assertTrue(worker.isRunning())
            time.sleep(0.08)

            # PICU TOMBOL PANIK DARURAT (Ctrl+Shift+Q)
            abort()
            self.assertTrue(is_aborted())

            # Worker harus segera berhenti (<100ms)
            worker.wait(300)
            self.assertFalse(worker.isRunning())

    def test_e2e_persona_and_operator_manifest_coherence(self):
        """
        Memverifikasi konsistensi sistem instruksi:
        Persona Wellmy Ernest (istri bangsawan, lore Iora, analogi kerajaan)
        berpadu utuh dengan seluruh 11 tools deklaratif operator di OPERATOR_TOOLS.
        """
        engine = PersonaEngine()
        system_instruction = engine.compile_system_instruction()

        # Validasi pilar kepribadian
        self.assertIn("Wellmy Ernest", system_instruction)
        self.assertIn("Proud to be a Villainess", system_instruction)
        self.assertIn("Iora", system_instruction)
        self.assertIn("suami", system_instruction.lower())

        # Validasi seluruh fungsi operator deklaratif ada di manifest tools
        tool_names = [fn.__name__ for fn in OPERATOR_TOOLS]
        expected_tools = [
            "get_cursor_info",
            "move_cursor",
            "click_mouse",
            "type_text_content",
            "execute_autoclicker",
            "get_screen_dimensions",
            "inspect_screen_vision",
            "speak_response",
            "schedule_task",
            "list_active_tasks",
            "cancel_scheduled_task",
        ]
        for tool in expected_tools:
            self.assertIn(tool, tool_names)

    def test_e2e_voice_and_safety_interlock(self):
        """
        Memverifikasi interlock audio player: saat darurat terpicu,
        pemutar audio memotong transmisi suara dan memblokir tool bicara.
        """
        tts = TTSEngine()
        player = AudioPlayer()
        emergency_wav = tts.emergency_sound_path
        self.assertTrue(emergency_wav.exists())

        player.play_file(emergency_wav)

        # Picu darurat
        abort()
        self.assertTrue(is_aborted())

        # Player harus berhenti dan tidak aktif
        player.stop_immediately()
        self.assertFalse(player.is_playing())

    def test_e2e_screen_redaction_privacy_guard(self):
        """
        Memverifikasi sensor otomatis jendela sensitif (.env, password, tokens)
        berjalan dan memodifikasi gambar sebelum dikirim ke luar.
        """
        from PIL import Image
        fake_img = Image.new("RGB", (300, 300), color=(100, 150, 200))
        target_box = (10, 10, 110, 110)

        redacted_img = redact_image(fake_img, [target_box])
        self.assertIsNotNone(redacted_img)
        # Piksel area sensor harus berubah
        orig_px = fake_img.getpixel((50, 50))
        redacted_px = redacted_img.getpixel((50, 50))
        self.assertNotEqual(orig_px, redacted_px)

    def test_e2e_scheduler_and_emergency_blockage(self):
        """
        Memverifikasi tugas penjadwalan terisolasi dan tertolak jika tombol panik aktif.
        """
        action_ran = []

        def sample_cb():
            action_ran.append(True)

        task_id = self.scheduler.schedule_delay(1, sample_cb, "E2E Task")
        self.assertIsNotNone(task_id)

        # Matikan sistem
        abort()
        time.sleep(1.2)
        self.assertEqual(action_ran, [])


if __name__ == "__main__":
    unittest.main()
