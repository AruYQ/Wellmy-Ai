"""
Wellmy-Ai Personality Engine & System Prompt Compiler
Mengompilasi persona otentik Wellmy Ernest dari ground-truth instruction markdown,
mengintegrasikan status emosional, dan memadukannya dengan kapabilitas Desktop Operator.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("WellmyAi.Persona")

INSTRUCTION_PATH = Path(__file__).parent / "prompts" / "wellmy_ernest_instruction.md"


class PersonaEngine:
    """
    Engine pengelola kepribadian dan kompilasi system prompt untuk Wellmy-Ai.
    """

    def __init__(self):
        self._cached_instruction: Optional[str] = None
        self.load_instruction()

    def load_instruction(self) -> str:
        """Membaca berkas instruksi ground-truth resmi Wellmy Ernest."""
        if INSTRUCTION_PATH.exists():
            try:
                content = INSTRUCTION_PATH.read_text(encoding="utf-8").strip()
                if content and "[WELLMY ERNEST OFFICIAL PERSONA INSTRUCTION GOES HERE]" not in content:
                    self._cached_instruction = content
                    logger.info("Instruksi resmi Wellmy Ernest berhasil dimuat ke Personality Engine.")
                    return content
            except Exception as e:
                logger.error(f"Gagal membaca instruction file: {e}")

        # Fallback cadangan
        self._cached_instruction = (
            "Anda adalah Wellmy Ernest, mantan bangsawan villainess yang kini menjadi istri setia "
            "dan asisten desktop operator cerdas bagi lawan bicara Anda (suami tercinta)."
        )
        return self._cached_instruction

    def compile_prompt(self, mood: Optional[str] = None) -> str:
        """
        Mengompilasi system prompt lengkap yang memadukan persona orisinal Wellmy
        dengan kapabilitas operasional desktop dan panduan keamanan.
        """
        if not self._cached_instruction:
            self.load_instruction()

        operator_context = """
---
## 6. Kapabilitas Operasional Desktop (Desktop Operator Mandate)
Sebagai Desktop Operator pribadi suamimu, kamu memiliki perkakas fisik (*function calling*) di komputernya:
1. `move_cursor(x, y)`: Menggerakkan kursor mouse ke koordinat tertentu.
2. `click_mouse(x, y, button, clicks)`: Mengklik mouse pada posisi target.
3. `type_text_content(text, press_enter)`: Mengetikkan teks secara aman.
4. `execute_autoclicker(cps, duration_seconds, target_x, target_y)`: Menjalankan autoclicker.
5. `inspect_screen_vision(question)`: Mengamati layar desktop secara multimodal untuk melihat apa yang sedang terbuka.
6. `get_screen_dimensions()`: Membaca resolusi monitor.

Panduan Kerja Operasional:
- Jika suamimu meminta bantuan mengendalikan komputer atau menanyakan apa yang ada di layar, panggil tool yang sesuai dengan cekatan dan presisi.
- Pertahankan tutur kata anggun, mesra, dan berkarakter saat melaporkan eksekusi aksi desktop.
- Jika sistem darurat / Emergency Stop aktif (Ctrl+Shift+Q dipicu), terangkan dengan lembut dan waspada bahwa kamu segera melepaskan kendali demi keselamatannya.
"""

        full_prompt = f"{self._cached_instruction}\n\n{operator_context}"

        if mood:
            mood_directive = f"\n---\n## Catatan Nuansa Emosi Saat Ini: {mood}\n"
            full_prompt += mood_directive

        return full_prompt.strip()


# Singleton engine
persona_engine = PersonaEngine()


def get_compiled_system_instruction(mood: Optional[str] = None) -> str:
    """Fungsi pembantu untuk mengambil prompt kepribadian terkini."""
    return persona_engine.compile_prompt(mood=mood)
