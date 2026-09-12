"""
<vibe_check>
Komponen/Widget  : gui/autoclicker_view.py (Autoclicker Control Panel)
Tujuan Pengguna  : Mengontrol kecepatan (CPS), durasi, tombol, dan koordinat target autoclicker dengan presisi tinggi
Layout Strategy  : BentoCard container vertikal elegan, display angka besar JetBrains Mono, slider responsif
Color Tokens     : bg_surface (#171B26), brand_primary (#6B7FD7), brand_secondary (#4ECDC4), text_primary (#F0F2F8)
Animation Plan   : Non-blocking QThread execution, smooth slider tracking, live click count feedback
Typography       : Space Grotesk labels, JetBrains Mono untuk angka CPS dan koordinat
Anti-Slop Check  : Tidak ada spinbox default Windows polos, widget menggunakan BentoCard dark acrylic styling
</vibe_check>

Autoclicker Control View untuk Wellmy-Ai Desktop.
Menyediakan antarmuka visual untuk autoclicker 1-100 CPS dengan background thread dan failsafe.
"""

import time
from typing import Optional

import pyautogui
from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from agent.safety import is_aborted
from agent.tools.mouse_keyboard import get_cursor_position, move_to
from gui.styles import TOKENS


class AutoclickerWorker(QThread):
    """Worker thread untuk eksekusi autoclicker tanpa membekukan GUI utama."""

    progress_signal = pyqtSignal(int, float)  # click_count, elapsed_seconds
    finished_signal = pyqtSignal(dict)        # result summary

    def __init__(
        self,
        cps: float,
        duration_sec: int,
        target_x: Optional[int] = None,
        target_y: Optional[int] = None,
        button: str = "left",
    ):
        super().__init__()
        self.cps = max(0.5, min(cps, 100.0))
        self.duration_sec = duration_sec  # 0 = tak terbatas
        self.target_x = target_x
        self.target_y = target_y
        self.button = button
        self._is_running = True

    def stop(self) -> None:
        self._is_running = False

    def run(self) -> None:
        if is_aborted():
            self.finished_signal.emit({
                "status": "aborted",
                "reason": "Emergency stop aktif",
                "clicks": 0,
            })
            return

        # Pindahkan ke koordinat target jika ditentukan
        if self.target_x is not None and self.target_y is not None:
            try:
                move_to(self.target_x, self.target_y, duration=0.1)
            except Exception as e:
                self.finished_signal.emit({"status": "error", "reason": str(e), "clicks": 0})
                return

        interval = 1.0 / self.cps
        start_time = time.perf_counter()
        click_count = 0

        try:
            while self._is_running:
                if is_aborted():
                    self.finished_signal.emit({
                        "status": "aborted",
                        "reason": "Emergency stop terpicu saat eksekusi",
                        "clicks": click_count,
                        "elapsed": round(time.perf_counter() - start_time, 2),
                    })
                    return

                # Cek batas durasi jika bukan infinite (duration_sec > 0)
                elapsed = time.perf_counter() - start_time
                if self.duration_sec > 0 and elapsed >= self.duration_sec:
                    break

                iter_start = time.perf_counter()
                pyautogui.click(button=self.button)
                click_count += 1

                # Emit progress setiap beberapa klik untuk performa GUI
                if click_count % max(1, int(self.cps / 5)) == 0 or click_count == 1:
                    self.progress_signal.emit(click_count, round(elapsed, 1))

                time_spent = time.perf_counter() - iter_start
                sleep_time = interval - time_spent
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except pyautogui.FailSafeException:
            from agent.safety import trigger_emergency_stop
            trigger_emergency_stop("PyAutoGUI FailSafe corner triggered")
            self.finished_signal.emit({
                "status": "failsafe",
                "reason": "FailSafe corner triggered",
                "clicks": click_count,
            })
            return
        except Exception as e:
            self.finished_signal.emit({
                "status": "error",
                "reason": str(e),
                "clicks": click_count,
            })
            return

        total_elapsed = round(time.perf_counter() - start_time, 2)
        self.finished_signal.emit({
            "status": "completed",
            "clicks": click_count,
            "elapsed": total_elapsed,
            "effective_cps": round(click_count / total_elapsed, 1) if total_elapsed > 0 else 0,
        })


