# Rule 06: Vibe Coding & Anti-Slop Desktop UI/UX Standards

Aturan ini **WAJIB dan NON-NEGOTIABLE** untuk seluruh pengembang dan AI Agent yang merancang atau memodifikasi antarmuka pengguna (`gui/`) pada proyek **Wellmy-Ai ("Jarvis Core")**.

Tujuan: Menolak template AI murahan (*anti-slop*), menjamin estetika setingkat agency premium, frameless dark acrylic, dan responsif tingkat tinggi di lingkungan Desktop OS (PyQt6).

---

## 🧠 Mandatory Pre-Coding Ritual: `<vibe_check>`

Sebelum menulis atau mengubah baris kode UI/QSS APAPUN, AI Agent **WAJIB** menyertakan blok perencanaan `<vibe_check>`:

```text
<vibe_check>
Komponen/Jendela : [nama file/widget, misal: gui/main_hud.py]
Tujuan Visual    : [kesan apa yang ingin dihadirkan untuk pengguna]
Layout Strategy  : [susunan elemen — asimetris/bento, bukan card simetris pasaran]
Color Tokens     : [palet terkurasi, misal: dark slate #0F1117, indigo #6B7FD7]
Animation Plan   : [animasi apa yang dipakai, QPropertyAnimation / opacity / slide]
Typography       : [font display / body / mono untuk angka koordinat]
Anti-Slop Check  : [aturan anti-slop mana yang dijaga ketat di sini]
</vibe_check>
```

> ⛔ **TIDAK ADA VIBE_CHECK = TIDAK BOLEH MENULIS KODE UI.**

---

## 🚫 30 Anti-Slop Rules untuk Desktop AI Operator

| # | Aturan Anti-Slop | Penerapan pada PyQt6 Desktop GUI |
|---|---|---|
| 1 | **No harsh linear gradients** | Gunakan solid surface bertingkat atau subtle ambient gradient 2-stop. |
| 2 | **No default Windows/Qt widgets** | Wajib QSS kustom: border-radius, background translucent, custom hover. |
| 3 | **No pure white `#FFFFFF` / pure black `#000`** | Gunakan `bg.base: #0F1117`, surface `#171B26`, elevated `#1E2333`. |
| 4 | **No rainbow coloring** | Maksimal 2–3 warna aksen: Muted Indigo (`#6B7FD7`) + Mint/Teal (`#4ECDC4`). |
| 5 | **No default rectangular system frames** | Jendela HUD wajib *frameless* (`Qt.WindowType.FramelessWindowHint`) berujung melengkung. |
| 6 | **No symmetric 3-column cards** | Gunakan layout Bento modular atau split-panel asimetris. |
| 7 | **No emoji sebagai status/label (🚀✨🔥)** | Gunakan lencana status geometris (*badge pill*) atau monogram icon. |
| 8 | **No liquid glassmorphism berlebihan** | Gunakan dark acrylic halus (`rgba(23, 27, 38, 0.85)` + subtle border). |
| 9 | **No em dashes (—) di tagline** | Tulis copy ringkas, percaya diri, dan berwibawa khas Wellmy. |
| 10 | **No standard system fonts (Arial/Calibri/Segoe)** | Gunakan *Space Grotesk*, *Syne*, dan *JetBrains Mono* (angka CPS/koordinat). |
| 11 | **No colored left-stripe border cards** | Gunakan full-card border tint subtle atau background hover highlight. |
| 12 | **No fake mock data statis** | Tampilkan state nyata dari koordinat layar dan CPS aktif. |
| 13 | **No terminal window mockup murahan** | Buat floating spotlight HUD yang elegan, bukan tiruan terminal Mac. |
| 14 | **No ActivityIndicator/spinner statis** | Gunakan pulse wave animasi atau status pill dinamis. |
| 15 | **No checkmark bullet lists generik** | Gunakan list item berventilasi dengan metadata terstruktur. |
| 16 | **No radius yang sama untuk semua elemen** | Variasikan: pills `999px`, cards `12px`, HUD container `16–20px`. |
| 17 | **No standard purple-black linear clone** | Gunakan slate-indigo dengan aksen cyan elegan. |
| 18 | **No particle effects / glitter random** | Efek animasi harus fungsional (misal: audio waveform bergetar saat bicara). |
| 19 | **No looping idle animations berat** | Idle state tenang; animasi hanya aktif saat ada event (bicara, eksekusi). |
| 20 | **No blocking UI on animation** | Gunakan `QPropertyAnimation` non-blocking terisolasi dari worker threads. |
| 21 | **No generic push buttons default** | Button interaktif dengan state hover: `rgba(107, 127, 215, 0.15)` + micro-scale. |
| 22 | **No low-contrast colors** | Wajib lolos rasio kontras WCAG AA (teks utama `#F0F2F8` di atas `#171B26`). |
| 23 | **No unaligned typography hierarchy** | Hierarki jelas: Display (24pt) > Heading (16pt) > Body (13pt) > Meta (11pt). |
| 24 | **No missing tooltips on action buttons** | Tombol ikon tanpa teks wajib memiliki tooltip informatif. |
| 25 | **No sudden layout shift (CLS)** | Dimensi HUD dan dashboard stabil; transisi panel menggunakan animasi fade/expand halus. |
| 26 | **No generic slider bars** | Slider CPS custom: track berwarna gelap halus, groove beraksen cyan, thumb elegan. |
| 27 | **No missing empty state** | Jika belum ada tugas terjadwal, tampilkan pesan berwibawa khas Wellmy. |
| 28 | **No intrusive notifications** | Notifikasi system tray tenang, tidak mengganggu fokus pengguna. |
| 29 | **No raw hex hardcoded in widgets** | Semua warna wajib mengacu pada token `gui/styles.py`. |
| 30 | **No half-baked placeholders** | Dilarang menulis komentar `// TODO nanti buat di sini`. Kode UI harus 100% fungsional. |
