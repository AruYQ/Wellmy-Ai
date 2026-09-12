"""
Engine Text-to-Speech (TTS) untuk Wellmy-Ai.
Menghasilkan sintesis suara neural bangsawan elegan (id-ID-GadisNeural / WaveNet)
dengan caching audio lokal dan dukungan suara darurat pre-cached tanpa latensi.
"""

import asyncio
import base64
import hashlib
import logging
import math
import struct
import wave
from pathlib import Path
from typing import Optional

from agent.safety import is_aborted
from config import config

logger = logging.getLogger("wellmy.voice.tts")


class TTSEngine:
    """
    Klien Text-to-Speech resmi untuk kepribadian Wellmy Ernest.
    Menggunakan profil suara alto elegan (id-ID-GadisNeural, rate -5%, pitch -2Hz)
    berbasis Neural TTS bebas kuota dan fallback Google Cloud TTS.
    """

    DEFAULT_VOICE = "id-ID-GadisNeural"
    SPEAKING_RATE = "-5%"
    PITCH = "-2Hz"

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path(".cache/audio")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._emergency_sound_path = self.cache_dir / "emergency_abort.wav"
        self._ensure_emergency_sound()

    def _get_cache_path(self, text: str) -> Path:
        """Menghasilkan path file cache berdasarkan hash SHA-256 dari teks & parameter."""
        cache_key = f"{text}_{self.DEFAULT_VOICE}_{self.SPEAKING_RATE}_{self.PITCH}"
        text_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{text_hash}.mp3"

    def _ensure_emergency_sound(self) -> Path:
        """
        Menyiapkan file audio darurat lokal (WAV) secara instan.
        Dibuat secara sintetik agar tidak bergantung pada internet ketika panic switch aktif.
        """
        if self._emergency_sound_path.exists() and self._emergency_sound_path.stat().st_size > 0:
            return self._emergency_sound_path

        try:
            sample_rate = 22050
            duration_sec = 0.35
            num_samples = int(sample_rate * duration_sec)

            with wave.open(str(self._emergency_sound_path), "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)

                # Dua nada peringatan menurun tajam (880Hz -> 440Hz)
                frames = bytearray()
                for i in range(num_samples):
                    t = float(i) / sample_rate
                    freq = 880.0 if t < 0.18 else 440.0
                    decay = math.exp(-t * 4.0)
                    sample = int(16000.0 * decay * math.sin(2.0 * math.pi * freq * t))
                    frames.extend(struct.pack("<h", max(-32767, min(32767, sample))))

                wav_file.writeframes(frames)
            logger.info(f"File audio darurat disiapkan: {self._emergency_sound_path}")
        except Exception as e:
            logger.error(f"Gagal membuat file audio darurat lokal: {e}")

        return self._emergency_sound_path

    @property
    def emergency_sound_path(self) -> Path:
        return self._emergency_sound_path

    def _synthesize_edge_tts(self, text: str, output_path: Path) -> bool:
        """Sintesis ucapan menggunakan engine Edge Neural Voice (id-ID-GadisNeural)."""
        try:
            import edge_tts

            async def _run():
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=self.DEFAULT_VOICE,
                    rate=self.SPEAKING_RATE,
                    pitch=self.PITCH,
                )
                await communicate.save(str(output_path))

            asyncio.run(_run())
            return output_path.exists() and output_path.stat().st_size > 0
        except Exception as e:
            logger.error(f"Gagal sintesis edge-tts: {e}")
            return False

    def synthesize(self, text: str) -> Optional[Path]:
        """
        Melakukan sintesis ucapan menjadi file audio.
        Mengecek cache lokal terlebih dahulu untuk efisiensi dan kecepatan.
        Mengembalikan Path file audio (MP3) yang siap diputar, atau None jika gagal.
        """
        clean_text = text.strip()
        if not clean_text:
            return None

        # Failsafe check (Rule 03)
        if is_aborted():
            logger.warning("Sintesis TTS dibatalkan karena sistem dalam keadaan darurat (Aborted).")
            return None

        cache_path = self._get_cache_path(clean_text)
        if cache_path.exists() and cache_path.stat().st_size > 0:
            logger.debug(f"Mengambil audio dari cache lokal: {cache_path.name}")
            return cache_path

        logger.info(f"Meminta sintesis suara neural Wellmy untuk teks: {clean_text[:40]}...")

        # 1. Coba Edge Neural TTS (Kualitas tinggi, bebas kuota, tanpa repot OAuth)
        if self._synthesize_edge_tts(clean_text, cache_path):
            logger.info(f"Sintesis suara neural berhasil disimpan ke cache: {cache_path.name}")
            return cache_path

        # 2. Fallback Google Cloud TTS jika konfigurasi tersedia
        if config.is_api_key_configured():
            try:
                import requests
                api_key = config.google_api_key.get_secret_value()
                url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
                payload = {
                    "input": {"text": clean_text},
                    "voice": {
                        "languageCode": "id-ID",
                        "name": "id-ID-Wavenet-A",
                        "ssmlGender": "FEMALE",
                    },
                    "audioConfig": {
                        "audioEncoding": "MP3",
                        "speakingRate": 0.90,
                        "pitch": -1.5,
                    },
                }
                headers = {"Content-Type": "application/json"}
                resp = requests.post(url, json=payload, headers=headers, timeout=8.0)
                if resp.status_code == 200:
                    data = resp.json()
                    audio_b64 = data.get("audioContent")
                    if audio_b64:
                        cache_path.write_bytes(base64.b64decode(audio_b64))
                        return cache_path
            except Exception as e:
                logger.error(f"Fallback Google Cloud TTS gagal: {e}")

        logger.error("Seluruh engine sintesis suara gagal menghasilkan audio.")
        return None
