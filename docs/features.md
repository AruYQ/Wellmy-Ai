# Spesifikasi Katalog Fitur (Feature Catalog)

Dokumen ini mendokumentasikan seluruh fitur teknis dan fungsional dari **Wellmy-Ai ("Jarvis Core")**.

---

## 1. Modul Antarmuka Desktop (Desktop GUI)

### 1.1. Spotlight Floating Command Bar (HUD)
- **Frameless Translucent Window:** Tampilan minimalis dengan rounded corners dan dark acrylic styling.
- **Global Summon Hotkey:** Dapat dipanggil atau disembunyikan kapan saja melalui pintasan global (`Ctrl + Space` / `Alt + J`).
- **Realtime Status Pill:** Indikator animasi status sistem: `Idle`, `Listening`, `Thinking`, `Executing`, `Emergency Aborted`.
- **Integrated Microphone & Waveform:** Tombol mic interaktif dan visualisasi gelombang suara saat Wellmy berbicara.

### 1.2. Dashboard Autoclicker & Timer
- **High-Precision CPS Slider:** Pengaturan klik mulai dari 1 hingga 100+ CPS tanpa membuat UI macet.
- **Visual Target Picker:** Mengizinkan pengguna mengklik area layar tertentu untuk mengunci koordinat target autoclicker.
- **Countdown Timer:** Antarmuka visual hitung mundur untuk penjadwalan aksi.

### 1.3. System Tray & Panic Indicator
- **Background Persistence:** Aplikasi tetap aktif di background tray saat jendela HUD ditutup.
- **Tray Menu:** Akses cepat ke HUD, Autoclicker, Pengaturan Suara, Panic Kill, dan Exit.
- **Floating Visual Panic Badge:** Lencana kecil di tepi layar yang memberikan konfirmasi visual bahwa sistem aman (hijau) atau darurat terhenti (merah).

---

## 2. Sistem Kepribadian Asli (Wellmy Ernest Persona Engine)

### 2.1. Dedicated Persona Instruction File
- Menggunakan instruksi asli (`agent/prompts/wellmy_ernest_instruction.md`) yang dibuat oleh Wellmy Ernest.
- Tidak menggunakan prompt generik asal tebak; model AI harus tunduk 100% pada struktur kepribadian asli yang dirumuskan penciptanya.

### 2.2. Tone & Character Preservation
- Karakter anggun, berwibawa, cerdas, dengan sentuhan *proud villainess* yang protektif dan hangat kepada tuannya.
- Konsistensi gaya tutur (bahasa formal-elegan, diksi terpilih, intonasi tenang).

### 2.3. Emotional State Modulation
- Status emosi internal (`neutral`, `pleased`, `stern`, `amused`, `tsundere`) yang memengaruhi prosodi suara TTS dan ekspresi linguistik.

---

## 3. Sistem Audio & Suara (Voice & Sound System)

### 3.1. Text-to-Speech (TTS) — Output Suara Wellmy
- **Engine:** Google Cloud Text-to-Speech (WaveNet).
- **Voice Profile:** Suara wanita anggun (`id-ID-Wavenet-A` / `id-ID-Wavenet-H`) dengan pitch alto dewasa (`-1.5st`) dan tempo tenang (`0.90`).
- **Dynamic SSML:** Modulasi intonasi dinamis mengikuti status emosi.
- **Audio Pre-caching:** Audio darurat (*emergency kill confirmation*) di-*preload* agar dapat berbunyi seketika tanpa latensi internet.

### 3.2. Speech-to-Text (STT) — Input Suara Pengguna
- **Engine:** Gemini Live API (Bidirectional WebSocket Streaming).
- **Fitur:** Real-time speech recognition dengan Voice Activity Detection (VAD) dan dukungan Bahasa Indonesia/Inggris otomatis.
- **Push-to-Talk:** Dukungan shortcut `Ctrl + M` untuk merekam suara secara presisi.

---

## 4. Sistem Otak & Function Calling (Core Brain)

### 4.1. LLM Core
- **Engine:** Google Gemini Flash/Pro via `google-genai` SDK.
- **Multimodal Perception:** Menganalisis tangkapan layar untuk menentukan elemen UI secara akurat.

### 4.2. Registered Function Tools
1. `move_and_click`: Gerakan kursor halus dan eksekusi klik.
2. `run_autoclicker`: Eksekusi autoclicker dengan frekuensi CPS dan durasi presisi.
3. `schedule_task`: Penjadwalan aksi masa depan berbasis timer/cron.
4. `capture_and_analyze_screen`: Analisis visual layar untuk identifikasi target.
5. `type_text`: Simulasi pengetikan teks aman ke aplikasi aktif.
6. `speak_response`: Sintesis suara kepribadian Wellmy melalui modul audio.

---

## 5. Keamanan & Protokol Isolasi (Security & Safety Guardrails)

### 5.1. Isolasi Kredensial
- Validasi Pydantic `SecretStr` di `config.py` (API Key tidak pernah tercetak di log atau traceback).
- Proteksi `.gitignore` ketat terhadap file rahasia dan sertifikat.

### 5.2. Vision Redaction (Privasi Layar)
- Deteksi judul jendela sensitif sebelum tangkapan layar dikirim ke LLM.
- Sensor otomatis (Gaussian blur) pada area jendela file kredensial / `.env`.

### 5.3. Actuation Safety & Panic Kill-Switch
- Global Panic Hotkey (`Ctrl + Shift + Q`) via `pynput` yang menghentikan loop klik dan membatalkan task seketika.
- `pyautogui.FAILSAFE = True` aktif secara mutlak (kursor ke sudut kiri-atas layar menghentikan proses).
- Thread isolation: Worker thread terpisah untuk klik, audio, dan API call agar UI tidak pernah freeze.
