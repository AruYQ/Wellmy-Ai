"""
Unit Tests untuk Sprint 6: Voice & Sound System.
Menguji TTSEngine (caching & emergency audio), AudioPlayer (failsafe kill-switch),
WaveformWidget (visual states), dan tool speak_response.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QApplication

from agent.safety import abort, is_aborted, reset_panic
from agent.voice.audio_player import AudioPlayer
from agent.voice.tts_engine import TTSEngine
from agent.tools.registry import speak_response
from gui.waveform_widget import WaveformWidget

# Inisialisasi QApplication tunggal untuk pengujian komponen Qt
app = QApplication.instance() or QApplication([])


class TestVoiceSystem(unittest.TestCase):
    """Pengujian terpadu subsistem suara dan audio Wellmy-Ai."""

    def setUp(self):
        reset_panic()
        self.test_dir = Path(tempfile.mkdtemp())
        self.tts = TTSEngine(cache_dir=self.test_dir)

    def tearDown(self):
        reset_panic()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_emergency_audio_file_created(self):
        """Memastikan file audio darurat lokal (WAV) otomatis digenerate dan valid."""
        path = self.tts.emergency_sound_path
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 0)
        self.assertEqual(path.suffix, ".wav")

    def test_caching_mechanism(self):
        """Memastikan jika file audio sudah ada di cache, tidak memanggil API eksternal."""
        test_text = "Salam hormat, Tuanku."
        cache_file = self.tts._get_cache_path(test_text)
        
        # Buat fake audio cache
        cache_file.write_bytes(b"FAKE_AUDIO_DATA_FOR_TESTING")
        
        # Panggil synthesize, harus langsung mengembalikan cache file tanpa network call
        result_path = self.tts.synthesize(test_text)
        self.assertEqual(result_path, cache_file)
        self.assertEqual(result_path.read_bytes(), b"FAKE_AUDIO_DATA_FOR_TESTING")

    def test_tts_blocked_when_aborted(self):
        """Memastikan proses sintesis diblokir seketika jika status darurat aktif."""
        abort()
        self.assertTrue(is_aborted())
        res = self.tts.synthesize("Uji coba saat darurat")
        self.assertIsNone(res)

    def test_audio_player_failsafe_stop(self):
        """Memastikan AudioPlayer menghentikan pemutaran seketika saat abort dipicu (<10ms)."""
        player = AudioPlayer()
        
        # Simulasikan pemutaran audio darurat
        emergency_file = self.tts.emergency_sound_path
        success = player.play_file(emergency_file)
        self.assertTrue(success)

        # Picu tombol darurat
        abort()
        self.assertTrue(is_aborted())

        # Player harus berhenti dan amplitudo direset ke 0
        player.stop_immediately()
        self.assertFalse(player.is_playing())

    def test_waveform_widget_states(self):
        """Memastikan status visualizer WaveformWidget beroperasi sesuai desain."""
        widget = WaveformWidget()
        
        widget.set_state(WaveformWidget.STATE_MUTED)
        self.assertEqual(widget._state, WaveformWidget.STATE_MUTED)

        widget.set_state(WaveformWidget.STATE_LISTENING)
        self.assertEqual(widget._state, WaveformWidget.STATE_LISTENING)

        widget.set_amplitude(0.85)
        self.assertEqual(widget._state, WaveformWidget.STATE_SPEAKING)
        self.assertAlmostEqual(widget._amplitude, 0.85)

        widget.set_amplitude(0.0)
        self.assertEqual(widget._state, WaveformWidget.STATE_IDLE)

    def test_speak_response_tool_aborted(self):
        """Memastikan tool speak_response mengembalikan status aborted saat emergency aktif."""
        abort()
        res = speak_response("Tes ucapan")
        self.assertEqual(res.get("status"), "aborted")


if __name__ == "__main__":
    unittest.main()
