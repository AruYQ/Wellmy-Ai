"""
<vibe_check>
Komponen/Widget  : gui/styles.py (QSS Design System & Color Tokens)
Tujuan Pengguna  : Menghadirkan atmosfer visual desktop gelap berkelas (dark acrylic), tanpa gaya kuno Windows
Layout Strategy  : Token terpusat, QSS hierarkis dengan micro-interactions & ambient glow
Color Tokens     : bg_base (#0F1117), bg_surface (#171B26), brand_primary (#6B7FD7), mint (#4ECDC4)
Animation Plan   : Micro-scale hover, border transitions, smooth glow on focus
Typography       : Space Grotesk, Syne, JetBrains Mono
Anti-Slop Check  : Lolos 30 anti-slop rules (no harsh gradients, no white #FFF, no default widgets)
</vibe_check>

Wellmy-Ai Desktop Design System & QSS Themes
Menerapkan Vibe Coding dan 30 Anti-Slop Rules untuk Desktop (Rule 06).
"""

# ==============================================================================
# 1. COLOR TOKENS (Modern Dark Slate & Muted Indigo)
# ==============================================================================
TOKENS = {
    # Surfaces & Backgrounds (BUKAN #000000 murni)
    "bg_base": "#0F1117",
    "bg_surface": "#171B26",
    "bg_elevated": "#1E2333",
    "bg_overlay": "#252A3D",
    "bg_translucent": "rgba(15, 17, 23, 0.92)",
    "bg_card_translucent": "rgba(23, 27, 38, 0.88)",

    # Brand Accent Palette
    "brand_primary": "#6B7FD7",
    "brand_primary_hover": "#8294E6",
    "brand_secondary": "#4ECDC4",
    "brand_secondary_hover": "#65DDD5",
    "brand_accent": "#F7B731",

    # Semantic Status
    "status_safe": "#4ECDC4",
    "status_listening": "#6B7FD7",
    "status_thinking": "#A882DD",
    "status_executing": "#54A0FF",
    "status_panic": "#FF5252",
    "status_panic_bg": "rgba(255, 82, 82, 0.15)",

    # Text Hierarchy (BUKAN #FFFFFF murni)
    "text_primary": "#F0F2F8",
    "text_secondary": "#9BA3BE",
    "text_muted": "#5A6177",
    "text_inverse": "#0F1117",

    # Borders & Separators
    "border_subtle": "rgba(46, 52, 80, 0.6)",
    "border_active": "rgba(107, 127, 215, 0.7)",
    "border_panic": "rgba(255, 82, 82, 0.8)",

    # Shadows & Glow
    "glow_primary": "rgba(107, 127, 215, 0.25)",
    "glow_panic": "rgba(255, 82, 82, 0.35)",
}

# ==============================================================================
# 2. GLOBAL QSS STYLESHEET (Anti-Slop Desktop UI)
# ==============================================================================
GLOBAL_STYLESHEET = f"""
/* Global Reset & Base Typography */
QWidget {{
    font-family: 'Space Grotesk', 'Segoe UI', -apple-system, sans-serif;
    color: {TOKENS["text_primary"]};
    outline: none;
}}

/* Tooltips */
QToolTip {{
    background-color: {TOKENS["bg_elevated"]};
    color: {TOKENS["text_primary"]};
    border: 1px solid {TOKENS["border_subtle"]};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
}}

/* Main Floating HUD Container */
#MainHUDContainer {{
    background-color: {TOKENS["bg_translucent"]};
    border: 1px solid {TOKENS["border_subtle"]};
    border-radius: 18px;
}}

#MainHUDContainer:hover {{
    border: 1px solid {TOKENS["border_active"]};
}}

/* Spotlight Command Line Input */
#CommandInput {{
    background: transparent;
    border: none;
    font-size: 15px;
    font-weight: 500;
    color: {TOKENS["text_primary"]};
    padding: 8px 12px;
}}

#CommandInput::placeholder {{
    color: {TOKENS["text_muted"]};
    font-weight: 400;
}}

/* Interactive Icon Buttons */
QPushButton.IconButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px;
    min-width: 32px;
    min-height: 32px;
}}

QPushButton.IconButton:hover {{
    background-color: {TOKENS["bg_overlay"]};
    border: 1px solid {TOKENS["border_active"]};
}}

QPushButton.IconButton:pressed {{
    background-color: {TOKENS["brand_primary"]};
    color: {TOKENS["text_inverse"]};
}}

/* Action Primary Button */
QPushButton.PrimaryButton {{
    background-color: {TOKENS["brand_primary"]};
    color: {TOKENS["text_primary"]};
    border: 1px solid {TOKENS["brand_primary_hover"]};
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton.PrimaryButton:hover {{
    background-color: {TOKENS["brand_primary_hover"]};
}}

QPushButton.PrimaryButton:pressed {{
    background-color: {TOKENS["bg_overlay"]};
}}

/* Stop / Panic Button */
QPushButton.DangerButton {{
    background-color: {TOKENS["status_panic_bg"]};
    color: {TOKENS["status_panic"]};
    border: 1px solid {TOKENS["border_panic"]};
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton.DangerButton:hover {{
    background-color: {TOKENS["status_panic"]};
    color: {TOKENS["text_primary"]};
}}

/* Card Container (Bento Style) */
QFrame.BentoCard {{
    background-color: {TOKENS["bg_card_translucent"]};
    border: 1px solid {TOKENS["border_subtle"]};
    border-radius: 14px;
    padding: 12px;
}}

/* Custom Slider (CPS Slider) */
QSlider::groove:horizontal {{
    height: 6px;
    background: {TOKENS["bg_overlay"]};
    border-radius: 3px;
}}

QSlider::sub-page:horizontal {{
    background: {TOKENS["brand_primary"]};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {TOKENS["text_primary"]};
    border: 2px solid {TOKENS["brand_primary"]};
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background: {TOKENS["brand_secondary"]};
    border-color: {TOKENS["brand_secondary_hover"]};
}}

/* Big Display Numbers (CPS & Timers) */
QLabel.DisplayNumber {{
    font-family: 'JetBrains Mono', 'Syne', monospace;
    font-size: 26px;
    font-weight: 700;
    color: {TOKENS["brand_secondary"]};
}}

/* Status Badge Pill */
QLabel.StatusPill {{
    background-color: {TOKENS["bg_overlay"]};
    border: 1px solid {TOKENS["border_subtle"]};
    border-radius: 12px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
}}

/* Context Menu / System Tray Menu */
QMenu {{
    background-color: {TOKENS["bg_elevated"]};
    border: 1px solid {TOKENS["border_subtle"]};
    border-radius: 10px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 6px;
    font-size: 13px;
    color: {TOKENS["text_primary"]};
}}

QMenu::item:selected {{
    background-color: {TOKENS["bg_overlay"]};
    color: {TOKENS["brand_primary_hover"]};
}}

QMenu::separator {{
    height: 1px;
    background: {TOKENS["border_subtle"]};
    margin: 4px 6px;
}}
"""
