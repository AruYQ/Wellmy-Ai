# ADR-0001: Pemilihan PyQt6 sebagai Kerangka Desktop GUI

## Status
Diterima (Accepted)

## Konteks
Sistem membutuhkan antarmuka desktop modern yang mampu menampilkan:
1. Jendela *frameless*, transparan (*acrylic/dark glass*), dan selalu di atas (*always on top*).
2. Integrasi *system tray* agar aplikasi dapat berjalan di latar belakang secara hemat daya.
3. Komunikasi *multi-threading* yang aman dan tidak memblokir antarmuka pengguna saat menjalankan eksekusi klik presisi tinggi (autoclicker) atau pemanggilan API jaringan.

## Pilihan yang Dipertimbangkan
- **Tkinter:** Bawaan Python, namun memiliki batasan besar dalam dukungan efek visual modern, transparansi, dan estetika premium.
- **Electron / Tauri (Web-based):** Tampilan sangat fleksibel, namun overhead memori tinggi dan integrasi native OS (global hotkey, screen capture, mouse actuation) membutuhkan IPC bridge yang kompleks ke Python.
- **PyQt6 / PySide6:** Framework matang dengan performa C++ native, dukungan luas untuk `QThread`, sinyal dan slot (*signals & slots*), *frameless window*, dan *styling* CSS modern (QSS).

## Keputusan
Memilih **PyQt6** sebagai kerangka antarmuka utama.

## Konsekuensi
- **Positif:** Integrasi langsung dengan Python tanpa jembatan IPC terpisah; performa rendering sangat cepat; dukungan sinyal-slot memisahkan UI dan background threads secara aman.
- **Tantangan:** Perlu penanganan thread yang disiplin (`QThread` / `pyqtSignal`) agar operasi I/O dan loop klik tidak memicu *Not Responding* pada UI.
