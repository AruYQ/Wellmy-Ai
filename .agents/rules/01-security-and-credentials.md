# Rule 01: Security, Secrets Isolation & Anti-Leak Protocols

Semua pengembang, kontributor, dan AI Development Agent (Antigravity) yang bekerja pada repositori Wellmy-Ai **WAJIB MEMATUHI ATURAN BERIKUT TANPA PENGECUALIAN**:

## 1. Penanganan Kredensial & Secrets
1. **Dilarang Keras Hardcode:** Jangan pernah menuliskan API Key, token, atau rahasia apa pun secara langsung di dalam kode sumber (`.py`), berkas dokumentasi (`.md`), maupun contoh skrip.
2. **Pydantic SecretStr:** Semua variabel sensitif dalam konfigurasi wajib dibungkus dengan `pydantic.SecretStr` dalam `config.py`.
3. **Penyembunyian Log:** Jangan pernah mencetak `config.google_api_key.get_secret_value()` ke dalam `print()`, `logger.info()`, `console.log`, maupun pesan error traceback.

## 2. Kebersihan Git & Repositori
1. Pastikan seluruh file `.env`, `.env.*` (kecuali `.env.example`), `custom_instructions.txt`, `*.key`, `*.cert`, dan `*.pem` selalu terdaftar di `.gitignore`.
2. Sebelum melakukan commit, selalu periksa `git status` dan `git diff` untuk memastikan tidak ada artefak lokal rahasia yang terbawa.

## 3. Vision Redaction & AI Privacy Guard
1. Setiap modul yang mengambil tangkapan layar (`agent/vision.py`) wajib memvalidasi judul jendela aktif sebelum citra dikirim ke cloud / Gemini Vision.
2. Area jendela yang terdeteksi memuat nama file `.env`, password manager, terminal berisi token, atau editor teks sensitif wajib diburamkan (*Gaussian blur*) atau ditolak pengirimannya.
3. **AI Privacy (PII Protection):** Jangan pernah mengirim data pribadi pengguna (kata sandi, nomor identitas, dokumen finansial) ke API LLM tanpa anonimisasi ketat.

## 4. Anti-Prompt Injection & Output Sanitization
1. System prompt wajib menginstruksikan model untuk menolak segala bentuk instruksi jahat (*prompt injection*) yang meminta pembacaan ulang kunci API atau bypass aturan keamanan.
2. Fungsi pengetikan otomatis (`agent/tools/mouse_keyboard.py` -> `type_text`) wajib memvalidasi teks target. Jika teks mengandung substring dari API Key rahasia, eksekusi pengetikan langsung dibatalkan sepihak.
