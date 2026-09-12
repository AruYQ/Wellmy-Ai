"""
Pemutar Audio Asinkron Non-blocking untuk Wellmy-Ai.
Mengutamakan modern WASAPI melalui PyQt6.QtMultimedia (QMediaPlayer + QAudioOutput)
dengan binding otomatis ke perangkat audio default Windows, failsafe kill-switch (<10ms),
serta fallback cerdas ke winsound / MCI.
"""

import logging
import math
import os
import random
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer

from agent.safety import is_aborted, register_panic_callback

logger = logging.getLogger("wellmy.voice.player")


class AudioPlayer(QObject):
    """
    Pemutar suara berbasis WASAPI / QMediaPlayer dengan auto-device routing
    dan integrasi failsafe darurat global (<10ms).
    """

    playback_started = pyqtSignal()
    playback_finished = pyqtSignal()
    amplitude_changed = pyqtSignal(float)

    MCI_ALIAS = "wellmy_voice_channel"

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._is_windows = (os.name == "nt")
        self._mci_playing = False

        # Inisialisasi QMediaPlayer & QAudioOutput (WASAPI)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self._refresh_audio_output()

        self.player.playbackStateChanged.connect(self._on_qt_playback_state_changed)
        self.player.errorOccurred.connect(self._on_qt_error_occurred)

        # Timer untuk memantau status pemutaran MCI fallback (jika aktif)
        self._mci_monitor_timer = QTimer(self)
        self._mci_monitor_timer.setInterval(100)
        self._mci_monitor_timer.timeout.connect(self._check_mci_status)

        # Timer untuk modulasi visualizer waveform HUD
        self._visualizer_timer = QTimer(self)
        self._visualizer_timer.setInterval(60)
        self._visualizer_timer.timeout.connect(self._emit_simulated_amplitude)
        self._wave_step = 0.0

        # Daftarkan callback ke failsafe darurat global (Rule 03)
        register_panic_callback(self.stop_immediately)

    def _refresh_audio_output(self) -> None:
        """Memastikan QAudioOutput terhubung ke perangkat output default dengan volume 100%."""
        try:
            default_device = QMediaDevices.defaultAudioOutput()
            if not default_device.isNull():
                self.audio_output.setDevice(default_device)
                logger.info(f"Audio output terikat ke: {default_device.description()}")
        except Exception as e:
            logger.warning(f"Gagal mendeteksi QMediaDevices: {e}")

        self.audio_output.setMuted(False)
        self.audio_output.setVolume(1.0)

    def play_file(self, file_path: Path) -> bool:
        """
        Memutar file audio lokal (MP3/WAV) secara asinkron non-blocking.
        Menggunakan WASAPI (QMediaPlayer) sebagai audio engine utama.
        """
        if is_aborted():
            logger.warning("Permintaan pemutaran audio ditolak karena sistem dalam keadaan darurat (Aborted).")
            return False

        if not file_path.exists() or file_path.stat().st_size == 0:
            logger.error(f"File audio tidak ditemukan atau kosong: {file_path}")
            return False

        self.stop_immediately()
        self._refresh_audio_output()

        # 1. Jalur Utama: QMediaPlayer (WASAPI hardware stream)
        try:
            resolved_path = str(file_path.resolve())
            url = QUrl.fromLocalFile(resolved_path)
            self.player.setSource(url)
            self.player.play()
            self._visualizer_timer.start()
            self.playback_started.emit()
            logger.info(f"Memulai pemutaran audio via QMediaPlayer (WASAPI): {file_path.name}")
            return True
        except Exception as e:
            logger.warning(f"QMediaPlayer gagal memulai ({e}). Mencoba fallback...")

        # 2. Fallback untuk file WAV di Windows: winsound
        if self._is_windows and file_path.suffix.lower() == ".wav":
            try:
                import winsound
                winsound.PlaySound(str(file_path.resolve()), winsound.SND_FILENAME | winsound.SND_ASYNC)
                self._visualizer_timer.start()
                self.playback_started.emit()
                logger.info(f"Memutar file WAV via Windows winsound: {file_path.name}")
                return True
            except Exception as e:
                logger.warning(f"winsound gagal: {e}")

        # 3. Fallback Windows MCI dengan pemaksaan volume maksimal
        if self._is_windows:
            if self._play_via_mci(file_path):
                return True

        self._visualizer_timer.stop()
        self.playback_finished.emit()
        return False

    def _play_via_mci(self, file_path: Path) -> bool:
        """Fallback sekunder menggunakan Windows Multimedia System (MCI) dengan penyesuaian volume."""
        import ctypes
        resolved_path = str(file_path.resolve())

        ctypes.windll.winmm.mciSendStringW(f"close {self.MCI_ALIAS}", None, 0, None)
        cmd_open = f'open "{resolved_path}" type mpegvideo alias {self.MCI_ALIAS}'
        if ctypes.windll.winmm.mciSendStringW(cmd_open, None, 0, None) != 0:
            return False

        # Set volume MCI ke 1000 (maksimum)
        ctypes.windll.winmm.mciSendStringW(f"setaudio {self.MCI_ALIAS} volume to 1000", None, 0, None)

        if ctypes.windll.winmm.mciSendStringW(f"play {self.MCI_ALIAS}", None, 0, None) != 0:
            ctypes.windll.winmm.mciSendStringW(f"close {self.MCI_ALIAS}", None, 0, None)
            return False

        self._mci_playing = True
        self._mci_monitor_timer.start()
        self._visualizer_timer.start()
        self.playback_started.emit()
        logger.info(f"Audio diputar melalui Windows MCI fallback: {file_path.name}")
        return True

    def _check_mci_status(self) -> None:
        """Memantau status pemutaran MCI fallback."""
        if not self._mci_playing:
            self._mci_monitor_timer.stop()
            return

        import ctypes
        buf = ctypes.create_unicode_buffer(64)
        ctypes.windll.winmm.mciSendStringW(f"status {self.MCI_ALIAS} mode", buf, 64, None)
        mode = buf.value.strip().lower()

        if mode != "playing":
            self._mci_playing = False
            self._mci_monitor_timer.stop()
            self._visualizer_timer.stop()
            ctypes.windll.winmm.mciSendStringW(f"close {self.MCI_ALIAS}", None, 0, None)
            self.amplitude_changed.emit(0.0)
            self.playback_finished.emit()

    def _on_qt_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """Handler perubahan status pemutaran dari QMediaPlayer."""
        if state == QMediaPlayer.PlaybackState.StoppedState and not self._mci_playing:
            self._visualizer_timer.stop()
            self.amplitude_changed.emit(0.0)
            self.playback_finished.emit()

    def _on_qt_error_occurred(self, error: QMediaPlayer.Error, error_string: str) -> None:
        """Handler penanganan error pada QMediaPlayer."""
        logger.error(f"Error pemutaran QMediaPlayer: {error} - {error_string}")
        if not self._mci_playing:
            self._visualizer_timer.stop()
            self.amplitude_changed.emit(0.0)
            self.playback_finished.emit()

    def stop_immediately(self) -> None:
        """Menghentikan pemutaran audio seketika (<1ms) saat panic switch aktif atau interupsi."""
        try:
            if self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self.player.stop()

            if self._is_windows:
                import ctypes
                ctypes.windll.winmm.mciSendStringW(f"stop {self.MCI_ALIAS}", None, 0, None)
                ctypes.windll.winmm.mciSendStringW(f"close {self.MCI_ALIAS}", None, 0, None)
                self._mci_playing = False
                self._mci_monitor_timer.stop()

            self._visualizer_timer.stop()
            self.amplitude_changed.emit(0.0)
            self.playback_finished.emit()
        except Exception as e:
            logger.error(f"Error saat menghentikan audio player: {e}")

    def is_playing(self) -> bool:
        """Mengecek apakah audio sedang aktif diputar."""
        if self._mci_playing:
            return True
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _emit_simulated_amplitude(self) -> None:
        """Menghasilkan nilai amplitudo dinamis (0.1 - 1.0) untuk visualizer spektrum."""
        if not self.is_playing():
            self._visualizer_timer.stop()
            self.amplitude_changed.emit(0.0)
            return

        self._wave_step += 0.25
        base = 0.4 + 0.3 * math.sin(self._wave_step)
        jitter = random.uniform(-0.15, 0.2)
        amp = max(0.1, min(1.0, base + jitter))
        self.amplitude_changed.emit(amp)

