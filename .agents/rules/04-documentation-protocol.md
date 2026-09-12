# Rule 04: Aturan Wajib Dokumentasi & Devlog

Aturan ini berlaku untuk SEMUA AI agent dan kontributor yang bekerja pada proyek **Wellmy-Ai**, tanpa terkecuali.

## 📌 Prosedur Wajib Setiap Task

1. **Sebelum Mulai Task**:
   - Buka `docs/progress.md`.
   - Tandai task terkait dengan status in-progress: `[/] [Nama Task]`.

2. **Saat Menjalankan & Menyelesaikan Task**:
   - Tulis entri log perkembangan di `docs/devlog/DEV-A.md` (mencakup perubahan komponen GUI, Core Brain, Voice, Tools, atau Keamanan).
   - Cantumkan: ringkasan perubahan, file yang disentuh, dan hasil verifikasi.

3. **Setelah Selesai**:
   - Update checklist di `docs/progress.md` menjadi selesai: `[x] [Nama Task]`.

4. **Keputusan Arsitektur Signifikan**:
   - Jika membuat keputusan teknis baru (library baru, perubahan arsitektur data/thread), buat berkas ADR baru di `docs/adr/XXXX-[nama-keputusan].md` dan perbarui indeks `docs/adr/README.md`.

5. **Konvensi Commit (Conventional Commits)**:
   - Format wajib: `<type>: <deskripsi>`
   - Pilihan type: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `style:`, `perf:`
