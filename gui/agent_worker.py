"""
<vibe_check>
Komponen/Widget  : gui/agent_worker.py (Background Agent Execution Thread)
Tujuan Pengguna  : Memproses perintah pengguna ke Gemini AI secara asinkron tanpa membekukan antarmuka desktop
Layout Strategy  : Non-visual QThread worker dengan sinyal status, respon, dan error
Color Tokens     : status_thinking (#A882DD), status_safe (#4ECDC4), text_primary (#F0F2F8)
Animation Plan   : Real-time signal dispatching ke GUI loop
Typography       : N/A (Thread Logic)
Anti-Slop Check  : Menghindari pemblokiran GUI thread, isolasi thread aman
</vibe_check>

Agent Worker Thread untuk Wellmy-Ai Desktop.
Menjalankan inferensi dan function calling Gemini di background thread.
"""

from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from agent.brain import WellmyBrain


class AgentWorker(QThread):
    """Worker thread untuk memproses perintah pengguna melalui WellmyBrain."""

    status_signal = pyqtSignal(str)     # Pesan status real-time ("Sedang berpikir...", dsb)
    response_signal = pyqtSignal(str)   # Jawaban akhir Wellmy
    error_signal = pyqtSignal(str)      # Pesan error jika terjadi kegagalan
    finished_signal = pyqtSignal()      # Sinyal selesai eksekusi

    def __init__(self, brain: WellmyBrain, user_message: str):
        super().__init__()
        self.brain = brain
        self.user_message = user_message

    def run(self) -> None:
        def on_status_update(status_text: str) -> None:
            self.status_signal.emit(status_text)

        try:
            self.status_signal.emit("Wellmy sedang merenungkan titah Anda...")
            response = self.brain.send_message(
                self.user_message,
                status_callback=on_status_update,
            )
            self.response_signal.emit(response)
        except Exception as e:
            self.error_signal.emit(f"Terjadi kesalahan saat memproses perintah: {str(e)}")
        finally:
            self.finished_signal.emit()
