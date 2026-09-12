# Rule 03: Desktop Actuation & System Safety Protocols

Aturan ketat untuk seluruh operasi kontrol kursor, pengetikan, dan eksekusi sistem.

## 1. Thread Isolation Mutlak
1. Segala aktivitas yang memakan waktu (autoclicker loop, Gemini API network calls, TTS audio synthesis & playback, screen capture) **HARUS** dijalankan di dalam worker thread (`QThread` atau `threading.Thread`).
2. GUI thread (`PyQt6`) tidak boleh diblokir (*freeze/not responding*) dalam kondisi apa pun.

## 2. Global Panic Hotkey & Emergency Stop
1. Listener `pynput` untuk tombol darurat (default: `Ctrl + Shift + Q`) wajib aktif sejak aplikasi dijalankan.
2. Ketika pemicu panik aktif:
   - Sinyal pembatalan `threading.Event().set()` langsung ditembakkan.
   - Loop autoclicker berhenti dalam kurun waktu `<10ms`.
   - Seluruh antrean tugas APScheduler dibatalkan.
   - Audio pemutaran suara dihentikan seketika.
   - Audio konfirmasi darurat lokal disuarakan.

## 3. PyAutoGUI FailSafe
1. Baris kode `pyautogui.FAILSAFE = True` wajib diinisialisasi di baris pertama modul input mouse/keyboard.
2. Mekanisme pergerakan mouse ke sudut layar kiri-atas tidak boleh dinonaktifkan.
