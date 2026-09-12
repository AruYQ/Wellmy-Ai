"""
Wellmy-Ai Screen Capture & Vision Perception Engine
Menangkap layar desktop dengan mss, mengoptimalkan resolusi untuk efisiensi token multimodal,
dan menerapkan sensor jendela sensitif otomatis (Rule 01).
"""

import io
import logging
from typing import Any, Dict, Optional, Tuple

import mss
from PIL import Image

from agent.safety import is_aborted
from agent.tools.vision_redactor import redact_image
from config import config

logger = logging.getLogger("WellmyAi.ScreenVision")


def get_screen_resolution() -> Tuple[int, int]:
    """Mendapatkan resolusi fisik monitor utama (Width, Height)."""
    try:
        mss_cls = getattr(mss, "MSS", mss.mss)
        with mss_cls() as sct:
            primary = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            return primary["width"], primary["height"]
    except Exception as e:
        logger.debug(f"Gagal membaca resolusi monitor via mss ({e}), fallback ke Windows API...")
        try:
            import ctypes
            w = ctypes.windll.user32.GetSystemMetrics(0)
            h = ctypes.windll.user32.GetSystemMetrics(1)
            if w > 0 and h > 0:
                return w, h
        except Exception:
            pass
        return 1920, 1080


def capture_desktop(
    redact: bool = True,
    max_dimension: int = 1600,
) -> Image.Image:
    """
    Mengambil tangkapan layar monitor utama dan menerapkan sensor otomatis.

    Args:
        redact: Terapkan sensor area sensitif (Rule 01)
        max_dimension: Batas dimensi maksimum gambar untuk menghemat token multimodal
    """
    if is_aborted():
        logger.warning("Capture layar dibatalkan: Status darurat aktif.")
        return Image.new("RGB", (640, 360), color=(25, 20, 20))

    image: Optional[Image.Image] = None

    # 1. Coba menggunakan mss (tercepat)
    try:
        mss_cls = getattr(mss, "MSS", mss.mss)
        with mss_cls() as sct:
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sct_img = sct.grab(monitor)
            image = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
    except Exception as e:
        logger.debug(f"Tangkapan layar mss gagal ({e}), mencoba fallback ImageGrab...")
        try:
            from PIL import ImageGrab
            image = ImageGrab.grab()
        except Exception as e2:
            logger.warning(f"Sesi desktop grafis tidak dapat diakses langsung ({e2}). Menggunakan kanvas fallback.")
            w, h = get_screen_resolution()
            image = Image.new("RGB", (w, h), color=(23, 27, 38))

    # Terapkan sensor privasi (Rule 01) jika diaktifkan
    if redact and image is not None:
        image = redact_image(image)

    # Skalakan gambar secara proporsional jika melampaui batas maksimum
    if image is not None:
        w, h = image.size
        if max(w, h) > max_dimension:
            scale = max_dimension / max(w, h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            logger.debug(f"Screenshot diskalakan dari {w}x{h} menjadi {new_w}x{new_h}")

    return image if image is not None else Image.new("RGB", (640, 360), color=(0, 0, 0))


def image_to_png_bytes(image: Image.Image) -> bytes:
    """Mengonversi PIL Image menjadi buffer bytes PNG."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
