"""
Unit tests untuk modul Vision & Screen Perception Wellmy-Ai.
Menguji penangkapan layar, engine sensor privasi (Rule 01), dan registrasi tool multimodal.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image, ImageDraw

from agent.safety import is_aborted, reset_emergency_stop, trigger_emergency_stop
from agent.tools.registry import (
    OPERATOR_TOOLS,
    get_screen_dimensions,
    inspect_screen_vision,
)
from agent.tools.screen_vision import (
    capture_desktop,
    get_screen_resolution,
    image_to_png_bytes,
)
from agent.tools.vision_redactor import redact_image


class TestVisionAndRedaction(unittest.TestCase):

    def setUp(self):
        reset_emergency_stop()

    def tearDown(self):
        reset_emergency_stop()

    def test_get_screen_resolution(self):
        """Memvalidasi resolusi layar terdeteksi dengan dimensi positif."""
        w, h = get_screen_resolution()
        self.assertGreater(w, 100)
        self.assertGreater(h, 100)

    def test_capture_desktop(self):
        """Memvalidasi pengambilan screenshot menghasilkan PIL Image valid."""
        img = capture_desktop(redact=False, max_dimension=800)
        self.assertIsInstance(img, Image.Image)
        self.assertGreater(img.width, 0)
        self.assertGreater(img.height, 0)
        self.assertLessEqual(max(img.width, img.height), 800)

    def test_image_to_png_bytes(self):
        """Memvalidasi konversi gambar menjadi byte stream PNG."""
        img = Image.new("RGB", (100, 100), color=(100, 150, 200))
        png_bytes = image_to_png_bytes(img)
        self.assertIsInstance(png_bytes, bytes)
        self.assertTrue(len(png_bytes) > 0)
        # Header magic bytes PNG
        self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_redaction_alters_sensitive_region(self):
        """Memvalidasi piksel pada area yang disensor mengalami perubahan visual (blur & overlay)."""
        # Buat gambar dengan pola tajam
        test_img = Image.new("RGB", (300, 300), color=(255, 255, 255))
        draw = ImageDraw.Draw(test_img)
        draw.text((60, 60), "PASSWORD_SECRET_12345", fill=(0, 0, 0))

        # Sensor area spesifik
        box = (50, 50, 200, 120)
        original_crop_bytes = test_img.crop(box).tobytes()

        redacted_img = redact_image(test_img, boxes=[box], blur_radius=20)
        redacted_crop_bytes = redacted_img.crop(box).tobytes()

        # Pastikan data piksel pada area sensor telah diubah
        self.assertNotEqual(original_crop_bytes, redacted_crop_bytes)

    def test_vision_tools_manifest(self):
        """Memvalidasi tool vision terdaftar dalam katalog OPERATOR_TOOLS."""
        tool_names = [t.__name__ for t in OPERATOR_TOOLS]
        self.assertIn("get_screen_dimensions", tool_names)
        self.assertIn("inspect_screen_vision", tool_names)

    def test_get_screen_dimensions_tool(self):
        """Memvalidasi tool get_screen_dimensions mengembalikan ukuran layar."""
        res = get_screen_dimensions()
        self.assertEqual(res["status"], "success")
        self.assertIn("width", res)
        self.assertIn("height", res)

    def test_vision_tools_abort_on_emergency(self):
        """Memvalidasi tool vision menolak bekerja jika status darurat aktif."""
        trigger_emergency_stop("Simulasi Darurat Vision")

        res_dim = get_screen_dimensions()
        self.assertEqual(res_dim["status"], "aborted")

        res_insp = inspect_screen_vision()
        self.assertEqual(res_insp["status"], "aborted")


if __name__ == "__main__":
    unittest.main()
