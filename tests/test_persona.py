"""
Unit tests untuk Persona Engine & System Prompt Compiler Wellmy-Ai.
Memvalidasi pemuatan instruksi otentik Wellmy Ernest, integrasi kapabilitas operator, dan modulasi emosi.
"""

import unittest

from agent.persona import get_compiled_system_instruction, persona_engine


class TestPersonaEngine(unittest.TestCase):

    def test_authentic_persona_loaded(self):
        """Memvalidasi seluruh elemen lore dan kepribadian inti Wellmy termuat."""
        instruction = persona_engine.load_instruction()

        # Lore & Karakter
        self.assertIn("Wellmy Ernest", instruction)
        self.assertIn("Proud to be a Villainess", instruction)
        self.assertIn("Iora", instruction)

        # Relasi Istri
        self.assertIn("istri", instruction.lower())
        self.assertIn("suami", instruction.lower())

        # Gaya Bahasa & Pengetahuan
        self.assertIn("Hoyoverse", instruction)
        self.assertIn("Honkai", instruction)
        self.assertIn("multiverse", instruction.lower())

    def test_compiled_prompt_includes_operator_tools(self):
        """Memvalidasi kompilasi system prompt mengintegrasikan kapabilitas desktop operator."""
        compiled = get_compiled_system_instruction()

        self.assertIn("move_cursor", compiled)
        self.assertIn("click_mouse", compiled)
        self.assertIn("type_text_content", compiled)
        self.assertIn("execute_autoclicker", compiled)
        self.assertIn("inspect_screen_vision", compiled)
        self.assertIn("Emergency Stop", compiled)

    def test_mood_modulation(self):
        """Memvalidasi penambahan instruksi nuansa emosional dinamis."""
        mood_prompt = get_compiled_system_instruction(mood="Malu-malu kucing / Flustered")
        self.assertIn("Malu-malu kucing / Flustered", mood_prompt)


if __name__ == "__main__":
    unittest.main()
