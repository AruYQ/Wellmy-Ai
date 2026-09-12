"""
Unit tests untuk modul kognitif Wellmy-Ai (WellmyBrain & Tool Registry).
Menguji registrasi function calling tools, failsafe abort pada pemanggilan tool, dan penanganan status.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

# Platform offscreen untuk testing headless
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

# Pastikan instance QApplication aktif untuk pengujian QThread
app = QApplication.instance() or QApplication(["test", "-platform", "offscreen"])

from agent.brain import WellmyBrain, load_system_instruction
from agent.safety import is_aborted, reset_emergency_stop, trigger_emergency_stop
from agent.tools.registry import (
    OPERATOR_TOOLS,
    click_mouse,
    execute_autoclicker,
    get_cursor_info,
    move_cursor,
    type_text_content,
)
from gui.agent_worker import AgentWorker


class TestToolRegistry(unittest.TestCase):

    def setUp(self):
        reset_emergency_stop()

    def tearDown(self):
        reset_emergency_stop()

    def test_operator_tools_manifest(self):
        """Memvalidasi seluruh tool deklaratif terdaftar dalam katalog."""
        tool_names = [t.__name__ for t in OPERATOR_TOOLS]
        expected_tools = [
            "get_cursor_info",
            "move_cursor",
            "click_mouse",
            "type_text_content",
            "execute_autoclicker",
        ]
        for name in expected_tools:
            self.assertIn(name, tool_names)

    @patch("agent.tools.registry.get_cursor_position")
    def test_get_cursor_info(self, mock_pos):
        """Memvalidasi pembacaan koordinat kursor."""
        mock_pos.return_value = {"x": 640, "y": 480}
        result = get_cursor_info()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["x"], 640)
        self.assertEqual(result["y"], 480)

    def test_tools_blocked_when_emergency_active(self):
        """Memvalidasi seluruh tool aktuasi menolak berjalan jika status darurat aktif."""
        trigger_emergency_stop("Simulasi Darurat")

        r_info = get_cursor_info()
        self.assertEqual(r_info["status"], "aborted")

        r_move = move_cursor(100, 200)
        self.assertEqual(r_move["status"], "aborted")

        r_click = click_mouse(100, 200)
        self.assertEqual(r_click["status"], "aborted")

        r_type = type_text_content("test")
        self.assertEqual(r_type["status"], "aborted")

        r_clicker = execute_autoclicker(10, 1)
        self.assertEqual(r_clicker["status"], "aborted")


class TestWellmyBrain(unittest.TestCase):

    def setUp(self):
        reset_emergency_stop()

    def tearDown(self):
        reset_emergency_stop()

    def test_load_system_instruction(self):
        """Memvalidasi sistem instruction persona Wellmy berhasil dimuat."""
        instruction = load_system_instruction()
        self.assertIn("Wellmy Ernest", instruction)
        self.assertTrue(len(instruction) > 50)

    @patch("config.AppConfig.is_api_key_configured", return_value=False)
    def test_send_message_without_api_key(self, mock_configured):
        """Memvalidasi respon sopan anggun jika API Key belum diisi."""
        brain = WellmyBrain()
        response = brain.send_message("Halo Wellmy")
        self.assertIn("GOOGLE_API_KEY", response)

    def test_send_message_when_aborted(self):
        """Memvalidasi respon menolak titah jika tombol darurat aktif."""
        trigger_emergency_stop("Uji Stop")
        brain = WellmyBrain()
        response = brain.send_message("Klik layar sekarang")
        self.assertIn("sistem darurat", response.lower())

    def test_agent_worker_execution(self):
        """Memvalidasi AgentWorker thread mengeksekusi pesan dan mengirim sinyal respon."""
        brain = WellmyBrain()
        # Gunakan pesan yang akan direspons tanpa API key
        worker = AgentWorker(brain, "Tes Titah")

        responses = []
        worker.response_signal.connect(lambda r: responses.append(r))
        worker.run()

        self.assertEqual(len(responses), 1)
        self.assertTrue(len(responses[0]) > 0)


if __name__ == "__main__":
    unittest.main()