class AutoclickerView(QFrame):
    """
    Panel kontrol visual untuk Autoclicker berpresisi tinggi.
    Didesain menggunakan BentoCard styling.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("AutoclickerView")
        self.setProperty("class", "BentoCard")
        self.worker: Optional[AutoclickerWorker] = None
        self._target_locked = False

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(16)

        # Header Title
        header_layout = QHBoxLayout()
        title_label = QLabel("⚡ AUTOCLICKER", self)
        title_label.setStyleSheet("font-size: 13px; font-weight: 700; letter-spacing: 1px; color: #6B7FD7;")
        self.status_pill = QLabel("IDLE", self)
        self.status_pill.setStyleSheet(f"""
            background-color: {TOKENS["bg_overlay"]};
            color: {TOKENS["text_secondary"]};
            border-radius: 8px;
            padding: 3px 8px;
            font-size: 10px;
            font-weight: 700;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_pill)
        main_layout.addLayout(header_layout)

        # Speed (CPS) Section
        cps_container = QFrame(self)
        cps_container.setStyleSheet(f"background-color: {TOKENS['bg_surface']}; border-radius: 10px; padding: 10px;")
        cps_layout = QVBoxLayout(cps_container)
        cps_layout.setContentsMargins(10, 8, 10, 8)
        cps_layout.setSpacing(6)

        cps_head = QHBoxLayout()
        cps_title = QLabel("CLICK SPEED", cps_container)
        cps_title.setStyleSheet("font-size: 11px; font-weight: 600; color: #9BA3BE;")
        self.cps_display = QLabel("10 CPS", cps_container)
        self.cps_display.setStyleSheet("font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 700; color: #4ECDC4;")
        cps_head.addWidget(cps_title)
        cps_head.addStretch()
        cps_head.addWidget(self.cps_display)
        cps_layout.addLayout(cps_head)

        self.cps_slider = QSlider(Qt.Orientation.Horizontal, cps_container)
        self.cps_slider.setRange(1, 100)
        self.cps_slider.setValue(10)
        self.cps_slider.valueChanged.connect(self._on_cps_slider_changed)
        cps_layout.addWidget(self.cps_slider)

        main_layout.addWidget(cps_container)

        # Settings Grid (Duration & Button)
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(12)
        grid_layout.setVerticalSpacing(8)

        # Duration Input
        dur_label = QLabel("Durasi (Detik, 0=∞):", self)
        dur_label.setStyleSheet("font-size: 11px; color: #9BA3BE;")
        self.dur_spin = QSpinBox(self)
        self.dur_spin.setRange(0, 3600)
        self.dur_spin.setValue(0)
        self.dur_spin.setSuffix(" dtk")
        self.dur_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {TOKENS["bg_surface"]};
                color: {TOKENS["text_primary"]};
                border: 1px solid {TOKENS["border_subtle"]};
                border-radius: 8px;
                padding: 6px;
                font-family: 'JetBrains Mono', monospace;
            }}
        """)
        grid_layout.addWidget(dur_label, 0, 0)
        grid_layout.addWidget(self.dur_spin, 1, 0)

        # Mouse Button Selector
        btn_label = QLabel("Tombol Mouse:", self)
        btn_label.setStyleSheet("font-size: 11px; color: #9BA3BE;")
        self.button_combo = QComboBox(self)
        self.button_combo.addItems(["Left (Kiri)", "Right (Kanan)", "Middle (Tengah)"])
        self.button_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {TOKENS["bg_surface"]};
                color: {TOKENS["text_primary"]};
                border: 1px solid {TOKENS["border_subtle"]};
                border-radius: 8px;
                padding: 6px;
                font-size: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {TOKENS["bg_elevated"]};
                color: {TOKENS["text_primary"]};
                selection-background-color: {TOKENS["brand_primary"]};
            }}
        """)
        grid_layout.addWidget(btn_label, 0, 1)
        grid_layout.addWidget(self.button_combo, 1, 1)

        main_layout.addLayout(grid_layout)

        # Target Coordinates Section
        target_container = QFrame(self)
        target_container.setStyleSheet(f"background-color: {TOKENS['bg_surface']}; border-radius: 10px; padding: 8px;")
        target_layout = QHBoxLayout(target_container)
        target_layout.setContentsMargins(8, 6, 8, 6)

        self.coord_label = QLabel("Target: Posisi Kursor Dinamis", target_container)
        self.coord_label.setStyleSheet("font-size: 11px; color: #9BA3BE;")
        self.pick_pos_btn = QPushButton("📍 Kunci Posisi", target_container)
        self.pick_pos_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {TOKENS["bg_overlay"]};
                color: {TOKENS["text_primary"]};
                border: 1px solid {TOKENS["border_subtle"]};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                border-color: {TOKENS["brand_secondary"]};
                color: {TOKENS["brand_secondary"]};
            }}
        """)
        self.pick_pos_btn.clicked.connect(self._toggle_lock_position)

        target_layout.addWidget(self.coord_label)
        target_layout.addStretch()
        target_layout.addWidget(self.pick_pos_btn)
        main_layout.addWidget(target_container)

        self.locked_x: Optional[int] = None
        self.locked_y: Optional[int] = None

        # Live Counter Label
        self.stats_label = QLabel("Siap dijalankan. Tekan Ctrl+Shift+Q untuk batal instan.", self)
        self.stats_label.setStyleSheet("font-size: 11px; color: #5A6177; text-align: center;")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.stats_label)

        # Action Buttons (Start / Stop)
        self.action_btn = QPushButton("MULAI AUTOCLICKER", self)
        self.action_btn.setObjectName("ActionBtn")
        self.action_btn.setProperty("class", "PrimaryButton")
        self.action_btn.setMinimumHeight(42)
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.clicked.connect(self._on_action_clicked)
        main_layout.addWidget(self.action_btn)

    def _on_cps_slider_changed(self, val: int) -> None:
        self.cps_display.setText(f"{val} CPS")

    def _toggle_lock_position(self) -> None:
        if not self._target_locked:
            pos = get_cursor_position()
            self.locked_x = pos["x"]
            self.locked_y = pos["y"]
            self._target_locked = True
            self.coord_label.setText(f"Terkunci di: ({self.locked_x}, {self.locked_y})")
            self.pick_pos_btn.setText("Lepas Kunci")
            self.pick_pos_btn.setStyleSheet(f"background-color: {TOKENS['brand_primary']}; color: #FFF; border-radius: 6px; padding: 4px 10px;")
        else:
            self.locked_x = None
            self.locked_y = None
            self._target_locked = False
            self.coord_label.setText("Target: Posisi Kursor Dinamis")
            self.pick_pos_btn.setText("📍 Kunci Posisi")
            self.pick_pos_btn.setStyleSheet(f"background-color: {TOKENS['bg_overlay']}; color: {TOKENS['text_primary']}; border-radius: 6px; padding: 4px 10px;")

    def _on_action_clicked(self) -> None:
        if self.worker and self.worker.isRunning():
            self._stop_autoclicker()
        else:
            self._start_autoclicker()

    def _start_autoclicker(self) -> None:
        if is_aborted():
            self.stats_label.setText("🚨 Gagal mulai: Status darurat aktif (Ctrl+Shift+Q terpicu)!")
            self.stats_label.setStyleSheet("font-size: 11px; color: #FF5252;")
            return

        cps = float(self.cps_slider.value())
        duration = int(self.dur_spin.value())
        button_map = {0: "left", 1: "right", 2: "middle"}
        btn = button_map.get(self.button_combo.currentIndex(), "left")

        self.worker = AutoclickerWorker(
            cps=cps,
            duration_sec=duration,
            target_x=self.locked_x,
            target_y=self.locked_y,
            button=btn,
        )
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

        self.action_btn.setText("HENTIKAN AUTOCLICKER")
        self.action_btn.setStyleSheet(f"""
            background-color: {TOKENS["status_panic_bg"]};
            color: {TOKENS["status_panic"]};
            border: 1px solid {TOKENS["border_panic"]};
            border-radius: 10px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
        """)
        self.status_pill.setText("RUNNING")
        self.status_pill.setStyleSheet(f"background-color: {TOKENS['glow_primary']}; color: {TOKENS['brand_secondary']}; border-radius: 8px; padding: 3px 8px; font-size: 10px; font-weight: 700;")
        self.stats_label.setText("Autoclicker sedang berjalan...")
        self.stats_label.setStyleSheet("font-size: 11px; color: #4ECDC4;")

    def _stop_autoclicker(self) -> None:
        if self.worker:
            self.worker.stop()
            self.worker.wait(500)
        self._reset_ui_idle()

    def _on_progress(self, clicks: int, elapsed: float) -> None:
        self.stats_label.setText(f"Berjalan: {clicks} klik ({elapsed}s)")

    def _on_finished(self, result: dict) -> None:
        self._reset_ui_idle()
        status = result.get("status")
        if status == "completed":
            self.stats_label.setText(f"✓ Selesai: {result.get('clicks')} klik dalam {result.get('elapsed')}s ({result.get('effective_cps')} CPS)")
            self.stats_label.setStyleSheet("font-size: 11px; color: #4ECDC4;")
        elif status == "aborted":
            self.stats_label.setText(f"🚨 Dihentikan oleh Panic Stop! Total: {result.get('clicks')} klik.")
            self.stats_label.setStyleSheet("font-size: 11px; color: #FF5252;")
        elif status == "failsafe":
            self.stats_label.setText("🚨 PyAutoGUI FailSafe terpicu! Gerakan kursor dihentikan.")
            self.stats_label.setStyleSheet("font-size: 11px; color: #FF5252;")
        else:
            self.stats_label.setText(f"Berhenti: {result.get('reason', 'Unknown')}")
            self.stats_label.setStyleSheet("font-size: 11px; color: #9BA3BE;")

    def _reset_ui_idle(self) -> None:
        self.action_btn.setText("MULAI AUTOCLICKER")
        self.action_btn.setStyleSheet(f"""
            background-color: {TOKENS["brand_primary"]};
            color: {TOKENS["text_primary"]};
            border: 1px solid {TOKENS["brand_primary_hover"]};
            border-radius: 10px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
        """)
        self.status_pill.setText("IDLE")
        self.status_pill.setStyleSheet(f"background-color: {TOKENS['bg_overlay']}; color: {TOKENS['text_secondary']}; border-radius: 8px; padding: 3px 8px; font-size: 10px; font-weight: 700;")
