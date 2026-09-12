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


def get_screen_dimensions() -> Dict[str, Any]:
    """Mendapatkan dimensi lebar dan tinggi resolusi layar desktop pengguna dalam satuan piksel."""
    if is_aborted():
        return {"status": "aborted", "error": "Emergency stop aktif!"}
    from agent.tools.screen_vision import get_screen_resolution
    w, h = get_screen_resolution()
    return {"status": "success", "width": w, "height": h}


def inspect_screen_vision(question: str = "Jelaskan apa yang sedang terlihat di layar desktop pengguna saat ini.") -> Dict[str, Any]:
    """
    Melihat dan menganalisis tampilan layar desktop pengguna saat ini secara multimodal (Vision).
    Gunakan tool ini ketika pengguna menanyakan isi layar, mencari posisi tombol/elemen visual, atau memeriksa status jendela.
    Area jendela sensitif (.env, password manager, perbankan) otomatis disensor sebelum dianalisis demi privasi (Rule 01).

    Args:
        question: Pertanyaan atau instruksi spesifik mengenai apa yang ingin dicari atau dianalisis pada tampilan layar.
    """
    if is_aborted():
        return {"status": "aborted", "error": "Emergency stop aktif! Analisis penglihatan layar dibatalkan."}

    from config import config
    if not config.is_api_key_configured():
        return {"status": "error", "error": "Kunci API Gemini belum terpasang di .env."}

    try:
        from agent.tools.screen_vision import capture_desktop, image_to_png_bytes
        from google import genai
        from google.genai import types

        # Tangkap layar dengan sensor otomatis
        image = capture_desktop(redact=True)
        img_bytes = image_to_png_bytes(image)

        client = genai.Client(api_key=config.get_api_key())
        image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/png")

        prompt = f"Anda adalah persepsi visual Wellmy-Ai. Perhatikan tangkapan layar pengguna berikut dan jawab pertanyaan dengan akurat: {question}"
        model = config.gemini_model or "gemini-3.7-flash"

        gen_cfg = types.GenerateContentConfig(tools=[])
        try:
            response = client.models.generate_content(
                model=model,
                contents=[image_part, prompt],
                config=gen_cfg,
            )
        except Exception as e:
            if ("503" in str(e) or "404" in str(e)) and model != "gemini-3.6-flash":
                logger.warning(f"Model vision {model} gagal, fallback ke gemini-3.6-flash...")
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[image_part, prompt],
                    config=gen_cfg,
                )
            else:
                raise e

        obs = response.text.strip() if response and response.text else "Tangkapan layar telah diamati."
        return {"status": "success", "observation": obs}

    except Exception as e:
        logger.error(f"Gagal melakukan inspect_screen_vision: {e}")
        return {"status": "error", "error": str(e)}


def speak_response(text: str) -> Dict[str, Any]:
    """
    Mensintesis dan menyuarakan ucapan dengan karakter vokal bangsawan Wellmy Ernest (Google Cloud WaveNet).
    Gunakan tool ini ketika Anda ingin menyampaikan pengumuman atau berbicara secara vokal kepada pengguna.

    Args:
        text: Kalimat yang ingin diucapkan dengan nada anggun.
    """
    if is_aborted():
        return {"status": "aborted", "error": "Emergency stop aktif! Sintesis suara dibatalkan."}

    try:
        from agent.voice.tts_engine import TTSEngine
        engine = TTSEngine()
        audio_path = engine.synthesize(text)
        if audio_path and audio_path.exists():
            return {"status": "success", "audio_path": str(audio_path), "text": text}
        return {"status": "error", "error": "Gagal menghasilkan file audio sintesis suara."}
    except Exception as e:
        logger.error(f"Gagal speak_response: {e}")
        return {"status": "error", "error": str(e)}


def schedule_task(task_name: str, delay_seconds: int, message_or_action: str) -> Dict[str, Any]:
    """
    Menjadwalkan sebuah tugas, pengingat, atau aksi di masa depan setelah penundaan beberapa detik.

    Args:
        task_name: Nama deskripsi tugas (misal: "Pengingat Istirahat")
        delay_seconds: Berapa detik dari sekarang tugas harus dieksekusi (misal: 60)
        message_or_action: Pesan pengingat atau aksi yang harus dijalankan
    """
    if is_aborted():
        return {"status": "aborted", "error": "Emergency stop aktif! Penjadwalan tugas dibatalkan."}

    try:
        from agent.scheduler import get_scheduler
        scheduler = get_scheduler()

        def _action_callback():
            logger.info(f"PENGINGAT TERJADWAL DIEKSEKUSI: {task_name} -> {message_or_action}")
            try:
                from agent.voice.tts_engine import TTSEngine
                TTSEngine().synthesize(f"Tuanku, pengingat untuk Anda: {message_or_action}")
            except Exception:
                pass

        task_id = scheduler.schedule_delay(
            delay_seconds=delay_seconds,
            callback=_action_callback,
            task_name=task_name,
        )

        return {
            "status": "success",
            "task_id": task_id,
            "task_name": task_name,
            "delay_seconds": delay_seconds,
            "message": f"Tugas '{task_name}' berhasil dijadwalkan dalam {delay_seconds} detik.",
        }
    except Exception as e:
        logger.error(f"Gagal schedule_task: {e}")
        return {"status": "error", "error": str(e)}


def list_active_tasks() -> Dict[str, Any]:
    """
    Melihat daftar tugas terjadwal dan timer yang saat ini sedang aktif menunggu eksekusi.
    """
    if is_aborted():
        return {"status": "aborted", "error": "Emergency stop aktif!"}

    try:
        from agent.scheduler import get_scheduler
        tasks = get_scheduler().get_active_tasks()
        return {"status": "success", "total_tasks": len(tasks), "tasks": tasks}
    except Exception as e:
        logger.error(f"Gagal list_active_tasks: {e}")
        return {"status": "error", "error": str(e)}


def cancel_scheduled_task(task_id: str) -> Dict[str, Any]:
    """
    Membatalkan sebuah tugas terjadwal berdasarkan ID tugas.

    Args:
        task_id: ID unik tugas yang ingin dibatalkan
    """
    if is_aborted():
        return {"status": "aborted", "error": "Emergency stop aktif!"}

    try:
        from agent.scheduler import get_scheduler
        ok = get_scheduler().cancel_task(task_id)
        if ok:
            return {"status": "success", "message": f"Tugas {task_id} berhasil dibatalkan."}
        return {"status": "not_found", "message": f"Tugas dengan ID {task_id} tidak ditemukan atau sudah selesai."}
    except Exception as e:
        logger.error(f"Gagal cancel_scheduled_task: {e}")
        return {"status": "error", "error": str(e)}


# Daftar seluruh tool yang tersedia untuk Google Gemini Function Calling
OPERATOR_TOOLS: List[Any] = [
    get_cursor_info,
    move_cursor,
    click_mouse,
    type_text_content,
    execute_autoclicker,
    get_screen_dimensions,
    inspect_screen_vision,
    speak_response,
    schedule_task,
    list_active_tasks,
    cancel_scheduled_task,
]
