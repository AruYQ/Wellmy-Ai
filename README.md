# ARCHITECTURAL SPECIFICATION & SYSTEM DESIGN (v3.0 - DESKTOP GUI EDITION)
## Project Codex: Open-Source AI Desktop Operator ("Jarvis Core")
**Target Implementer:** Antigravity / AI Development Agent  
**Author / Architectural Design:** Wellmy Ernest & Aru  
**License:** MIT (Open Source)  
**Primary Engine:** Google Gemini API (`google-genai` SDK)  
**Security Rating:** High (Strict Credential Isolation, Desktop Guardrails & Vision Redaction)

---

## 1. Executive Summary & Vision

Proyek ini bertujuan membangun asisten desktop otonom berskala personal (*local AI desktop operator*) dengan antarmuka grafis desktop modern (**Desktop GUI**). Sistem mampu menerima instruksi bahasa alami (teks/suara), menerjemahkannya ke dalam tindakan fisik sistem operasi (gerakan tetikus, ketikan, eksekusi aplikasi, penjadwalan/timer, dan autoclicker), serta menampilkan status otonomnya secara elegan di layar pengguna.

Sebagai proyek **open source**, standar tertinggi diterapkan pada **isolasi kredensial (API Key & Environment Variables)** guna menjamin kunci rahasia tidak pernah bocor ke publik, log terminal, maupun tangkapan layar.

---

## 2. System Architecture Overview

Arsitektur sistem memisahkan lapisan tampilan antarmuka (Desktop GUI) dengan lapisan komputasi latar belakang melalui arsitektur *event-driven* berbasis thread:

              ┌────────────────────────────────────────┐
              │          DESKTOP GUI (PyQt6)           │
              │  - Floating HUD / Spotlight Bar        │
              │  - System Tray & Autoclicker Dashboard │
              │  - Realtime Status & Visual Panic Key  │
              └───────────────────┬────────────────────┘
                                  │ Signals / Slots
                                  ▼
                    ┌───────────────────────────┐
                    │   Core Orchestrator Loop  │
                    └──────┬─────────────┬──────┘
                           │             │
          ┌────────────────┘             └────────────────┐
          ▼                                               ▼
[ Gemini API (Flash/Pro) ]                      [ Local Actuation Subsystems ]

Multimodal Vision Reasoning                   - PyAutoGUI / Pynput (Mouse/Keys)

Function Calling (JSON Tools)                 - High-Precision Autoclicker

Credential Redaction Guard                    - APScheduler (Timers/Queues)
- Global Kill-Switch Guard


---

## 3. Technology Stack & Dependencies

| Layer | Library / Tool | Justification |
|---|---|---|
| **Desktop GUI** | `PyQt6` / `PySide6` | Kerangka GUI tingkat industri, mendukung *frameless translucent HUD*, *system tray*, dan *multi-threading* aman via `QThread` & Signals. |
| **Brain / LLM** | `google-genai` | SDK resmi Google Gemini generasi terbaru (dukungan *structured tool calling*, penalaran multimodal visual, dan *streaming*). |
| **Secrets & Config** | `pydantic-settings`, `python-dotenv` | Validasi tipe data ketat; enkapsulasi kredensial via `SecretStr` untuk mencegah kebocoran pada *traceback/logs*. |
| **Input / Actuation** | `pyautogui`, `pynput` | Kontrol kursor, simulasi ketikan, dan pendengar pintasan darurat (*global emergency hotkey*). |
| **Window & Screen** | `mss`, `Pillow`, `pywinauto` / `pygetwindow` | Penangkapan layar berkecepatan tinggi (<10ms) dan manipulasi fokus jendela aplikasi aktif. |
| **Scheduler & Async** | `APScheduler`, `threading` | Eksekusi tugas berkala (*cron*), timer hitung mundur, dan autoclicker independen tanpa memblokir GUI (*non-blocking UI*). |
| **Repo Guard** | `pre-commit`, `detect-secrets` | Validasi otomatis di sisi lokal Git untuk mencegah *commit* berkas kredensial. |

