"""
Wellmy-Ai Safety Controller & Emergency Kill-Switch Module
Memantau pintasan darurat global (default: Ctrl + Shift + Q) dan memotong seluruh
eksekusi fisik/otomatisasi dalam waktu <10ms sesuai Rule 03.
"""

import logging
import threading
from typing import Callable, List, Optional

logger = logging.getLogger("WellmyAi.Safety")

# Event global untuk sinyal abort kilat
_abort_event = threading.Event()
_emergency_callbacks: List[Callable[[str], None]] = []
_callbacks_lock = threading.Lock()


def is_aborted() -> bool:
    """Pemeriksaan atomik super cepat (<1ms) apakah sistem dalam kondisi darurat."""
    return _abort_event.is_set()


def trigger_emergency_stop(reason: str = "Pintasan panik darurat dipicu!") -> None:
    """
    Mengaktifkan status darurat seketika.
    Menghentikan loop klik, membatalkan task aktif, dan memicu callback audio/GUI.
    """
    if not _abort_event.is_set():
        _abort_event.set()
        logger.warning(f"🚨 EMERGENCY STOP TRIGGERED: {reason}")

        # Jalankan callback terdaftar (GUI status update, sound warning)
        with _callbacks_lock:
            for cb in _emergency_callbacks:
                try:
                    import inspect
                    sig = inspect.signature(cb)
                    if len(sig.parameters) == 0:
                        cb()
                    else:
                        cb(reason)
                except Exception as e:
                    logger.error(f"Gagal mengeksekusi emergency callback: {e}")


def reset_abort() -> None:
    """Mereset status darurat kembali ke normal (idle)."""
    _abort_event.clear()
    logger.info("🛡️ Status darurat dinonaktifkan. Sistem kembali normal.")


def reset_emergency_stop() -> None:
    """Alias untuk reset_abort."""
    reset_abort()


# Alias konsisten untuk kenyamanan ekosistem
abort = trigger_emergency_stop
reset_panic = reset_abort


def register_emergency_callback(callback: Callable[..., None]) -> None:
    """Mendaftarkan fungsi yang akan dipanggil seketika saat tombol panik aktif."""
    with _callbacks_lock:
        if callback not in _emergency_callbacks:
            _emergency_callbacks.append(callback)


register_panic_callback = register_emergency_callback


class PanicHotkeyListener:
    """Listener pintasan keyboard global berbasis pynput."""

    def __init__(self, hotkey_str: str = "<ctrl>+<shift>+q"):
        self.hotkey_str = self._normalize_hotkey(hotkey_str)
        self._listener = None
        self._is_running = False

    @staticmethod
    def _normalize_hotkey(raw: str) -> str:
        """Mengonversi format hotkey teks biasa menjadi format pynput."""
        parts = [p.strip().lower() for p in raw.split("+")]
        normalized = []
        for p in parts:
            if p in ("ctrl", "control"):
                normalized.append("<ctrl>")
            elif p in ("shift",):
                normalized.append("<shift>")
            elif p in ("alt",):
                normalized.append("<alt>")
            else:
                normalized.append(p)
        return "+".join(normalized)

    def start(self) -> bool:
        """Menjalankan listener keyboard global di background thread."""
        try:
            from pynput import keyboard

            hotkeys_map = {
                self.hotkey_str: lambda: trigger_emergency_stop("Global Panic Hotkey Detected")
            }
            self._listener = keyboard.GlobalHotKeys(hotkeys_map)
            self._listener.daemon = True
            self._listener.start()
            self._is_running = True
            logger.info(f"Listener tombol panik aktif pada kombinasi: {self.hotkey_str}")
            return True
        except Exception as e:
            logger.error(f"Gagal menginisialisasi listener pynput keyboard: {e}")
            return False

    def stop(self) -> None:
        """Menghentikan listener pintasan."""
        if self._listener and self._is_running:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._is_running = False
            logger.info("Listener tombol panik dihentikan.")


# Inisialisasi default safety manager
safety_listener: Optional[PanicHotkeyListener] = None


def init_safety_listener(hotkey_str: str = "ctrl+shift+q") -> PanicHotkeyListener:
    """Menginisialisasi dan memulai listener tombol panik."""
    global safety_listener
    if safety_listener is None:
        safety_listener = PanicHotkeyListener(hotkey_str=hotkey_str)
        safety_listener.start()
    return safety_listener
