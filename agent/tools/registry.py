"""
Wellmy-Ai Tool Registry & Declarative Operator Capabilities
Mendefinisikan fungsi-fungsi yang dapat dipanggil langsung oleh Google Gemini LLM via Function Calling.
Dilengkapi proteksi failsafe is_aborted() dan sanitasi input/output (Rule 01 dan Rule 03).
"""

import logging
from typing import Any, Dict, List, Optional

from agent.safety import is_aborted
from agent.tools.mouse_keyboard import (
    ActuationError,
    click_at,
    get_cursor_position,
    move_to,
    run_autoclicker,
    type_text,
)

logger = logging.getLogger("WellmyAi.ToolRegistry")


def get_cursor_info() -> Dict[str, Any]:
    """Mendapatkan posisi koordinat kursor mouse (X, Y) saat ini di layar desktop pengguna."""
    if is_aborted():
        return {"status": "aborted", "error": "Emergency stop aktif! Aksi fisik diblokir."}
    pos = get_cursor_position()
    return {"status": "success", "x": pos["x"], "y": pos["y"]}


def move_cursor(x: int, y: int) -> Dict[str, Any]:
    """
    Menggerakkan kursor mouse ke koordinat layar tertentu secara halus.

    Args:
        x: Koordinat horizontal piksel (misal: 500)
        y: Koordinat vertikal piksel (misal: 300)
    """
    if is_aborted():
        return {"status": "aborted", "error": "Emergency stop aktif! Pergerakan mouse dibatalkan."}
    try:
        res = move_to(x, y, duration=0.2)
        return {"status": "success", "current_position": res.get("target")}
    except ActuationError as e:
        return {"status": "aborted", "error": str(e)}
    except Exception as e:
        logger.error(f"Gagal move_cursor: {e}")
        return {"status": "error", "error": str(e)}


def click_mouse(x: int, y: int, button: str = "left", clicks: int = 1) -> Dict[str, Any]:
    """
    Menggerakkan kursor dan melakukan klik mouse pada koordinat tertentu.

    Args:
        x: Koordinat horizontal layar piksel
        y: Koordinat vertikal layar piksel
        button: Tombol mouse ('left', 'right', 'middle'). Default adalah 'left'
        clicks: Jumlah klik (default 1)
    """
    if is_aborted():
        return {"status": "aborted", "error": "Emergency stop aktif! Klik dibatalkan."}
    try:
        res = click_at(x, y, button=button, clicks=clicks)
        return {"status": "success", "clicked_at": res.get("position"), "button": button}
    except ActuationError as e:
        return {"status": "aborted", "error": str(e)}
    except Exception as e:
        logger.error(f"Gagal click_mouse: {e}")
        return {"status": "error", "error": str(e)}


def type_text_content(text: str, press_enter: bool = False) -> Dict[str, Any]:
    """
    Mengetikkan teks secara aman ke aplikasi aktif menggunakan keyboard virtual.
    Otomatis diblokir jika teks mengandung rahasia atau API Key (Rule 01).

    Args:
        text: Teks yang ingin diketikkan
        press_enter: Apakah tombol Enter harus ditekan setelah teks selesai diketik
    """
    if is_aborted():
        return {"status": "aborted", "error": "Emergency stop aktif! Pengetikan dibatalkan."}
    try:
        res = type_text(text, press_enter=press_enter)
        if res.get("status") == "blocked":
            return {"status": "blocked", "error": "Pelanggaran Keamanan: Teks mengandung kunci rahasia/API Key."}
        return {"status": "success", "typed_length": res.get("characters_typed")}
    except ActuationError as e:
        return {"status": "aborted", "error": str(e)}
    except Exception as e:
        logger.error(f"Gagal type_text_content: {e}")
        return {"status": "error", "error": str(e)}


def execute_autoclicker(
    clicks_per_second: float,
    duration_seconds: int,
    target_x: Optional[int] = None,
    target_y: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Menjalankan autoclicker berkecepatan tinggi (1 hingga 100 CPS) selama durasi detik tertentu.
    Akan berhenti otomatis seketika (<10ms) jika tombol panik (Ctrl+Shift+Q) terpicu.

    Args:
        clicks_per_second: Kecepatan klik per detik (rentang 1.0 - 100.0)
        duration_seconds: Lama durasi autoclicker berjalan dalam detik (maksimum 300)
        target_x: Koordinat X target (opsional, jika None klik di posisi saat ini)
        target_y: Koordinat Y target (opsional, jika None klik di posisi saat ini)
    """
    if is_aborted():
        return {"status": "aborted", "error": "Emergency stop aktif! Autoclicker tidak dapat dimulai."}
    
    # Batasi durasi maksimum aman dari pemanggilan LLM
    safe_duration = max(1, min(duration_seconds, 300))
    safe_cps = max(1.0, min(clicks_per_second, 100.0))

    try:
        res = run_autoclicker(
            clicks_per_second=safe_cps,
            duration_seconds=safe_duration,
            target_x=target_x,
            target_y=target_y,
        )
        return res
    except ActuationError as e:
        return {"status": "aborted", "error": str(e)}
    except Exception as e:
        logger.error(f"Gagal execute_autoclicker: {e}")
        return {"status": "error", "error": str(e)}


# Daftar seluruh tool yang tersedia untuk Google Gemini Function Calling
OPERATOR_TOOLS: List[Any] = [
    get_cursor_info,
    move_cursor,
    click_mouse,
    type_text_content,
    execute_autoclicker,
]
