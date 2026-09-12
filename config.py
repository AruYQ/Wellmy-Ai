"""
Wellmy-Ai Configuration & Secrets Management Module
Menggunakan pydantic-settings dengan enkapsulasi SecretStr untuk isolasi kredensial mutlak (Rule 01).
"""

from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Konfigurasi utama aplikasi dengan proteksi rahasia."""

    google_api_key: SecretStr = Field(
        default=SecretStr("your_gemini_api_key_here"),
        description="API Key resmi Google Gemini (Tipe SecretStr mencegah kebocoran log/traceback)",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Model Gemini yang digunakan untuk penalaran dan function calling",
    )
    panic_hotkey: str = Field(
        default="ctrl+shift+q",
        description="Pintasan global darurat untuk menghentikan seluruh aktivitas instan",
    )
    gui_theme: str = Field(
        default="dark",
        description="Tema visual antarmuka desktop (dark/light)",
    )
    log_level: str = Field(
        default="INFO",
        description="Tingkat kedalaman pencatatan log sistem",
    )
    enable_vision_redaction: bool = Field(
        default=True,
        description="Mengaktifkan pengaburan otomatis area jendela sensitif saat tangkapan layar",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def is_api_key_configured(self) -> bool:
        """Memeriksa apakah API Key telah diisi dengan nilai yang valid (bukan placeholder)."""
        val = self.google_api_key.get_secret_value().strip()
        return bool(val and val != "your_gemini_api_key_here")

    def get_api_key(self) -> str:
        """Mengambil nilai mentah API key secara aman untuk pengiriman ke SDK resmi."""
        return self.google_api_key.get_secret_value()


# Inisialisasi singleton config
config = AppConfig()
