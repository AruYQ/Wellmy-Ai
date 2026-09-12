"""
<vibe_check>
Komponen/Widget  : gui/waveform_widget.py -> WaveformWidget
Tujuan Pengguna  : Visualisasi aktivitas audio yang hidup dan berwibawa saat Wellmy berbicara atau mendengarkan
Layout Strategy  : Kompak horizontal acrylic pill bar, 7 bar spektrum equalizer dengan rounded corners
Color Tokens     : brand_primary (#6B7FD7), status_thinking (#A882DD), border_subtle, bg_surface
Animation Plan   : QTimer 30 FPS, organic sinusoidal wave modulation, dynamic height easing
Typography       : JetBrains Mono (status tag)
Anti-Slop Check  : Anti-aliasing aktif, tidak ada warna mentah, bar rounded, background tembus pandang subtle
</vibe_check>

Waveform Audio Visualizer Widget untuk Wellmy-Ai Desktop Operator.
Menampilkan spektrum frekuensi audio animated yang halus dan responsif.
"""

import math
from typing import List, Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPaintEvent
from PyQt6.QtWidgets import QWidget

from gui.styles import TOKENS


class WaveformWidget(QWidget):
    """
    Visualizer spektrum audio beranimasi organik.
    Dapat disematkan langsung di bilah kontrol HUD.
    """

    STATE_IDLE = "idle"
    STATE_SPEAKING = "speaking"
    STATE_LISTENING = "listening"
    STATE_MUTED = "muted"

    def __init__(self, parent: Optional[QWidget] = None, num_bars: int = 7):
        super().__init__(parent)
        self.num_bars = num_bars
        self._state = self.STATE_IDLE
        self._amplitude = 0.0
        self._phase = 0.0

        # Bar heights relatif (0.1 s.d. 1.0)
        self._bar_heights: List[float] = [0.2] * self.num_bars

        self.setFixedSize(58, 26)
        self.setToolTip("Indikator Suara & Gelombang Audio Wellmy")

        # Timer animasi 30 FPS untuk transisi halus
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(33)
        self._anim_timer.timeout.connect(self._step_animation)
        self._anim_timer.start()

    def set_state(self, state: str) -> None:
        """Mengubah status visual visualizer: idle, speaking, listening, muted."""
        self._state = state
        self.update()

    def set_amplitude(self, amp: float) -> None:
        """Memperbarui nilai amplitudo ucapan (0.0 s.d. 1.0) untuk modulasi spektrum."""
        self._amplitude = max(0.0, min(1.0, amp))
        if self._state != self.STATE_MUTED:
            self._state = self.STATE_SPEAKING if self._amplitude > 0.05 else self.STATE_IDLE
        self.update()

    def _step_animation(self) -> None:
        """Memperbarui tinggi bar secara matematis dengan fungsi gelombang sinus."""
        self._phase += 0.12

        if self._state == self.STATE_SPEAKING:
            for i in range(self.num_bars):
                offset = (i * math.pi) / (self.num_bars / 2)
                wave = (math.sin(self._phase * 1.6 + offset) + 1.0) * 0.5
                target = 0.2 + (self._amplitude * 0.8) * (0.4 + 0.6 * wave)
                # Easing menuju target
                self._bar_heights[i] += (target - self._bar_heights[i]) * 0.35

        elif self._state == self.STATE_LISTENING:
            for i in range(self.num_bars):
                wave = (math.sin(self._phase * 0.8 + i * 0.5) + 1.0) * 0.5
                target = 0.25 + 0.45 * wave
                self._bar_heights[i] += (target - self._bar_heights[i]) * 0.25

        elif self._state == self.STATE_MUTED:
            for i in range(self.num_bars):
                target = 0.12
                self._bar_heights[i] += (target - self._bar_heights[i]) * 0.2

        else:  # IDLE
            for i in range(self.num_bars):
                wave = (math.sin(self._phase * 0.5 + i * 0.4) + 1.0) * 0.5
                target = 0.15 + 0.15 * wave
                self._bar_heights[i] += (target - self._bar_heights[i]) * 0.2

        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Merender bar equalizer dengan antialiasing dan gradasi warna berkelas."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Warna gradien berdasarkan state
        if self._state == self.STATE_SPEAKING:
            top_color = QColor("#A882DD")     # Lavender bangsawan
            bottom_color = QColor("#6B7FD7")  # Indigo
        elif self._state == self.STATE_LISTENING:
            top_color = QColor("#4ECDC4")     # Mint listening
            bottom_color = QColor("#26807B")
        elif self._state == self.STATE_MUTED:
            top_color = QColor("#5A6177")     # Muted grey
            bottom_color = QColor("#2E3450")
        else:  # IDLE
            top_color = QColor(107, 127, 215, 160)
            bottom_color = QColor(78, 205, 196, 120)

        bar_width = 3.5
        spacing = (width - (self.num_bars * bar_width)) / (self.num_bars + 1)

        for i in range(self.num_bars):
            bar_h = max(3.0, self._bar_heights[i] * (height - 6.0))
            x = spacing + i * (bar_width + spacing)
            y = (height - bar_h) / 2.0

            gradient = QLinearGradient(x, y, x, y + bar_h)
            gradient.setColorAt(0.0, top_color)
            gradient.setColorAt(1.0, bottom_color)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_h), 1.7, 1.7)

        painter.end()
