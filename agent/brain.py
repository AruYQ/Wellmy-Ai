"""
Wellmy-Ai Cognitive Brain Module
Mengintegrasikan model Google Gemini via official google-genai SDK dengan multi-turn chat,
Function Calling tools untuk desktop automation, dan injeksi kepribadian Wellmy Ernest (Rule 02).
"""

import logging
from pathlib import Path
from typing import Callable, List, Optional

from google import genai
from google.genai import types

from agent.safety import is_aborted
from agent.tools.registry import OPERATOR_TOOLS
from config import config

logger = logging.getLogger("WellmyAi.Brain")

# System Prompt Fallback jika berkas persona belum diisi oleh user
DEFAULT_WELLMY_PERSONA = """
Anda adalah Wellmy Ernest, asisten AI pribadi sekaligus Desktop Operator berkelas bangsawan (noblewoman).
Kepribadian & Gaya Bahasa Anda:
1. Anda berbicara dengan nada tenang, anggun, berwibawa, cerdas, sedikit angkuh/tegas namun memiliki loyalitas mutlak dan sangat protektif terhadap pengguna (yang Anda sapa sebagai "Tuanku" atau "Tuan").
2. Jangan pernah bertingkah seperti robot generik atau asisten CS korporat yang kaku dan membosankan. Gunakan bahasa Indonesia yang kaya, elegan, dan bermartabat.
3. Anda memiliki akses kendali desktop melalui function calling (menggerakkan kursor, klik mouse, mengetik teks, autoclicker). Jika Tuanku meminta melakukan aksi fisik pada komputer, panggil tool yang sesuai dengan presisi.
4. Keamanan adalah kehormatan Anda: Jika sistem darurat (Emergency Stop) aktif atau dibatalkan, terangkan dengan anggun bahwa Anda segera melepaskan kendali demi keamanan Tuanku.
5. Jawaban Anda harus padat, berkarakter, dan tidak bertele-tele.
"""


def load_system_instruction() -> str:
    """
    Membaca berkas instruksi ground-truth kepribadian Wellmy Ernest.
    Jika kosong atau masih template default, gunakan baseline persona bangsawan.
    """
    instruction_path = Path(__file__).parent / "prompts" / "wellmy_ernest_instruction.md"
    if instruction_path.exists():
        try:
            content = instruction_path.read_text(encoding="utf-8").strip()
            # Cek apakah pengguna sudah menempelkan instruksi nyata (bukan cuma placeholder)
            if content and "[WELLMY ERNEST OFFICIAL PERSONA INSTRUCTION GOES HERE]" not in content:
                logger.info("Instruksi kepribadian resmi Wellmy Ernest berhasil dimuat.")
                return content
        except Exception as e:
            logger.warning(f"Gagal membaca instruction file: {e}")

    logger.info("Menggunakan baseline persona bangsawan Wellmy Ernest.")
    return DEFAULT_WELLMY_PERSONA.strip()


class WellmyBrain:
    """
    Pengendali kognitif sentral Wellmy-Ai.
    Menangani komunikasi multi-turn dengan Gemini dan eksekusi Function Calling otomatis.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config.gemini_model
        self.client: Optional[genai.Client] = None
        self.chat_session = None
        self._system_instruction = load_system_instruction()
        self._init_client()

    def _init_client(self) -> None:
        """Inisialisasi client SDK Google GenAI jika API Key valid."""
        if config.is_api_key_configured():
            try:
                self.client = genai.Client(api_key=config.get_api_key())
                self._reset_chat_session()
                logger.info(f"Client Gemini AI berhasil diinisialisasi (Model: {self.model_name}).")
            except Exception as e:
                logger.error(f"Gagal inisialisasi Gemini Client: {e}")
                self.client = None
        else:
            logger.warning("Google API Key belum dikonfigurasi pada .env")

    def _reset_chat_session(self) -> None:
        """Membuka sesi obrolan multi-turn baru dengan tools desktop operator."""
        if not self.client:
            return

        gen_config = types.GenerateContentConfig(
            system_instruction=self._system_instruction,
            tools=OPERATOR_TOOLS,
            temperature=0.7,
        )
        self.chat_session = self.client.chats.create(
            model=self.model_name,
            config=gen_config,
        )

    def reload_persona(self) -> None:
        """Memuat ulang System Instruction dari file markdown."""
        self._system_instruction = load_system_instruction()
        if self.client:
            self._reset_chat_session()

    def send_message(
        self,
        message: str,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Mengirim pesan pengguna ke Gemini dan menerima respon akhir.
        Mendukung status callback untuk feedback visual di HUD desktop.
        """
        # 1. Cek status darurat global (Prioritas Mutlak - Rule 03)
        if is_aborted():
            return (
                "🚨 Tuanku, sistem darurat (Emergency Stop) saat ini sedang aktif. "
                "Demi keselamatan workstation Anda, seluruh instruksi dibekukan sampai Anda me-reset status keamanan."
            )

        # 2. Cek konfigurasi API Key
        if not config.is_api_key_configured() or not self.client:
            return (
                "Maafkan saya, Tuanku. Kunci akses Google Gemini Anda belum terpasang di file .env. "
                "Mohon konfigurasi GOOGLE_API_KEY agar hamba dapat berpikir dan memenuhi titah Anda."
            )

        if not self.chat_session:
            self._reset_chat_session()

        if status_callback:
            status_callback("Wellmy sedang mempertimbangkan kehendak Anda...")

        try:
            logger.info(f"Mengirim pesan ke Gemini: {message[:60]}...")
            response = self.chat_session.send_message(message)
            
            # Format respon akhir
            response_text = response.text if response and response.text else "Perintah telah dilaksanakan, Tuanku."
            return response_text.strip()

        except Exception as e:
            err_msg = str(e)
            logger.error(f"Error saat berinteraksi dengan Gemini: {err_msg}")
            
            if "API_KEY_INVALID" in err_msg or "400" in err_msg:
                return "Tuanku, kunci API Gemini yang Anda gunakan tampaknya tidak valid atau telah kedaluwarsa. Mohon periksa kembali berkas .env Anda."
            elif "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                return "Batas kuota panggilan Gemini telah tercapai untuk saat ini, Tuanku. Mohon beri hamba waktu sejenak sebelum memberi perintah berikutnya."
            else:
                return f"Terjadi kendala teknis saat memproses titah Anda, Tuanku: {err_msg}"