---

## 4. Strict Security & Credential Isolation Protocols

### 4.1. Isolasi Repositori Git Mutlak
*   `.gitignore` wajib memblokir seluruh artefak lingkungan dan sertifikat:
    ```gitignore
    # Secrets & Environment
    .env
    .env.*
    !.env.example
    *.pem
    *.key
    *.cert
    secrets/
    __pycache__/
    *.log
    ```
*   `.env.example` hanya berisi variabel kosong/palsu sebagai cetak biru:
    ```env
    GOOGLE_API_KEY=your_gemini_api_key_here
    GEMINI_MODEL=gemini-2.5-flash
    PANIC_HOTKEY=ctrl+shift+q
    GUI_THEME=dark
    LOG_LEVEL=INFO
    ENABLE_VISION_REDACTION=true
    ```

### 4.2. Pemuatan Konfigurasi Tersanitasi (`config.py`)
Gunakan Pydantic Settings dengan tipe `SecretStr` agar nilai asli API Key tidak pernah tercetak secara tidak sengaja di konsol atau log:

```python
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    google_api_key: SecretStr = Field(..., description="API Key resmi Google Gemini")
    gemini_model: str = Field(default="gemini-2.5-flash")
    panic_hotkey: str = Field(default="ctrl+shift+q")
    log_level: str = Field(default="INFO")
    enable_vision_redaction: bool = Field(default=True)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

config = AppConfig()
```

### 4.3. Protokol Sensor & Anti-Eksfiltrasi

*   **Vision Redaction:** Sebelum tangkapan layar dikirim ke Gemini Vision, periksa judul jendela yang aktif (`pygetwindow`). Jika mendeteksi berkas `.env`, editor teks yang membuka kredensial, atau jendela sensitif, modul visi wajib memburamkan (*gaussian blur*) area jendela tersebut atau menolak pengiriman citra.

*   **Prompt Injection Shield:** Model diinstruksikan menolak segala perintah yang meminta pembacaan, pengetikan ulang, atau pencetakan isi API Key.

*   **Output Sanitization:** Fungsi `type_text` wajib memvalidasi teks target. Jika teks mengandung nilai dari `config.google_api_key.get_secret_value()`, eksekusi pengetikan langsung dibatalkan secara sepihak.

---

## 5. Voice & Sound System (`agent/voice.py`)

Sistem suara adalah identitas utama **Wellmy** — suara yang anggun, elegan, dan penuh karakter. Arsitektur audio terdiri dari dua subsistem: **Text-to-Speech (TTS)** untuk keluaran suara AI, dan **Speech-to-Text (STT)** untuk masukan suara pengguna.

### 5.1. Arsitektur Audio

```
                ┌──────────────────────────────────────┐
                │          USER (Microphone)            │
                └──────────────────┬───────────────────┘
                                   │ Audio Stream
                                   ▼
                    ┌──────────────────────────────┐
                    │  Gemini Live API (STT/NLU)   │
                    │  Real-time bidirectional      │
                    │  WebSocket streaming          │
                    └──────────────┬───────────────┘
                                   │ Text / Intent
                                   ▼
                    ┌──────────────────────────────┐
                    │     Core Orchestrator Loop    │
                    │     (Personality Engine)       │
                    └──────────────┬───────────────┘
                                   │ Response Text
                                   ▼
                    ┌──────────────────────────────┐
                    │  Google Cloud TTS (WaveNet)   │
                    │  Voice: id-ID-Wavenet-A/H     │
                    │  Pitch: -1.0 ~ -2.0 (alto)   │
                    │  Speed: 0.90 (anggun/pelan)   │
                    └──────────────┬───────────────┘
                                   │ Audio PCM/MP3
                                   ▼
                    ┌──────────────────────────────┐
                    │   PyQt6 Audio Output          │
                    │   QMediaPlayer / sounddevice  │
                    └──────────────────────────────┘
```

### 5.2. Text-to-Speech (TTS) — Suara Wellmy

