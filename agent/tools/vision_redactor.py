"""
Wellmy-Ai Vision Redactor Module (Rule 01 - Security & Credentials Isolation)
Secara otomatis mendeteksi jendela/area sensitif pada desktop (seperti berkas .env,
pengelola kata sandi, browser perbankan, token/secret) dan menyensornya dengan Gaussian blur
serta overlay proteksi sebelum gambar tangkapan layar dikirim ke Gemini Cloud API.
"""

import logging
import os
import sys
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import config

logger = logging.getLogger("WellmyAi.VisionRedactor")

# Kata kunci judul jendela yang diklasifikasikan sebagai area sensitif
SENSITIVE_KEYWORDS = [
    ".env",
    "password",
    "keepass",
    "1password",
    "bitwarden",
    "lastpass",
    "credential",
    "secret",
    "token",
    "banking",
    "authenticator",
    "private_key",
    "id_rsa",
]


def get_sensitive_window_boxes() -> List[Tuple[int, int, int, int]]:
    """
    Memindai seluruh jendela aktif di Windows dan mengembalikan koordinat
    bounding box (left, top, right, bottom) untuk jendela yang memuat kata kunci sensitif.
    """
    boxes: List[Tuple[int, int, int, int]] = []

    if os.name != "nt":
        return boxes

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        # Tipe data RECT
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG),
            ]

        # Callback EnumWindows
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def enum_windows_callback(hwnd, lparam):
            # Hanya periksa jendela yang terlihat (visible) dan bukan jendela iconified/minimized
            if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buffer, length + 1)
                    title = buffer.value.lower()

                    # Cek apakah judul mengandung kata kunci sensitif
                    for kw in SENSITIVE_KEYWORDS:
                        if kw in title:
                            rect = RECT()
                            if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                                w = rect.right - rect.left
                                h = rect.bottom - rect.top
                                # Pastikan jendela memiliki dimensi yang valid
                                if w > 50 and h > 50:
                                    boxes.append((rect.left, rect.top, rect.right, rect.bottom))
                                    logger.info(f"Jendela sensitif terdeteksi untuk sensor: '{buffer.value[:40]}' di {rect.left},{rect.top}")
                            break
            return True

        user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

    except Exception as e:
        logger.warning(f"Gagal memindai jendela Windows untuk sensor privasi: {e}")

    return boxes


def redact_image(
    image: Image.Image,
    boxes: Optional[List[Tuple[int, int, int, int]]] = None,
    blur_radius: int = 30,
) -> Image.Image:
    """
    Menyensor area tertentu pada gambar dengan Gaussian Blur tebal
    dan overlay tanda air proteksi privasi.
    """
    if not config.enable_vision_redaction:
        return image

    target_boxes = boxes if boxes is not None else get_sensitive_window_boxes()
    if not target_boxes:
        return image

    redacted_img = image.copy()
    draw = ImageDraw.Draw(redacted_img, "RGBA")
    img_w, img_h = redacted_img.size

    for (left, top, right, bottom) in target_boxes:
        # Clamp koordinat ke batas dimensi gambar
        c_left = max(0, min(left, img_w - 1))
        c_top = max(0, min(top, img_h - 1))
        c_right = max(0, min(right, img_w))
        c_bottom = max(0, min(bottom, img_h))

        if c_right <= c_left or c_bottom <= c_top:
            continue

        box = (c_left, c_top, c_right, c_bottom)

        # 1. Terapkan Gaussian Blur tebal pada area sensitif
        cropped_region = redacted_img.crop(box)
        blurred_region = cropped_region.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        redacted_img.paste(blurred_region, box)

        # 2. Gambar overlay transparan gelap dan garis batas
        draw.rectangle(box, fill=(15, 17, 23, 180), outline=(255, 82, 82, 220), width=2)

        # 3. Beri teks penanda sensor privasi
        label_text = "🔒 SENSITIVE REGION REDACTED (Rule 01)"
        draw.text(
            (c_left + 12, c_top + 12),
            label_text,
            fill=(240, 242, 248, 240),
        )

    logger.info(f"Berhasil menyensor {len(target_boxes)} area sensitif pada tangkapan layar.")
    return redacted_img
