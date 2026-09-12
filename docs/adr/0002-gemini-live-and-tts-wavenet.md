# ADR-0002: Arsitektur Audio: Gemini Live API & Google Cloud TTS WaveNet

## Status
Diterima (Accepted)

## Konteks
Sistem asisten desktop otonom membutuhkan kemampuan dua arah:
1. **Mendengarkan instruksi suara pengguna (STT/NLU)** secara lancar, responsif, dan bebas jeda canggung (*conversational latency*).
2. **Menyuarakan tanggapan AI (TTS)** dengan karakter suara wanita yang sangat anggun, melodis, elegan, dan mencerminkan persona bangsawan (*noblewoman/princess*).

## Keputusan
1. **Input Suara (STT):** Menggunakan **Gemini Live API** berbasis streaming WebSocket dua arah, dilengkapi *Voice Activity Detection* (VAD).
2. **Output Suara (TTS):** Menggunakan **Google Cloud Text-to-Speech (WaveNet)** dengan konfigurasi suara wanita Bahasa Indonesia (`id-ID-Wavenet-A` / `id-ID-Wavenet-H`), dimodifikasi dengan parameter:
   - Speaking Rate: `0.90` (tenang, anggun)
   - Pitch: `-1.5st` (alto berwibawa)
   - Dukungan SSML untuk modulasi ekspresi emosi dinamis.
3. **Safety Fallback:** Menyimpan *pre-cached audio byte* lokal untuk pesan darurat (*emergency abort confirmation*) agar tidak bergantung pada koneksi internet ketika tombol panik ditekan.

## Konsekuensi
- Pengguna mendapatkan pengalaman percakapan audio real-time.
- Kuota gratis 1 juta karakter per bulan untuk WaveNet sangat mencukupi kebutuhan penggunaan personal.