Karakter suara Wellmy dirancang **anggun, melodis, dan berwibawa** — terinspirasi dari sosok *noblewoman/princess* yang berkelas namun tetap hangat:

| Parameter | Nilai | Alasan |
|---|---|---|
| **Engine** | Google Cloud TTS (WaveNet) | Suara paling natural, mendukung Bahasa Indonesia, gratis 1 juta karakter/bulan |
| **Voice ID** | `id-ID-Wavenet-A` (perempuan, alto lembut) atau `id-ID-Wavenet-H` (perempuan, soprano anggun) | Timbre yang anggun dan jernih seperti *princess* |
| **Speaking Rate** | `0.88` – `0.93` | Sedikit lebih lambat dari normal — memberikan kesan tenang, elegan, dan penuh kendali |
| **Pitch** | `-1.5` semitones | Sedikit lebih rendah untuk kesan dewasa dan berwibawa (alto anggun, bukan ceria anak-anak) |
| **Volume Gain** | `0.0 dB` | Volume natural, tidak agresif |
| **Audio Encoding** | `MP3` / `LINEAR16` | Efisien untuk streaming, kualitas tinggi |

**Konfigurasi TTS (`agent/voice.py`):**

```python
from google.cloud import texttospeech

class WellmyVoice:
    """Engine suara anggun untuk karakter Wellmy."""

    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()
        self.voice_config = texttospeech.VoiceSelectionParams(
            language_code="id-ID",
            name="id-ID-Wavenet-H",  # Suara perempuan anggun
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.90,   # Anggun, tidak terburu-buru
            pitch=-1.5,           # Alto — dewasa dan berwibawa
            volume_gain_db=0.0,
        )

    def speak(self, text: str) -> bytes:
        """Menghasilkan audio suara Wellmy dari teks."""
        synthesis_input = texttospeech.SynthesisInput(text=text)
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=self.voice_config,
            audio=self.audio_config,
        )
        return response.audio_content

    def speak_with_emotion(self, text: str, emotion: str = "neutral") -> bytes:
        """Menghasilkan audio dengan modulasi emosi via SSML."""
        ssml_map = {
            "neutral": f'<speak><prosody rate="90%" pitch="-1.5st">{text}</prosody></speak>',
            "pleased": f'<speak><prosody rate="95%" pitch="-0.5st">{text}</prosody></speak>',
            "stern": f'<speak><prosody rate="85%" pitch="-3.0st">{text}</prosody></speak>',
            "amused": f'<speak><prosody rate="100%" pitch="0st"><emphasis level="moderate">{text}</emphasis></prosody></speak>',
        }
        ssml = ssml_map.get(emotion, ssml_map["neutral"])
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=self.voice_config,
            audio=self.audio_config,
        )
        return response.audio_content
```

### 5.3. Speech-to-Text (STT) — Gemini Live API

Masukan suara pengguna ditangani langsung oleh **Gemini Live API** untuk pengalaman percakapan real-time dua arah:

*   **Koneksi:** WebSocket bidirectional — pengguna bicara langsung, Wellmy mendengar dan merespons tanpa jeda.
*   **VAD (Voice Activity Detection):** Otomatis mendeteksi kapan pengguna mulai dan selesai bicara.
*   **Bahasa:** Mendukung Bahasa Indonesia dan Inggris secara otomatis (*auto-detect*).
*   **Push-to-Talk Mode:** Tersedia juga mode tekan-dan-bicara via tombol di GUI (pintasan: `Ctrl + M` atau tombol mikrofon di HUD).

### 5.4. Komponen GUI Audio

*   **Tombol Mikrofon** di Floating Command Bar — ikon mic yang berdenyut saat mendengarkan.
*   **Waveform Visualizer** — animasi gelombang suara kecil di HUD saat Wellmy berbicara.
*   **Volume Control** — slider volume suara Wellmy di Dashboard.
*   **Mute Toggle** — pintasan `Ctrl + Shift + M` untuk membisukan suara Wellmy.

