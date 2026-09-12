---
name: wellmy-devlog
description: >
  Skill wajib untuk siklus dokumentasi dan pencatatan devlog pada proyek Wellmy-Ai.
  AI Agent HARUS mengupdate devlog harian (DEV-A.md), progress tracker (progress.md),
  dan Architecture Decision Records (docs/adr/) setiap kali menyelesaikan task atau
  mengambil keputusan teknis besar.
---

# Wellmy-Ai — Documentation & Devlog Skill

> **"Dokumentasi adalah bagian mutlak dari Definition of Done. Kode tanpa dokumentasi dan pengujian = kode yang belum selesai."**

---

## 🔴 Aturan Wajib (Non-Negotiable)

AI Agent **HARUS** menjalankan urutan dokumentasi ini setiap kali mengeksekusi task:

1. **Sebelum Mulai:** Buka `docs/progress.md` dan ubah status task dari `[ ]` menjadi `[/]` (in progress).
2. **Saat Menjalankan:** Tulis entri log terstruktur di `docs/devlog/DEV-A.md`.
3. **Setelah Selesai & Lolos Verifikasi:** Ubah status di `docs/progress.md` menjadi `[x]`.
4. **Keputusan Arsitektur:** Jika memilih library baru, mengubah struktur thread, atau menambah tool LLM, buat berkas ADR baru di `docs/adr/XXXX-[judul].md`.
5. **Commit Message:** Wajib mematuhi konvensi *Conventional Commits*.

---

## 📁 Struktur Dokumen Utama

```
docs/
├── progress.md          ← Pelacak status sprint, milestone & roadmap
├── features.md          ← Katalog spesifikasi fitur fungsional & teknis
├── devlog/
│   ├── README.md        ← Indeks devlog
│   └── DEV-A.md         ← Jurnal aktivitas harian teknis (Wellmy-Ai Core)
└── adr/
    ├── README.md        ← Indeks keputusan arsitektur
    ├── 0001-gui-framework-pyqt6.md
    ├── 0002-gemini-live-and-tts-wavenet.md
    ├── 0003-security-and-credential-isolation.md
    └── 0004-wellmy-ernest-personality-engine.md
```

---

## 📝 Format Entri Devlog (`docs/devlog/DEV-A.md`)

Setiap kali menyelesaikan task atau checkpoint sprint, tambahkan entri dengan template berikut:

```markdown
### [YYYY-MM-DD] — [Judul Task / Fitur]

**Sprint**: Sprint X ([Nama Sprint])
**Komponen**: GUI | Brain / Tools | Voice / TTS | Safety | Scheduler
**Status**: Selesai | Sedang Dikerjakan | Terblokir

**Rincian yang Dikerjakan:**
- Item konkret yang diselesaikan
- Optimasi yang dilakukan

**Berkas yang Dibuat / Dimodifikasi:**
- `gui/[NamaFile].py` — deskripsi perubahan
- `agent/[NamaFile].py` — deskripsi perubahan

**Vibe Check & Safety Check:**
- UI/UX Anti-Slop: [Lolos / Tidak ada pelanggaran]
- Credential Safety: [Tidak ada eksposur secret / Pydantic SecretStr aman]
- Actuation Safety: [Failsafe PyAutoGUI & Panic Hotkey terverifikasi aktif]

**Masalah & Solusi:**
- [Kendala yang dihadapi] → [Solusi teknis yang diterapkan]

**Hasil Uji Coba & Verifikasi:**
- [Perintah uji, exit code, dan respon fisik/audio sistem]
```

---

## 📊 Format Pemutakhiran `docs/progress.md`

```markdown
# Sebelum mulai:
- [ ] Implementasi modul voice WaveNet

# Saat pengerjaan:
- [/] Implementasi modul voice WaveNet (Sedang merancang SSML emotion mapping)

# Setelah teruji lolos quality gate:
- [x] Implementasi modul voice WaveNet (Tuntas & audio playback terverifikasi lancar)
```

---

## ⚡ Standar Pesan Commit (Conventional Commits)

Semua pesan commit **WAJIB** menggunakan format:

```text
<type>: <deskripsi singkat imperative>

[body opsional — penjelasan mendalam jika diperlukan]
```

| Type | Kapan Digunakan |
|---|---|
| `feat` | Fitur baru (misal: penambahan tool autoclicker, widget HUD baru) |
| `fix` | Perbaikan bug atau penanganan error |
| `docs` | Perubahan dokumentasi, ADR, progress, atau devlog |
| `refactor` | Restrukturisasi kode tanpa mengubah fungsionalitas |
| `style` | Perubahan QSS / visual tanpa mengubah logika bisnis |
| `perf` | Optimasi performa (misal: pengurangan latensi screen capture `mss`) |
| `test` | Menambah atau memperbaiki pengujian otomatis / dry-run |
| `chore` | Konfigurasi, requirements.txt, .gitignore |

---

## 🔄 Alur Siklus Kerja Lengkap (Task Lifecycle)

```
[Mulai Task]
    ↓
1. Update docs/progress.md: [ ] → [/]
    ↓
2. Lakukan <vibe_check> (jika task UI) atau Safety Check (jika task Actuation/Brain)
    ↓
3. Tulis kode implementasi (100% lengkap, no placeholders)
    ↓
4. Jalankan verifikasi internal (syntax test, linting, thread test)
    ↓
5. Catat entri baru di docs/devlog/DEV-A.md
    ↓
6. Jalankan Gerbang Verifikasi User (Quality Gate)
    ↓
7. Jika ada keputusan arsitektur baru → Tambahkan ADR di docs/adr/
    ↓
8. Update docs/progress.md: [/] → [x]
    ↓
[Selesai — Siap ke Task Berikutnya]
```
