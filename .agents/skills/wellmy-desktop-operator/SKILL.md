---
name: wellmy-desktop-operator
description: Panduan dan instruksi operasional untuk mengembangkan, menguji, dan memelihara subsistem Wellmy-Ai Desktop Operator.
---

# Wellmy Desktop Operator Skill

Skill ini memandu AI agent (Antigravity) dalam mengimplementasikan, menguji, dan merawat subsistem **Wellmy-Ai ("Jarvis Core")**.

## Kapan Menggunakan Skill Ini
Gunakan skill ini saat mengimplementasikan atau merefaktor komponen:
1. Antarmuka Desktop PyQt6 (`gui/`) — **Wajib aktifkan skill `wellmy-ui-ux`**.
2. Dokumentasi & Devlog (`docs/`) — **Wajib aktifkan skill `wellmy-devlog`**.
3. Integrasi model Gemini dan function calling (`agent/brain.py`, `agent/tools/`).
4. Audio engine TTS WaveNet dan Gemini Live API (`agent/voice.py`).
5. Injeksi kepribadian otentik Wellmy Ernest (`agent/prompts/`).
6. Mekanisme keamanan failsafe dan autoclicker (`agent/safety.py`, `agent/tools/mouse_keyboard.py`).

## Protokol Wajib
1. **Verifikasi Kredensial (Rule 01):** Selalu gunakan `config.google_api_key.get_secret_value()` secara tertutup tanpa pernah mencetaknya.
2. **Penyelarasan Persona (Rule 02):** Pastikan respons teks dan suara mencerminkan kepribadian Wellmy Ernest di `agent/prompts/wellmy_ernest_instruction.md`.
3. **Desktop Actuation Safety (Rule 03):** Wajib cek flag `safety.is_aborted()`, `pyautogui.FAILSAFE = True`, dan thread isolation.
4. **Dokumentasi & Devlog (Rule 04):** Update `docs/progress.md`, tulis log di `docs/devlog/DEV-A.md`, dan ikuti conventional commits.
5. **Quality Gate Verifikasi (Rule 05):** Uji coba internal → checklist pengujian pengguna → konfirmasi eksplisit sebelum sprint berikutnya.
6. **Vibe Coding Desktop UI (Rule 06):** Wajib blok `<vibe_check>` sebelum menulis kode UI, ikuti 30 Anti-Slop Rules untuk Desktop.

## Daftar Skill Terkait
- [wellmy-ui-ux](../wellmy-ui-ux/SKILL.md) — Design system dark acrylic, tipografi, dan animasi PyQt6.
- [wellmy-devlog](../wellmy-devlog/SKILL.md) — Standar dokumentasi, format devlog, dan pencatatan ADR.