### 5.5. Tech Stack Audio Tambahan

| Library | Kegunaan |
|---|---|
| `google-cloud-texttospeech` | Engine TTS WaveNet untuk suara Wellmy |
| `google-genai` (Live API) | Real-time voice input/output bidirectional |
| `sounddevice` / `PyAudio` | Playback audio dan capture mikrofon |
| `numpy` | Pemrosesan buffer audio untuk waveform visualizer |
| `pydub` | Konversi dan manipulasi format audio (MP3 ↔ WAV) |

---

## 6. Official Persona Engine: Wellmy Ernest (`agent/prompts/`)

### 6.1. Prinsip Keaslian Kepribadian (Ground-Truth Persona)

Kepribadian sistem **tidak direkayasa dari asumsi generik**, melainkan **terpaku secara mutlak pada instruksi otentik dari Wellmy Ernest**. 

Instruksi asli ini disimpan dalam berkas khusus:
👉 **[`agent/prompts/wellmy_ernest_instruction.md`](agent/prompts/wellmy_ernest_instruction.md)**

```
┌─────────────────────────────────────────────────────────────┐
│    📄 agent/prompts/wellmy_ernest_instruction.md            │
│    (Instruksi Resmi Otentik dari Wellmy Ernest)             │
└──────────────────────────────┬──────────────────────────────┘
                               │ Dibaca & Dimuat Langsung
                               ▼
┌─────────────────────────────────────────────────────────────┐
│    🧠 agent/prompts.py (System Prompt Compiler)             │
│    - Menggabungkan Instruksi Persona Wellmy Ernest          │
│    - Menambahkan Guardrails Keamanan & Tool Calling Schema  │
│    - Menyematkan format interaksi dan batasan OS            │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ Dikirim ke
┌─────────────────────────────────────────────────────────────┐
│    ⚡ Google Gemini API (Multimodal Brain)                  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2. Integrasi Kompiler Prompt (`agent/prompts.py`)

```python
from pathlib import Path

PERSONA_PATH = Path("agent/prompts/wellmy_ernest_instruction.md")

