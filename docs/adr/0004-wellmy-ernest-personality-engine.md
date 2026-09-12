# ADR-0004: Penegakan Kepribadian Otentik Wellmy Ernest via Dedicated Instruction

## Status
Diterima (Accepted)

## Konteks
Kepribadian asisten tidak boleh hanya sekadar prompt acak atau rekaan fantasi bebas yang menyimpang dari visi penciptanya. Pencipta asli (Wellmy Ernest) telah merumuskan instruksi kepribadian khusus (*persona instructions*) agar interaksi benar-benar mencerminkan karakter asli Wellmy Ernest yang anggun, berwibawa, berkarakter kuat, dan protektif.

## Keputusan
1. **Dedicated Instruction Repository File:**
   Instruksi persona disimpan dalam berkas khusus:
   `agent/prompts/wellmy_ernest_instruction.md`
   File ini berisi teks instruksi asli dari Wellmy Ernest tanpa modifikasi spekulatif dari pihak ketiga.
2. **Deterministic Prompt Compilation:**
   Saat modul `agent/prompts.py` mengompilasi system prompt untuk Gemini LLM, berkas `wellmy_ernest_instruction.md` akan dimuat dan disematkan langsung sebagai dasar karakter tak tergantikan.
3. **Guardrail Kepribadian:**
   Agen tidak diperkenankan mengganti kepribadian Wellmy dengan karakter lain secara sembarangan, kecuali pengguna memperbarui berkas instruksi resmi tersebut.
4. **Emotional Prosody Binding:**
   Parameter emosional suara TTS (WaveNet pitch dan rate) dikaitkan langsung dengan status kepribadian Wellmy untuk memastikan kesesuaian antara kata-kata dan intonasi suara.

## Konsekuensi
Karakter Wellmy tetap konsisten, otentik, dan persis seperti yang dirancang oleh Wellmy Ernest.
