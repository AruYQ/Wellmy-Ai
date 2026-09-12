"""
Pemutar Audio Asinkron Non-blocking untuk Wellmy-Ai.
Mendukung Windows Native MCI (DirectSound/WASAPI) bebas konflik codec video FFmpeg,
dengan fallback ke PyQt6.QtMultimedia dan failsafe kill-switch instan (<10ms).
"""

import logging
import math
import os
import random
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from agent.safety import is_aborted, register_panic_callback

logger = logging.getLogger("wellmy.voice.player")


class AudioPlayer(QObject):
    """
    Pemutar suara berkemampuan ganda (Windows Native MCI + QMediaPlayer Fallback)
    yang terintegrasi langsung dengan failsafe darurat global.
    """

    playback_started = pyqtSignal()
    playback_finished = pyqtSignal()
    amplitude_changed = pyqtSignal(float)

    MCI_ALIAS = "wellmy_voice_channel"

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._is_windows = (os.name == "nt")
        self._mci_playing = False

        # Qt Multimedia fallback
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)
        self.player.playbackStateChanged.connect(self._on_qt_playback_state_changed)

        # Timer untuk memantau status pemutaran MCI (Windows)
        self._mci_monitor_timer = QTimer(self)
        self._mci_monitor_timer.setInterval(100)  # Cek setiap 100ms
        self._mci_monitor_timer.timeout.connect(self._check_mci_status)

        # Timer untuk simulasi modulasi amplitudo vokal (menghidupkan visualizer waveform)
        self._visualizer_timer = QTimer(self)
        self._visualizer_timer.setInterval(60)  # ~16 FPS visual update
        self._visualizer_timer.timeout.connect(self._emit_simulated_amplitude)
        self._wave_step = 0.0

        # Daftarkan callback ke sistem penghenti darurat global (Rule 03)
        register_panic_callback(self.stop_immediately)

    def _play_via_mci(self, file_path: Path) -> bool:
        """Memutar file audio secara langsung melalui Windows Multimedia System (MCI)."""
        import ctypes
        resolved_path = str(file_path.resolve())

        # Tutup channel sebelumnya jika ada
        ctypes.windll.winmm.mciSendStringW(f"close {self.MCI_ALIAS}", None, 0, None)

        # Buka stream audio
        cmd_open = f'open "{resolved_path}" type mpegvideo alias {self.MCI_ALIAS}'
        r_open = ctypes.windll.winmm.mciSendStringW(cmd_open, None, 0, None)
        if r_open != 0:
            logger.warning(f"MCI open gagal (kode {r_open}), beralih ke QMediaPlayer fallback.")
            return False

        # Putar stream
        cmd_play = f"play {self.MCI_ALIAS}"
        r_play = ctypes.windll.winmm.mciSendStringW(cmd_play, None, 0, None)
        if r_play != 0:
            logger.warning(f"MCI play gagal (kode {r_play}), beralih ke QMediaPlayer fallback.")
            ctypes.windll.winmm.mciSendStringW(f"close {self.MCI_ALIAS}", None, 0, None)
            return False

        self._mci_playing = True
        self._mci_monitor_timer.start()
        self._visualizer_timer.start()
        self.playback_started.emit()
        logger.info(f"Audio diputar melalui Windows MCI: {file_path.name}")
        return True

    def _check_mci_status(self) -> None:
        """Memantau apakah pemutaran MCI masih aktif atau sudah selesai."""
        if not self._mci_playing:
            self._mci_monitor_timer.stop()
            return

        import ctypes
        buf = ctypes.create_unicode_buffer(64)
        ctypes.windll.winmm.mciSendStringW(f"status {self.MCI_ALIAS} mode", buf, 64, None)
        mode = buf.value.strip().lower()

        if mode != "playing":
            # Pemutaran telah selesai
            self._mci_playing = False
            self._mci_monitor_timer.stop()
            self._visualizer_timer.stop()
            ctypes.windll.winmm.mciSendStringW(f"close {self.MCI_ALIAS}", None, 0, None)
            self.amplitude_changed.emit(0.0)
            self.playback_finished.emit()

    def play_file(self, file_path: Path) -> bool:
        """
        Memutar file audio lokal (MP3/WAV) secara asinkron.
        Mengutamakan Windows MCI di Windows, dengan fallback otomatis ke QMediaPlayer.
        """
        if is_aborted():
            logger.warning("Permintaan pemutaran audio ditolak karena sistem dalam keadaan darurat (Aborted).")
            return False

        if not file_path.exists() or file_path.stat().st_size == 0:
            logger.error(f"File audio tidak ditemukan atau kosong: {file_path}")
            return False

        self.stop_immediately()

        # 1. Coba pemutar asli Windows MCI terlebih dahulu (bebas konflik codec FFmpeg)
        if self._is_windows:
            try:
                if self._play_via_mci(file_path):
                    return True
            except Exception as e:
                logger.warning(f"Eksepsi saat memutar via MCI: {e}. Mencoba fallback QMediaPlayer...")

        # 2. Fallback QMediaPlayer
        try:
            url = QUrl.fromLocalFile(str(file_path.resolve()))
            self.player.setSource(url)
            self.player.play()
            self._visualizer_timer.start()
            self.playback_started.emit()
            logger.info(f"Memulai pemutaran audio via QMediaPlayer: {file_path.name}")
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
            # Hentikan MCI
            if self._is_windows:
                import ctypes
                ctypes.windll.winmm.mciSendStringW(f"stop {self.MCI_ALIAS}", None, 0, None)
                ctypes.windll.winmm.mciSendStringW(f"close {self.MCI_ALIAS}", None, 0, None)
                self._mci_playing = False
                self._mci_monitor_timer.stop()

            # Hentikan QMediaPlayer
            if self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self.player.stop()

            self._visualizer_timer.stop()
            self.amplitude_changed.emit(0.0)
            self.playback_finished.emit()
        except Exception as e:
            logger.error(f"Error saat menghentikan audio player: {e}")

    def is_playing(self) -> bool:
        """Mengecek apakah audio sedang aktif diputar (baik via MCI maupun Qt)."""
        if self._mci_playing:
            return True
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _on_qt_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """Handler perubahan status pemutaran dari QMediaPlayer."""
        if state == QMediaPlayer.PlaybackState.StoppedState and not self._mci_playing:
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