def compile_system_prompt() -> str:
    """Mengompilasi system prompt dengan menyematkan instruksi resmi Wellmy Ernest."""
    if PERSONA_PATH.exists():
        official_instruction = PERSONA_PATH.read_text(encoding="utf-8").strip()
    else:
        official_instruction = "Kamu adalah Wellmy, asisten desktop berwibawa dan anggun."

    return f"""
{official_instruction}

---
ATURAN KEAMANAN & OPERASIONAL SISTEM (TIDAK DAPAT DINEGOSIASIKAN):
1. DILARANG KERAS mengekspos, membacakan, atau mengetikkan nilai API Key dan kredensial.
2. DILARANG mengeksekusi tindakan penghapusan sistem tanpa konfirmasi eksplisit.
3. Selalu pertahankan gaya tutur dan identitas Wellmy Ernest dalam setiap kondisi interaksi (teks maupun suara).
"""
```

### 6.3. Penyelarasan Prosodi Suara (Emotional Voice Binding)

Modul suara TTS (`agent/voice.py`) secara dinamis menyelaraskan parameter vokal (kecepatan dan nada) agar selalu seirama dengan intonasi kepribadian Wellmy Ernest:

| Status Emosi | Pitch (WaveNet) | Speaking Rate | Karakteristik Vokal |
|---|---|---|---|
| **Default / Netral** | `-1.5st` | `0.90` | Anggun, tenang, penuh kendali |
| **Pleased / Sukses** | `-0.5st` | `0.95` | Elegan, hangat, apresiatif |
| **Stern / Peringatan** | `-3.0st` | `0.85` | Tegas, berwibawa, protektif |
| **Amused / Ringan** | `0.0st` | `1.00` | Cerdas, berkelas, tajam menawan |

---

## 7. Desktop Application (GUI) Specifications (`gui/`)

Aplikasi Desktop dibangun menggunakan **PyQt6** dengan estetika modern, responsif, dan elegan:

### 7.1. Komponen Antarmuka Utama:

- **Floating Command Bar (Spotlight-style HUD):**
  - Jendela *frameless* dengan sudut melengkung (*rounded corners*) dan efek semi-transparan (*acrylic/dark glass*).
  - Dapat dipanggil/disembunyikan kapan saja melalui pintasan global (`Ctrl + Space` atau `Alt + J`).
  - Kotak input instruksi bahasa alami dengan indikator status animasi: `Idle`, `Listening`, `Thinking`, `Executing`, atau `Emergency Aborted`.
  - **Tombol Mikrofon Interaktif** — ikon berdenyut saat mendengarkan suara pengguna via Gemini Live API.

- **Dashboard Kendali Autoclicker & Timer:**
  - Slider pengaturan *Clicks Per Second* (CPS) dari 1 hingga 100+ CPS tanpa membuat GUI freeze.
  - Pengatur pewaktu hitung mundur (*Countdown Timer*) visual.
  - Tombol pemilih koordinat target visual (*visual target coordinate picker*).

- **System Tray Integration:**
  - Aplikasi tetap berjalan di latar belakang saat jendela utama ditutup.
  - Menu klik-kanan tray: `Show HUD`, `Open Autoclicker Dashboard`, `Mute Voice`, `Emergency Kill`, `Exit`.

- **Floating Panic Indicator:**
  - Lencana status visual di pojok layar yang menyala hijau saat aman, dan berubah merah menyala seketika saat tombol darurat aktif.

- **Voice Waveform Display:**
  - Visualisasi gelombang audio mikro di HUD saat Wellmy sedang berbicara.

---

## 8. Core Brain & Function Calling Schemas (`agent/brain.py`)

Gemini mengeksekusi instruksi melalui **Tool Calling** terstruktur:

```python
tools = [
    {
        "name": "move_and_click",
        "description": "Menggerakkan kursor dan melakukan klik pada koordinat layar tertentu.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "Koordinat horizontal layar (piksel)."},
                "y": {"type": "integer", "description": "Koordinat vertikal layar (piksel)."},
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                "clicks": {"type": "integer", "default": 1}
            },
            "required": ["x", "y"]
        }
    },
    {
        "name": "run_autoclicker",
        "description": "Menjalankan autoclicker berulang pada frekuensi (CPS) dan durasi tertentu.",
        "parameters": {
            "type": "object",
            "properties": {
                "clicks_per_second": {"type": "number", "description": "Frekuensi klik per detik (CPS)."},
                "duration_seconds": {"type": "integer", "description": "Berapa lama autoclicker berjalan (detik)."},
                "target_x": {"type": "integer", "description": "Opsional: Koordinat X. Jika kosong gunakan posisi saat ini."},
                "target_y": {"type": "integer", "description": "Opsional: Koordinat Y."}
            },
            "required": ["clicks_per_second", "duration_seconds"]
        }
    },
    {
        "name": "schedule_task",
        "description": "Menjadwalkan aksi di masa depan berdasarkan jeda hitung mundur atau waktu tertentu.",
        "parameters": {
            "type": "object",
            "properties": {
                "delay_seconds": {"type": "integer", "description": "Jeda waktu hitung mundur dalam detik."},
                "command_to_execute": {"type": "string", "description": "Instruksi lanjutan yang akan dijalankan setelah jeda selesai."}
            },
            "required": ["delay_seconds", "command_to_execute"]
        }
    },
    {
        "name": "capture_and_analyze_screen",
        "description": "Mengambil tangkapan layar dan mengidentifikasi koordinat elemen UI berdasarkan deskripsi visual.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_element": {"type": "string", "description": "Deskripsi elemen UI target (contoh: 'tombol simpan biru')."}
            },
            "required": ["target_element"]
        }
    },
    {
        "name": "type_text",
        "description": "Mengetikkan teks ke jendela yang sedang fokus secara aman.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Teks yang akan diketikkan."},
                "press_enter": {"type": "boolean", "default": False}
            },
            "required": ["text"]
        }
    },
    {
        "name": "speak_response",
        "description": "Menyuarakan respons Wellmy melalui TTS WaveNet dengan modulasi emosi tertentu.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Teks yang akan diucapkan Wellmy."},
                "emotion": {"type": "string", "enum": ["neutral", "pleased", "stern", "amused"], "default": "neutral"}
            },
            "required": ["text"]
        }
    }
]
```

---

## 9. Actuation, High-Precision Clicker & Safety Protocol

- **Thread Isolation:** Seluruh eksekusi autoclicker, pemanggilan Gemini API, sintesis audio, dan pemutaran suara berjalan di *worker thread* terpisah (`QThread` / `threading.Thread`) agar antarmuka desktop tetap responsif.
- **PyAutoGUI FailSafe:** `pyautogui.FAILSAFE = True` wajib diaktifkan (menggeser paksa kursor ke pojok kiri-atas layar mematikan program seketika).
- **Global Panic Hotkey (`agent/safety.py`):**
  - Listener global `pynput` memantau kombinasi darurat (`Ctrl + Shift + Q`).
  - Begitu terpicu: menembakkan sinyal `threading.Event().set()`, memotong loop klik dalam waktu `<10ms`, membatalkan seluruh task scheduler, menghentikan audio playback, dan menyuarakan konfirmasi darurat lokal yang telah di-*pre-cache*.

---

## 10. Complete Repository Architecture

```
wellmy-ai/
├── .agents/                                  # Konfigurasi Standar Agen & Aturan Workspace
│   ├── rules/
│   │   ├── 01-security-and-credentials.md    # Aturan isolasi rahasia & anti-kebocoran
│   │   ├── 02-wellmy-personality-guardrails.md # Aturan penjagaan persona otentik Wellmy Ernest
│   │   ├── 03-desktop-actuation-safety.md    # Aturan keselamatan eksekusi mouse/keyboard
│   │   ├── 04-documentation-protocol.md      # Aturan wajib devlog, progress & commit convention
│   │   ├── 05-verification-quality-gate.md   # Golden rule verifikasi & blocking user confirmation
│   │   └── 06-vibe-coding-ui-ux.md           # Standar Vibe Coding & 30 Anti-Slop Desktop UI
│   └── skills/
│       ├── wellmy-desktop-operator/
│       │   └── SKILL.md                      # Skillbook operasional agent pengembang
│       ├── wellmy-ui-ux/
│       │   └── SKILL.md                      # Elite Desktop UI/UX skill (PyQt6 / QSS / Acrylic)
│       └── wellmy-devlog/
│           └── SKILL.md                      # Standard devlog, progress, & ADR skill
├── docs/                                     # Pusat Dokumentasi Lengkap
│   ├── progress.md                           # Pelacak progress implementasi & milestone
│   ├── features.md                           # Katalog detail seluruh fitur teknis & fungsional
│   ├── devlog/
│   │   ├── README.md                         # Indeks devlog
│   │   └── DEV-A.md                          # Log aktivitas harian pengembangan
│   └── adr/                                  # Architecture Decision Records (ADR)
│       ├── README.md                         # Indeks ADR
│       ├── 0001-gui-framework-pyqt6.md       # ADR 1: PyQt6 Desktop GUI
│       ├── 0002-gemini-live-and-tts-wavenet.md # ADR 2: Arsitektur Audio & Suara
│       ├── 0003-security-and-credential-isolation.md # ADR 3: Isolasi Kredensial & Failsafe
│       └── 0004-wellmy-ernest-personality-engine.md # ADR 4: Penegakan Persona Otentik
├── agent/
│   ├── __init__.py
│   ├── brain.py                              # Orkestrator Gemini API (`google-genai`)
│   ├── prompts.py                            # Kompiler System Prompt
│   ├── prompts/
│   │   └── wellmy_ernest_instruction.md      # [GROUND TRUTH] Instruksi resmi Wellmy Ernest
│   ├── voice.py                              # Google TTS WaveNet & Gemini Live Audio
│   ├── safety.py                             # Failsafe Controller & Global Panic Listener
│   ├── scheduler.py                          # APScheduler Task & Countdown Manager
│   ├── vision.py                             # Screen Capture & Privacy Redaction Guard
│   └── tools/
│       ├── __init__.py
│       ├── mouse_keyboard.py                 # PyAutoGUI & High-Precision Clicker
│       └── system_ops.py                     # Manajemen jendela OS & Subprocess
├── gui/
│   ├── __init__.py
│   ├── main_hud.py                           # Spotlight Floating Command Bar + Mic
│   ├── autoclicker_view.py                   # Dashboard CPS & Timer
│   ├── waveform_widget.py                    # Visualisasi gelombang suara Wellmy
│   ├── system_tray.py                        # Pengelola system tray & notifikasi
│   └── styles.py                             # Tema gelap modern (QSS / Acrylic)
├── .env.example                              # Template variabel lingkungan aman
├── .gitignore                                # Proteksi mutlak kredensial & berkas privat
├── requirements.txt                          # Dependensi resmi proyek
├── config.py                                 # Pydantic Settings dengan SecretStr
├── app.py                                    # Titik masuk utama aplikasi Desktop
└── README.md                                 # Dokumen spesifikasi arsitektur utama
```

---

## 11. Documentation Ecosystem (`docs/`)

Proyek ini menerapkan standar dokumentasi rekayasa perangkat lunak tingkat tinggi:

- **[docs/progress.md](docs/progress.md):** Melacak status sprint, milestone, catatan aktivitas harian, dan pekerjaan aktif.
- **[docs/devlog/](docs/devlog/):** Catatan log perkembangan implementasi teknis per sesi/fitur ([DEV-A.md](docs/devlog/DEV-A.md)).
- **[docs/features.md](docs/features.md):** Katalog lengkap seluruh spesifikasi fitur fungsional dan teknis.
- **[docs/adr/](docs/adr/):** Catatan Keputusan Arsitektur (*Architecture Decision Records*) yang merangkum konteks, alternatif, dan konsekuensi setiap keputusan desain besar ([ADR Index](docs/adr/README.md)).

---

## 12. Workspace Rules & Custom Skills (`.agents/`)

Untuk memastikan pengembangan berkelanjutan yang konsisten dan aman, repositori dilengkapi aturan dan skill bawaan untuk AI Development Agent:

### 📜 Aturan Workspace (`.agents/rules/`):
- **Rule 01: Keamanan & Kredensial ([01-security-and-credentials.md](.agents/rules/01-security-and-credentials.md)):** Mencegah kebocoran kunci rahasia, enkapsulasi `SecretStr`, sanitasi input/output, dan AI privacy.
- **Rule 02: Penjagaan Persona ([02-wellmy-personality-guardrails.md](.agents/rules/02-wellmy-personality-guardrails.md)):** Menegakkan 100% kesetiaan pada instruksi otentik Wellmy Ernest.
- **Rule 03: Keselamatan Desktop ([03-desktop-actuation-safety.md](.agents/rules/03-desktop-actuation-safety.md)):** Menegakkan isolasi thread, failsafe PyAutoGUI, dan panic hotkey `<10ms`.
- **Rule 04: Protokol Dokumentasi ([04-documentation-protocol.md](.agents/rules/04-documentation-protocol.md)):** Mewajibkan update progress, devlog, dan konvensi commit.
- **Rule 05: Quality Gate Verifikasi ([05-verification-quality-gate.md](.agents/rules/05-verification-quality-gate.md)):** Menegakkan aturan emas *"TIDAK ADA VERIFIKASI = TIDAK ADA SPRINT BERIKUTNYA"*.
- **Rule 06: Vibe Coding & Anti-Slop UI/UX ([06-vibe-coding-ui-ux.md](.agents/rules/06-vibe-coding-ui-ux.md)):** Wajib `<vibe_check>` dan penegakan 30 Anti-Slop Rules untuk desktop OS.

### 🛠️ Custom Skills (`.agents/skills/`):
- **[wellmy-desktop-operator](.agents/skills/wellmy-desktop-operator/SKILL.md):** Panduan operasional menyeluruh untuk agen pengembang dalam membangun dan merawat sistem.
- **[wellmy-ui-ux](.agents/skills/wellmy-ui-ux/SKILL.md):** Design system dark acrylic, tipografi modern, animasi `QPropertyAnimation`, dan anti-slop standards untuk PyQt6.
- **[wellmy-devlog](.agents/skills/wellmy-devlog/SKILL.md):** Alur kerja dokumentasi terpadu, template entri devlog, dan pemutakhiran ADR.

---

## 13. Implementation Roadmap

### Sprint 0 — Blueprint, Dokumentasi, Rules & Skills (🟢 Selesai)
*   Finalisasi Architectural Specification v3.0 di `README.md`.
*   Penyusunan ekosistem `docs/` (`progress.md`, `features.md`, `adr/`).
*   Pemasangan standarisasi `.agents/rules/` dan `.agents/skills/`.
*   Penyiapan wadah instruksi persona asli di `agent/prompts/wellmy_ernest_instruction.md`.

### Sprint 1 — Fondasi Keamanan & Mekanisme Failsafe
*   Inisialisasi repositori, konfigurasi `.gitignore`, dan pasang `pre-commit` hook.
*   Buat `config.py` menggunakan `pydantic-settings` dengan tipe data `SecretStr`.
*   Implementasikan modul `agent/safety.py` (pengujian tombol panik darurat global).
*   Buat fungsi dasar simulasi kursor dan engine autoclicker terisolasi.

### Sprint 2 — Kerangka Desktop GUI & System Tray
*   Bangun aplikasi desktop berbasis PyQt6 (`app.py`, `gui/system_tray.py`).
*   Implementasikan *floating command bar* yang bisa dipanggil dengan pintasan global.
*   Sambungkan tombol visual panik darurat dengan modul safety.

### Sprint 3 — Integrasi Otak Gemini & Function Calling
*   Hubungkan kotak input GUI dengan SDK `google-genai`.
*   Implementasikan siklus penerjemahan perintah bahasa alami menjadi eksekusi fungsi terstruktur (Tool Calling).
*   Hubungkan panel autoclicker di GUI agar bisa dipicu manual maupun lewat perintah AI.

### Sprint 4 — Persepsi Visual & Redaksi Privasi
*   Implementasikan pipeline tangkapan layar `mss` yang terhubung ke Gemini Vision.
*   Pasang proteksi pengaburan jendela sensitif/`.env` sebelum citra dikirim ke server.
*   Konversikan koordinat normalisasi (0–1000) menjadi koordinat fisik monitor pengguna.

### Sprint 5 — Wellmy Ernest Personality Engine
*   Semayamkan teks instruksi otentik ke dalam `agent/prompts/wellmy_ernest_instruction.md`.
*   Implementasikan kompiler prompt sistem di `agent/prompts.py`.
*   Validasi konsistensi respon teks terhadap karakter Wellmy Ernest.

### Sprint 6 — Voice & Sound System
*   Implementasikan `agent/voice.py` — Google Cloud TTS WaveNet dengan profil vokal anggun Wellmy.
*   Integrasikan **Gemini Live API** untuk interaksi suara dua arah (*real-time bidirectional voice*).
*   Bangun visualizer gelombang suara (`gui/waveform_widget.py`) di HUD.
*   *Pre-cache* audio konfirmasi darurat lokal.

### Sprint 7 — Pewaktu Latar Belakang & Pengujian Menyeluruh
*   Integrasikan APScheduler untuk eksekusi tugas terjadwal dan hitung mundur.
*   Uji skenario menyeluruh: Input suara → Wellmy merespons dengan vokal anggun → Eksekusi tugas desktop → Autoclicker berjalan → Tombol panik menghentikan aksi seketika.