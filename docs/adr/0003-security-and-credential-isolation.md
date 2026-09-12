# ADR-0003: Protokol Isolasi Kredensial, Anti-Leak & Safety Kill-Switch

## Status
Diterima (Accepted)

## Konteks
Sebagai perangkat lunak open-source yang memiliki akses manipulasi OS fisik (kursor, keyboard, layar), risiko keamanan sangat nyata:
1. Kemungkinan kebocoran API Key ke Git repo atau tangkapan layar.
2. Kerusakan sistem akibat loop tak terkontrol pada autoclicker atau eksekusi perintah liar.
3. Eksfiltrasi kredensial melalui pengetikan otomatis atau prompt injection.

## Keputusan
1. **Enkapsulasi Kredensial:** Menggunakan `pydantic-settings` dengan tipe `SecretStr` di `config.py`. Nilai rahasia tidak pernah ditampilkan pada `repr()`, `str()`, atau log traceback.
2. **Git Hygiene:** Aturan ketat `.gitignore` yang memblokir semua varian file `.env`, sertifikat, dan file kustom pribadi pengguna.
3. **Vision Redaction:** Pemeriksaan judul jendela aktif sebelum screenshot dikirim ke cloud. Jendela dengan kata kunci sensitif (`.env`, kredensial, token) otomatis diburamkan (*Gaussian blur*) atau digugurkan.
4. **Output Sanitization:** Fungsi pengetikan `type_text` menolak mengetik jika teks berisi nilai rahasia API Key.
5. **Failsafe Ganda:**
   - `pyautogui.FAILSAFE = True` (geser kursor ke pojok kiri-atas mematikan program).
   - Global Panic Hotkey (`Ctrl + Shift + Q`) melalui listener `pynput` yang memotong loop klik dan menghentikan seluruh aktivitas secara instan.

## Konsekuensi
Tingkat keamanan tinggi terjamin tanpa mengurangi kenyamanan operasional asisten.
