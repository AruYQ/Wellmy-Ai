"""
Wellmy-Ai Mouse & Keyboard Actuation Module
Menangani pergerakan kursor, pengetikan teks aman, dan autoclicker presisi tinggi.
Terintegrasi ketat dengan modul safety (Rule 01 dan Rule 03).
"""

import time
import logging
from typing import Optional, Dict, Any

import pyautogui
from agent.safety import is_aborted
from config import config

# Wajib per Rule 03: Menggeser kursor ke sudut kiri-atas layar mematikan proses seketika
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02

logger = logging.getLogger("WellmyAi.Actuation")


class ActuationError(Exception):
    """Exception khusus kegagalan atau pembatalan aksi fisik."""
    pass


def get_cursor_position() -> Dict[str, int]:
    """Mendapatkan koordinat fisik kursor saat ini."""
    pos = pyautogui.position()
    return {"x": int(pos.x), "y": int(pos.y)}


def move_to(x: int, y: int, duration: float = 0.2) -> Dict[str, Any]:
    """Menggerakkan kursor ke koordinat tertentu secara halus."""
    if is_aborted():
        raise ActuationError("Aksi dibatalkan: Status darurat aktif.")

    screen_w, screen_h = pyautogui.size()
    clamped_x = max(0, min(x, screen_w - 1))
    clamped_y = max(0, min(y, screen_h - 1))

    pyautogui.moveTo(clamped_x, clamped_y, duration=duration)
    return {
        "status": "success",
        "action": "move_to",
        "target": {"x": clamped_x, "y": clamped_y},
    }


def click_at(x: int, y: int, button: str = "left", clicks: int = 1) -> Dict[str, Any]:
    """Menggerakkan kursor dan melakukan klik pada koordinat tertentu."""
    if is_aborted():
        raise ActuationError("Aksi dibatalkan: Status darurat aktif.")

    move_to(x, y, duration=0.15)

    if is_aborted():
        raise ActuationError("Aksi dibatalkan: Status darurat aktif sebelum klik.")

    valid_buttons = {"left", "right", "middle"}
    btn = button if button in valid_buttons else "left"

    pyautogui.click(x=x, y=y, button=btn, clicks=clicks)
    return {
        "status": "success",
        "action": "click_at",
        "position": {"x": x, "y": y},
        "button": btn,
        "clicks": clicks,
    }


def run_autoclicker(
    clicks_per_second: float,
    duration_seconds: int,
    target_x: Optional[int] = None,
    target_y: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Menjalankan autoclicker presisi tinggi dengan pengecekan status darurat <10ms.
    """
    if is_aborted():
        raise ActuationError("Tidak dapat memulai autoclicker: Status darurat aktif.")

    # Jika koordinat target diberikan, geser kursor ke sana terlebih dahulu
    if target_x is not None and target_y is not None:
        move_to(target_x, target_y, duration=0.1)

    cps = max(0.5, min(clicks_per_second, 100.0))
    interval = 1.0 / cps
    total_duration = max(1, duration_seconds)

    start_time = time.perf_counter()
    end_time = start_time + total_duration
    click_count = 0

    logger.info(f"Memulai autoclicker: {cps} CPS selama {total_duration} detik...")

    try:
        while time.perf_counter() < end_time:
            # Pengecekan abort super cepat di setiap iterasi (<10ms)
            if is_aborted():
                logger.warning("Autoclicker dihentikan seketika oleh sinyal darurat.")
                return {
                    "status": "aborted",
                    "clicks_executed": click_count,
                    "elapsed_seconds": round(time.perf_counter() - start_time, 2),
                    "reason": "Emergency panic abort",
                }

            iter_start = time.perf_counter()
            pyautogui.click()
            click_count += 1

            # Hitung sisa jeda waktu tidur yang presisi
            time_spent = time.perf_counter() - iter_start
            sleep_time = interval - time_spent
            if sleep_time > 0:
                time.sleep(sleep_time)

    except pyautogui.FailSafeException:
        logger.critical("PyAutoGUI FailSafe terpicu! Kursor diarahkan ke pojok layar.")
        from agent.safety import trigger_emergency_stop
        trigger_emergency_stop("PyAutoGUI FailSafe corner triggered")
        return {
            "status": "failsafe_triggered",
            "clicks_executed": click_count,
            "elapsed_seconds": round(time.perf_counter() - start_time, 2),
            "reason": "FailSafe corner triggered",
        }

    elapsed = round(time.perf_counter() - start_time, 2)
    logger.info(f"Autoclicker selesai: {click_count} klik dalam {elapsed} detik.")

    return {
        "status": "completed",
        "clicks_executed": click_count,
        "elapsed_seconds": elapsed,
        "target_cps": cps,
        "effective_cps": round(click_count / elapsed, 1) if elapsed > 0 else 0,
    }


def type_text(text: str, press_enter: bool = False) -> Dict[str, Any]:
    """
    Mengetikkan teks secara aman dengan sanitasi anti-eksfiltrasi (Rule 01).
    """
    if is_aborted():
        raise ActuationError("Aksi pengetikan dibatalkan: Status darurat aktif.")

    # Output Sanitization: Cek apakah teks mengandung API Key rahasia
    secret_key = config.get_api_key()
    if secret_key and len(secret_key) > 8 and secret_key in text:
        logger.critical("🚨 BLOCKED: Percobaan pengetikan teks yang mengandung API Key!")
        return {
            "status": "blocked",
            "reason": "Security violation: text contains sensitive API Key",
        }

    # Ketik teks karakter demi karakter
    pyautogui.write(text, interval=0.02)

    if press_enter and not is_aborted():
        pyautogui.press("enter")

    return {
        "status": "success",
        "characters_typed": len(text),
        "pressed_enter": press_enter,
    }
