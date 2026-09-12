"""
Pemutar Audio Asinkron Non-blocking untuk Wellmy-Ai.
Menggunakan PyQt6.QtMultimedia (QMediaPlayer & QAudioOutput) dengan failsafe kill-switch instan (<10ms).
"""

import logging
import math
import random
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QUrl, QTimer, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from agent.safety import is_aborted, register_panic_callback

logger = logging.getLogger("wellmy.voice.player")


class AudioPlayer(QObject):
    """
    Pemutar suara berbasis QMediaPlayer yang terintegrasi langsung dengan failsafe.
    Menyediakan sinyal pemutaran dan simulasi modulasi amplitudo untuk waveform HUD.
    """

    playback_started = pyqtSignal()
    playback_finished = pyqtSignal()
    amplitude_changed = pyqtSignal(float)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        # Sambungkan sinyal internal QMediaPlayer
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)

        # Timer untuk simulasi fluktuasi amplitudo ucapan (menghidupkan animasi waveform)
        self._visualizer_timer = QTimer(self)
        self._visualizer_timer.setInterval(60)  # ~16 FPS audio pulse update
        self._visualizer_timer.timeout.connect(self._emit_simulated_amplitude)
        self._wave_step = 0.0

        # Daftarkan callback ke sistem penghenti darurat global (Rule 03)
        register_panic_callback(self.stop_immediately)

    def play_file(self, file_path: Path) -> bool:
        """
        Memutar file audio lokal (MP3/WAV) secara asinkron.
        Mengembalikan True jika pemutaran berhasil diinisiasi.
        """
        if is_aborted():
            logger.warning("Permintaan pemutaran audio ditolak karena sistem dalam keadaan darurat (Aborted).")
            return False

        if not file_path.exists() or file_path.stat().st_size == 0:
            logger.error(f"File audio tidak ditemukan atau kosong: {file_path}")
            return False

        try:
            self.stop_immediately()
            url = QUrl.fromLocalFile(str(file_path.resolve()))
            self.player.setSource(url)
            self.player.play()
            self._visualizer_timer.start()
            self.playback_started.emit()
            logger.info(f"Memulai pemutaran audio: {file_path.name}")
            return True
        except Exception as e:
            logger.error(f"Gagal memutar file audio: {e}")
            self._visualizer_timer.stop()
            self.playback_finished.emit()
            return False

    def stop_immediately(self) -> None:
        """
        Menghentikan pemutaran audio seketika (<1ms) saat panic switch aktif atau interupsi.
        """
        try:
            if self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self.player.stop()
            self._visualizer_timer.stop()
            self.amplitude_changed.emit(0.0)
            self.playback_finished.emit()
        except Exception as e:
            logger.error(f"Error saat menghentikan audio player: {e}")

    def is_playing(self) -> bool:
        """Mengecek apakah audio sedang aktif diputar."""
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """Handler perubahan status pemutaran dari QMediaPlayer."""
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self._visualizer_timer.stop()
            self.amplitude_changed.emit(0.0)
            self.playback_finished.emit()

    def _emit_simulated_amplitude(self) -> None:
        """
        Menghasilkan nilai amplitudo dinamis (0.1 - 1.0) untuk menganimasikan visualizer
        secara organik sesuai ritme vokal ucapan.
        """
        if not self.is_playing():
            self._visualizer_timer.stop()
            self.amplitude_changed.emit(0.0)
            return

        self._wave_step += 0.25
        base = 0.4 + 0.3 * math.sin(self._wave_step)
        jitter = random.uniform(-0.15, 0.2)
        amp = max(0.1, min(1.0, base + jitter))
        self.amplitude_changed.emit(amp)
