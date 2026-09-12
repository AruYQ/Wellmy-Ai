---
name: wellmy-ui-ux
description: >
  Elite UI/UX design system dan coding standards untuk antarmuka desktop Wellmy-Ai
  (PyQt6 / QSS / Custom Widgets). WAJIB diaktifkan oleh AI agent sebelum membuat,
  memodifikasi, atau mereview file antarmuka (gui/). Menerapkan prinsip Vibe Coding,
  30 Anti-Slop Rules untuk Desktop, dark acrylic styling, dan tipografi modern.
---

# Wellmy-Ai — Elite Desktop UI/UX Skill (Vibe Coding Mode: ENABLED)

Skill ini menetapkan standar desain visual antarmuka desktop (*Desktop GUI*) untuk Wellmy-Ai. 
Tujuan utamanya adalah menciptakan antarmuka tingkat *design agency* yang elegan, minimalis, dan berwibawa—menolak segala bentuk UI generik bawaan OS atau template AI pasaran.

---

## 🧠 Mandatory Pre-Coding Ritual: `<vibe_check>`

Sebelum menulis baris kode UI APAPUN di folder `gui/`, AI Agent **WAJIB** menyertakan blok `<vibe_check>`:

```text
<vibe_check>
Komponen/Widget  : [Nama file/widget, misal: gui/main_hud.py -> SpotlightBar]
Tujuan Pengguna  : [Apa yang ingin dirasakan/dilakukan user di layar ini]
Layout Strategy  : [Asimetris, floating acrylic, bento arrangement, dsb]
Color Tokens     : [Gunakan token dari gui/styles.py, BUKAN arbitrary hex]
Animation Plan   : [QPropertyAnimation: fade/slide/pulse, durasi ms, easing curve]
Typography       : [Space Grotesk untuk headings, Syne untuk display, JetBrains Mono untuk angka]
Anti-Slop Check  : [Aturan 30 anti-slop mana yang dijaga ketat pada komponen ini]
</vibe_check>
```

> ⛔ **Langkah ini NON-OPSIONAL. Tidak ada vibe_check = kode ditolak.**

---

## 🎨 Desktop Design System Tokens (`gui/styles.py`)

### 1. Palet Warna (Modern Dark Slate & Muted Indigo)

```python
# gui/styles.py — Token resmi antarmuka desktop
COLOR_TOKENS = {
    # Backgrounds — Dark Slate Elegan (BUKAN #000000 murni)
    "bg_base": "#0F1117",        # Dasar jendela HUD / overlay gelap
    "bg_surface": "#171B26",     # Permukaan card / input bar
    "bg_elevated": "#1E2333",    # Modal, popover menu tray, dropdown
    "bg_overlay": "#252A3D",     # State hover dan tombol terpilih

    # Brand Colors — Karakter Bangsawan Anggun
    "brand_primary": "#6B7FD7",   # Aksen utama, border aktif, spotlight glow
    "brand_secondary": "#4ECDC4", # Aksen kedua (status aman, normal)
    "brand_accent": "#F7B731",    # Aksen peringatan, countdown running

    # Status / Semantik
    "status_safe": "#4ECDC4",     # Hijau mint — idle & aman
    "status_listening": "#6B7FD7",# Indigo — mendengarkan suara user
    "status_thinking": "#A882DD", # Lavender — memproses penalaran LLM
    "status_executing": "#54A0FF",# Biru cerah — autoclicker / mouse aktif
    "status_panic": "#FF5252",    # Merah menyala — Kill-Switch dipicu!

    # Teks & Tipografi
    "text_primary": "#F0F2F8",   # Teks utama, judul, angka fokus
    "text_secondary": "#9BA3BE", # Subtitle, label slider, status
    "text_muted": "#5A6177",     # Placeholder, teks non-aktif
    "text_accent": "#6B7FD7",    # Highlight penting

    # Border & Dividers
    "border_subtle": "#252A3D",  # Border halus antar card
    "border_active": "#6B7FD7",  # Border glow saat widget fokus
    "border_panic": "#FF5252",   # Border menyala saat darurat
}
```

### 2. Tipografi Desktop

Gunakan font modern yang diunduh ke project atau sistem OS:
- **Display / Big Numbers (CPS & Timer):** `Syne`, 700 Bold
- **Headings & Command Input:** `Space Grotesk`, 600 SemiBold
- **Body & Subtitles:** `Space Grotesk`, 400 Regular
- **Coordinates & Logs:** `JetBrains Mono`, 500 Medium

### 3. Radius & Spacing System
- **Pills / Badges / Status Dots:** `border-radius: 999px`
- **Input Fields & Buttons:** `border-radius: 10px`
- **Cards & Sub-Panels:** `border-radius: 14px`
- **Main HUD Window Container:** `border-radius: 18px`

---

## 🏗️ Spesifikasi Komponen PyQt6 Premium

### 1. Floating Command Bar (Spotlight-Style HUD)
- **Flag Window:**
  ```python
  self.setWindowFlags(
      Qt.WindowType.FramelessWindowHint |
      Qt.WindowType.WindowStaysOnTopHint |
      Qt.WindowType.SubWindow
  )
  self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
  ```
- **Acrylic Dark Glass Effect:**
  Background menggunakan `rgba(15, 17, 23, 0.92)` dengan border `1px solid rgba(107, 127, 215, 0.25)` dan shadow ambient offset.
- **Status Pill Dinamis:**
  Badge kecil di samping input bar dengan animasi denyut (*pulse*) saat Wellmy sedang mendengarkan atau berbicara.

### 2. Waveform Visualizer Widget (`gui/waveform_widget.py`)
- Visualisasi amplitudo suara 7-bar audio visualizer menggunakan `QPainter` dan timer animasi 30 FPS.
- Warna bar bergradasi dari `#6B7FD7` (indigo) ke `#4ECDC4` (mint).
- Bar bergerak dinamis mengikuti level desibel audio saat Wellmy bersuara.

### 3. Autoclicker & Timer Dashboard
- **Slider Presisi:** Slider QSS kustom dengan groove berwarna gelap subtle dan thumb bulat beraksen cyan.
- **Real-Time Stat Display:** Angka CPS ditampilkan dengan font mono besar (`JetBrains Mono`, 28pt) sehingga mudah dibaca sepintas.
- **Coordinate Crosshair Button:** Tombol "Lock Target" yang mengubah kursor menjadi crosshair visual saat memilih titik klik.

### 4. Floating Panic Badge (`gui/panic_badge.py`)
- Widget melayang minimalis di pojok layar (diameter 24px).
- Warna hijau tenang (`#4ECDC4`) saat status normal.
- Berkedip merah cepat (`#FF5252`) dengan getaran mikro saat pintasan `Ctrl + Shift + Q` dipicu.

---

## ⚡ Animasi Desktop PyQt6 (`QPropertyAnimation`)

Gunakan animasi mikro untuk menghidupkan antarmuka:

```python
# Contoh animasi Smooth Fade-in saat HUD muncul
def animate_show(widget):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(220)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    return anim
```

---

## 🚫 30 Anti-Slop Rules Checklist

Saat merancang file UI apapun, pastikan:
1. Tidak ada tombol abu-abu default Windows 98/XP.
2. Tidak ada teks `#FFFFFF` murni yang menyilaukan mata (gunakan `#F0F2F8`).
3. Tidak ada emoji murahan di label; gunakan status badge rapi.
4. Tidak ada card simetris membosankan yang tidak bernapas.
5. Tidak ada operasi komputasi berat di GUI thread utama.
6. Tidak ada kode placeholder `// TODO`. Semua widget harus siap pakai dan dapat berinteraksi.
