# Rule 05: Aturan Pengujian Fitur & Gerbang Verifikasi (Quality Gate)

Aturan ini **WAJIB dan NON-NEGOTIABLE** untuk seluruh pengembang dan AI Agent yang bekerja pada repositori Wellmy-Ai.

> ⛔ **GOLDEN RULE: TIDAK ADA VERIFIKASI = TIDAK ADA SPRINT/PHASE BERIKUTNYA.**
> Dilarang keras memulai perencanaan atau coding untuk sprint berikutnya sebelum seluruh fitur pada sprint aktif diuji dan dikonfirmasi aman oleh pengguna.

---

## 🎯 Cakupan Pengujian Wajib

1. **Fitur Baru (New Features):** Komponen GUI baru, skema tool Gemini baru, fungsionalitas audio TTS/STT baru, atau modul scheduler.
2. **Fitur Terdampak (Regression Testing):** Memastikan integrasi baru tidak merusak thread safety, mekanisme tombol panik darurat, latensi audio, atau stabilitas antarmuka PyQt6.

---

## 🔄 Prosedur Wajib Pengujian (Step-by-Step)

```text
[Coding Fitur Selesai]
        ↓
1. Verifikasi Internal Otomatis (Syntax check / linting / dry-run test)
        ↓
2. Susun Panduan & Checklist Skenario Uji Coba untuk Pengguna
        ↓
3. Minta Konfirmasi Eksplisit dari Pengguna (Blocking Step)
        ↓
   Apakah ditemukan kendala/bug?
    ├── YA  ──> Dilarang lanjut! Perbaiki langsung & ulangi pengetesan
    └── TDK ──> Update docs/progress.md & docs/devlog/ ──> Izin lanjut ke Sprint berikutnya
```

### Langkah 1: Verifikasi Internal (Oleh Agent)
Sebelum menyerahkan ke pengguna, AI Agent wajib memastikan:
- Seluruh berkas Python bebas dari syntax error (`python -m py_compile [file]`).
- GUI tidak mengalami deadlock atau freeze saat worker thread berjalan.
- Kredensial tidak bocor di output terminal.

### Langkah 2: Penyusunan Panduan Uji Coba Pengguna
Agent harus menyajikan skenario pengujian konkret:
- Perintah eksekusi (`python app.py`).
- Tindakan yang harus dilakukan (klik tombol mic HUD, ketik instruksi, geser slider CPS, dsb).
- Respon yang diharapkan (*Expected Behavior*), termasuk output suara Wellmy dan pergerakan mouse.
- Pengujian darurat tombol panik (`Ctrl + Shift + Q`).

### Langkah 3: Minta Konfirmasi Pengguna (Blocking Prompt)
Agent **WAJIB BERHENTI** dan menanyakan konfirmasi kepada pengguna:
> *"Apakah seluruh skenario pengujian di atas sudah dicoba dan berjalan lancar di layar Anda?"*

### Langkah 4: Penanganan Hasil
- **Jika Pengguna Menemukan Kendala / Bug**:
  - Agent **DILARANG** menutup task atau berpindah topik.
  - Agent wajib langsung menganalisis akar masalah, memperbaiki kode, dan meminta pengguna mengetes ulang hingga tuntas.
- **Jika Pengguna Mengonfirmasi Aman (Lolos)**:
  - Tandai checklist verifikasi di `docs/progress.md` menjadi `[x]`.
  - Catat hasil pengujian di devlog (`docs/devlog/DEV-A.md`).
  - Barulah agent diizinkan menawarkan atau memulai sprint berikutnya.

---

## 📋 Format Template Permintaan Verifikasi ke Pengguna

Setiap kali menyelesaikan checkpoint sprint, agent wajib menyertakan blok verifikasi berikut:

```markdown
### 🧪 Gerbang Verifikasi Fitur (Quality Gate — Sprint X)

Silakan uji coba skenario berikut di perangkat Anda:
1. [Skenario 1]: [Langkah uji] ➔ Ekspektasi: [Hasil yang diharapkan]
2. [Skenario 2]: [Langkah uji] ➔ Ekspektasi: [Hasil yang diharapkan]
3. [Safety Test]: [Tekan Ctrl + Shift + Q] ➔ Ekspektasi: [Sistem berhenti seketika & badge merah]

⚠️ **Konfirmasi Diperlukan:**
Mohon beritahu saya apakah semua skenario di atas berhasil tanpa kendala?
- Jika ada kendala/error, sebutkan dan akan langsung saya perbaiki sekarang.
- Jika sudah aman, kita baru akan melangkah ke fase berikutnya.
```
