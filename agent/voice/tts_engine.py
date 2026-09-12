"""
Engine Text-to-Speech (TTS) Google Cloud WaveNet untuk Wellmy-Ai.
Menghasilkan sintesis suara bangsawan elegan (id-ID-Wavenet-A) dengan caching audio lokal
dan dukungan suara darurat pre-cached tanpa latensi.
"""

import base64
import hashlib
import json
import logging
import math
import struct
import wave
from pathlib import Path
from typing import Optional

import requests

from config import config
from agent.safety import is_aborted

logger = logging.getLogger("wellmy.voice.tts")


class TTSEngine:
    """
    Klien Text-to-Speech resmi untuk kepribadian Wellmy Ernest.
    Menggunakan profil suara alto elegan (id-ID-Wavenet-A, pitch -1.5st, rate 0.90).
    """

    DEFAULT_VOICE = "id-ID-Wavenet-A"
    DEFAULT_LANG = "id-ID"
    DEFAULT_GENDER = "FEMALE"
    SPEAKING_RATE = 0.90
    PITCH = -1.5

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

    def synthesize(self, text: str) -> Optional[Path]:
        """
        Melakukan sintesis ucapan menjadi file audio.
        Mengecek cache lokal terlebih dahulu untuk efisiensi kuota dan kecepatan.
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

        # Cek API Key
        if not config.is_api_key_configured():
            logger.warning("API Key tidak terkonfigurasi. Melewati sintesis TTS Google Cloud.")
            return None

        api_key = config.google_api_key.get_secret_value()
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"

        payload = {
            "input": {"text": clean_text},
            "voice": {
                "languageCode": self.DEFAULT_LANG,
                "name": self.DEFAULT_VOICE,
                "ssmlGender": self.DEFAULT_GENDER,
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": self.SPEAKING_RATE,
                "pitch": self.PITCH,
            },
        }

        headers = {"Content-Type": "application/json"}

        try:
            logger.info(f"Meminta sintesis WaveNet Google Cloud untuk teks: {clean_text[:40]}...")
            resp = requests.post(url, json=payload, headers=headers, timeout=8.0)

            if resp.status_code == 200:
                data = resp.json()
                audio_content_b64 = data.get("audioContent")
                if audio_content_b64:
                    audio_bytes = base64.b64decode(audio_content_b64)
                    cache_path.write_bytes(audio_bytes)
                    logger.info(f"Sintesis suara berhasil disimpan ke cache: {cache_path.name}")
                    return cache_path

            # Fallback jika model Wavenet tidak tersedia untuk akun ini, coba id-ID-Standard-A
            if resp.status_code == 400 and self.DEFAULT_VOICE != "id-ID-Standard-A":
                logger.warning(f"Voice {self.DEFAULT_VOICE} gagal ({resp.status_code}), mencoba fallback Standard-A...")
                payload["voice"]["name"] = "id-ID-Standard-A"
                fallback_resp = requests.post(url, json=payload, headers=headers, timeout=8.0)
                if fallback_resp.status_code == 200:
                    data = fallback_resp.json()
                    audio_bytes = base64.b64decode(data.get("audioContent", ""))
                    if audio_bytes:
                        cache_path.write_bytes(audio_bytes)
                        return cache_path

            logger.error(f"Google Cloud TTS API menolak permintaan: HTTP {resp.status_code} - {resp.text[:120]}")
            return None

        except Exception as e:
            logger.error(f"Kesalahan jaringan saat memanggil Google Cloud TTS: {e}")
            return None
