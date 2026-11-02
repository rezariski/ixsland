#!/usr/bin/env python3
"""
ixsland Authentic High-End Promo Video Generator (3:4 Ratio - 1080x1440 @ 30 FPS)
- Song: VOCE NA MIRA JUMPSTYLE - Slowed by Sxilwix (with real cover art)
- Continuous background music starting at 00:00:12 of the song
- Flat background music volume (0.18), with subtle ducking to 0.05 during notification
- Zoomed Dynamic Island (~1.85x) for massive, clear, phone-optimized focal viewing
- Cyber glitch transitions on bottom card text and prayer schedule
- Rich cyber HUD aesthetic: corner brackets, traveling neon borders, audio visualizer spectrum
- Seamless loop connection between ending frame and starting frame
- Clean pure OLED look without drop shadows
- Zero mention of 'DP-1'
"""

import sys
import os
import math
import subprocess
from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, QPointF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, QFont, QPixmap, QImage, QPainterPath
)

app = QApplication.instance() or QApplication(sys.argv)

WIDTH = 1080
HEIGHT = 1440
FPS = 30
TOTAL_FRAMES = 840  # 28.0 seconds

OUTPUT_VIDEO = "/home/reza/ixsland_promo_3x4.mp4"
THUMBNAIL_IMG = "/home/reza/ixsland_promo_thumbnail.png"
WALLPAPER_PATH = "/tmp/clean_sonoma_top.png"
SPOTIFY_ART_PATH = "/tmp/voce_art.jpg"
SPOTIFY_SONG_PATH = "/tmp/voce_na_mira.mp3"

wallpaper_pix = QPixmap(WALLPAPER_PATH) if os.path.exists(WALLPAPER_PATH) else None
spotify_art_pix = QPixmap(SPOTIFY_ART_PATH) if os.path.exists(SPOTIFY_ART_PATH) else None

# Island Zoom Factor
ISLAND_ZOOM = 1.85

# Easing Helpers
def ease_out_cubic(t):
    return 1.0 - math.pow(1.0 - max(0.0, min(1.0, t)), 3)

def ease_in_out_cubic(t):
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - math.pow(-2.0 * t + 2.0, 3) / 2.0

def ease_out_back(t, s=1.70158):
    t = max(0.0, min(1.0, t)) - 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0

def lerp(a, b, t):
    return a + (b - a) * t

# Scenes configuration (NO 'DP-1' anywhere!)
SCENES = [
    {
        "id": "MASCOT",
        "tab": "01 Mascot",
        "start": 0, "end": 140, # 0.0s - 4.6s
        "badge": "FEATURE 01 / 05",
        "title": "Interactive OLED Mascot",
        "sub": "Mascot vector reaktif terhadap pergerakan kursor di layar",
        "bullets": [
            ("Gaze Tracking Engine", "Mata OLED melirik posisi kursor secara matematis dan presisi."),
            ("Blinking & Hover Joy", "Mata berkedip natural dan tersenyum merona pink saat kursor mendekat."),
            ("Auto Sleep Engine", "Mascot otomatis tidur (zZ) saat kursor tidak bergerak.")
        ],
        "tags": ["Vector OLED", "Gaze Physics", "Pure PyQt6", "Zero Wine"]
    },
    {
        "id": "MEDIA",
        "tab": "02 Media",
        "start": 140, "end": 290, # 4.6s - 9.6s
        "badge": "FEATURE 02 / 05",
        "title": "Interactive Media Hub",
        "sub": "Kontrol musik real-time dengan cover art asli dan live seekbar",
        "bullets": [
            ("MPRIS Dual-Way Sync", "Membaca album art, judul lagu, dan live durasi detik otomatis Spotify."),
            ("Live Scrub & Seekbar", "Klik pada garis durasi untuk langsung melompat ke detik yang diinginkan."),
            ("Dancing Visual Equalizer", "Animasi bar frekuensi bergerak dinamis mengikuti status pemutaran.")
        ],
        "tags": ["D-Bus MPRIS", "Spotify / Brave", "Live Seekbar", "60 FPS Morph"]
    },
    {
        "id": "AUTOCLOSE",
        "tab": "03 Auto-Close",
        "start": 290, "end": 420, # 9.6s - 14.0s
        "badge": "FEATURE 03 / 05",
        "title": "Smart Auto-Collapse",
        "sub": "Penutupan otomatis tanpa perlu repot menekan tombol silang",
        "bullets": [
            ("Mouse Exit Detection", "Island ciut kembali ke compact saat kursor mouse meninggalkan area."),
            ("Debounce 120ms Guard", "Cegah penutupan tidak disengaja saat kursor sekadar melintas cepat."),
            ("Fixed Window Canvas", "Ukuran kanvas KWin tetap terkunci di posisi atas tanpa pergeseran.")
        ],
        "tags": ["KWin Rule", "Wayland Native", "Auto-Collapse", "Zero Lag"]
    },
    {
        "id": "VOLUME",
        "tab": "04 Volume",
        "start": 420, "end": 570, # 14.0s - 19.0s
        "badge": "FEATURE 04 / 05",
        "title": "Fluid PipeWire Volume OSD",
        "sub": "Animasi volume berseluncur halus dengan indikator over-boost",
        "bullets": [
            ("OutCubic Sliding Bar", "Animasi interpolasi 160ms membuat pergerakan bar terasa sangat fluid."),
            ("150% Boost Indicator", "Bar otomatis berubah dari Cyan ke Amber saat volume melebihi 100%."),
            ("Realtime Hardware Polling", "Mendeteksi tombol volume keyboard dan wheel mouse secara instan.")
        ],
        "tags": ["PipeWire wpctl", "OutCubic Easing", "Over-Boost 150%", "Hardware OSD"]
    },
    {
        "id": "NOTIF_PRAYER",
        "tab": "05 Alerts",
        "start": 570, "end": 710, # 19.0s - 23.6s
        "badge": "FEATURE 05 / 05",
        "title": "Smart Notif & Prayer Engine",
        "sub": "Pusat notifikasi desktop lokal dan kalkulasi jadwal sholat offline",
        "bullets": [
            ("Subuh s/d Isya Ticker", "Kalkulasi 5 waktu sholat berganti cepat dengan efek glitch presisi."),
            ("Instant Desktop Alerts", "Tampilan banner notifikasi pesan chat dan sistem yang rapi dan elegan."),
            ("Auto-Pause Music Player", "Musik otomatis jeda saat waktu sholat tiba untuk ketenangan ibadah.")
        ],
        "tags": ["Subuh s/d Isya", "Cyber Glitch", "Astronomical Math", "Smart Alerts"]
    },
    {
        "id": "CLOSING",
        "tab": "Open Source",
        "start": 710, "end": 840, # 23.6s - 28.0s
        "badge": "OPEN SOURCE PROJECT",
        "title": "ixsland for Linux Wayland",
        "sub": "Proyek open source siap pakai untuk desktop modern Linux Anda",
        "bullets": [
            ("Kunjungi Repositori", "github.com/rezariski/ixsland"),
            ("Setup Cepat & Ringan", "Cukup clone dan aktifkan via systemd user service."),
            ("Dukung Proyek Ini", "Beri bintang di GitHub dan bagikan ke komunitas Linux!")
        ],
        "tags": ["github.com/rezariski", "GPL-3.0", "Arch / CachyOS / KDE", "Made with PyQt6"]
    }
]

# 5 Prayer Times definition for the rapid cyber cycle
PRAYER_SCHEDULE = [
    ("SUBUH", "04:28 WIB"),
    ("DZUHUR", "11:42 WIB"),
    ("ASHAR", "14:58 WIB"),
    ("MAGHRIB", "17:52 WIB"),
    ("ISYA", "19:04 WIB")
]

def get_current_scene(frame):
    for sc in SCENES:
        if sc["start"] <= frame < sc["end"]:
            return sc
    return SCENES[-1]

def get_scene_index(frame):
    for idx, sc in enumerate(SCENES):
        if sc["start"] <= frame < sc["end"]:
            return idx
    return len(SCENES) - 1

def draw_virtual_cursor(p, x, y, click_ring_radius=0.0, click_ring_alpha=0):
    if click_ring_radius > 0 and click_ring_alpha > 0:
        p.save()
        p.setPen(QPen(QColor(0, 212, 255, click_ring_alpha), 2.0))
        p.setBrush(QBrush(QColor(0, 212, 255, click_ring_alpha // 3)))
        p.drawEllipse(QPointF(x, y), click_ring_radius, click_ring_radius)
        p.restore()

    # Subtle Cursor shadow
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(0, 0, 0, 150)))
    path_sh = QPainterPath()
    path_sh.moveTo(x + 2, y + 2)
    path_sh.lineTo(x + 2, y + 25)
    path_sh.lineTo(x + 8, y + 19)
    path_sh.lineTo(x + 14, y + 25)
    path_sh.lineTo(x + 19, y + 21)
    path_sh.lineTo(x + 13, y + 15)
    path_sh.lineTo(x + 19, y + 15)
    path_sh.closeSubpath()
    p.drawPath(path_sh)

    # Crisp White Vector Cursor
    p.setBrush(QBrush(QColor(255, 255, 255)))
    p.setPen(QPen(QColor(18, 18, 24), 1.6))
    path = QPainterPath()
    path.moveTo(x, y)
    path.lineTo(x, y + 23)
    path.lineTo(x + 6, y + 17)
    path.lineTo(x + 12, y + 23)
    path.lineTo(x + 17, y + 19)
    path.lineTo(x + 11, y + 13)
    path.lineTo(x + 17, y + 13)
    path.closeSubpath()
    p.drawPath(path)

def draw_native_pill(p, x, y, w, h, radius=None):
    """Clean Pure OLED Pill without blurry drop shadow behind it."""
    if radius is None:
        radius = h / 2.0

    # NO DROP SHADOW BEHIND PILL (Clean OLED aesthetic)
    # Pure OLED Glass Container with ultra-crisp border
    p.setPen(QPen(QColor(255, 255, 255, 45), 1.0))
    p.setBrush(QBrush(QColor(12, 13, 16, 252)))
    p.drawRoundedRect(QRectF(x, y, w, h), radius, radius)

# --- 1. ORGANIC OLED MASCOT WITH HIGH-PRECISION GAZE PHYSICS ---

def get_mascot_cursor_path(f_rel):
    # Cursor stays inside stage bounds in unscaled space
    if f_rel < 28:
        return 730.0, 480.0, 0.0, 0
    elif f_rel < 65:
        t = (f_rel - 28) / 37.0
        te = ease_in_out_cubic(t)
        p0 = (730.0, 480.0)
        p1 = (430.0, 420.0)
        p2 = (380.0, 290.0)
        x = (1-te)**2 * p0[0] + 2*(1-te)*te * p1[0] + te**2 * p2[0]
        y = (1-te)**2 * p0[1] + 2*(1-te)*te * p1[1] + te**2 * p2[1]
        return x, y, 0.0, 0
    elif f_rel < 95:
        t = (f_rel - 65) / 30.0
        te = ease_in_out_cubic(t)
        p0 = (380.0, 290.0)
        p1 = (680.0, 260.0)
        p2 = (540.0, 360.0)
        x = (1-te)**2 * p0[0] + 2*(1-te)*te * p1[0] + te**2 * p2[0]
        y = (1-te)**2 * p0[1] + 2*(1-te)*te * p1[1] + te**2 * p2[1]
        return x, y, 0.0, 0
    elif f_rel < 130:
        t = (f_rel - 95) / 35.0
        te = ease_out_cubic(t)
        x = lerp(540.0, 540.0, te)
        y = lerp(360.0, 262.0, te)
        return x, y, 0.0, 0
    else:
        t_click = (f_rel - 130) / 10.0
        ring_r = lerp(4.0, 36.0, ease_out_cubic(t_click))
        ring_a = int(lerp(220.0, 0.0, t_click))
        return 540.0, 262.0, ring_r, ring_a

def render_mascot_scene(p, f_rel, f_dur, base_x, base_y):
    w = 180.0
    h = 32.0
    px = base_x + (380.0 - w) / 2.0
    py = base_y

    draw_native_pill(p, px, py, w, h, 16.0)

    # Green Active Indicator
    mid_y = py + h / 2.0
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(16, 185, 129)))
    p.drawEllipse(QPointF(px + 13.0, mid_y), 2.8, 2.8)

    cur_x, cur_y, click_r, click_a = get_mascot_cursor_path(f_rel)

    mid_x = px + w / 2.0
    dist = math.hypot(cur_x - mid_x, cur_y - mid_y)
    is_hover = (dist < 68.0 and f_rel >= 105)
    is_sleeping = (f_rel < 28)
    is_blinking = (f_rel in (44, 45, 46, 88, 89, 90))

    eye_spacing = 17.5
    left_eye_x = mid_x - eye_spacing
    right_eye_x = mid_x + eye_spacing
    eye_y = mid_y - 2.0

    if is_sleeping:
        p.setPen(QPen(QColor(0, 229, 255, 200), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for ex in (left_eye_x, right_eye_x):
            p.drawLine(QPointF(ex - 5.5, eye_y + 1), QPointF(ex + 5.5, eye_y + 1))

        p.setPen(QPen(QColor(255, 255, 255, 180), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(mid_x - 3.5, eye_y + 7.5), QPointF(mid_x + 3.5, eye_y + 7.5))

        zz_float = math.sin(f_rel * 0.25) * 2.5
        p.setFont(QFont("Cantarell", 8, QFont.Weight.Bold))
        p.setPen(QColor(0, 229, 255, 210))
        p.drawText(QRect(int(mid_x + 28), int(eye_y - 8 + zz_float), 30, 20), Qt.AlignmentFlag.AlignLeft, "zZ")
    elif is_hover:
        p.setPen(QPen(QColor(0, 229, 255, 255), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for ex in (left_eye_x, right_eye_x):
            epath = QPainterPath()
            epath.moveTo(ex - 6.0, eye_y + 3.2)
            epath.quadTo(ex, eye_y - 4.5, ex + 6.0, eye_y + 3.2)
            p.drawPath(epath)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 105, 180, 195)))
        p.drawEllipse(QPointF(left_eye_x - 8.5, eye_y + 5.5), 3.8, 2.4)
        p.drawEllipse(QPointF(right_eye_x + 8.5, eye_y + 5.5), 3.8, 2.4)

        p.setPen(QPen(QColor(255, 255, 255, 245), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        mpath = QPainterPath()
        mpath.moveTo(mid_x - 6.0, eye_y + 7.2)
        mpath.quadTo(mid_x, eye_y + 12.5, mid_x + 6.0, eye_y + 7.2)
        p.drawPath(mpath)
    elif is_blinking:
        p.setPen(QPen(QColor(0, 229, 255, 240), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for ex in (left_eye_x, right_eye_x):
            p.drawLine(QPointF(ex - 5.5, eye_y), QPointF(ex + 5.5, eye_y))
    else:
        # High-Precision 3D Parallax OLED Gaze
        dx = (cur_x - mid_x) / 280.0
        dy = (cur_y - mid_y) / 160.0
        gx = max(-1.0, min(1.0, dx))
        gy = max(-1.0, min(1.0, dy))

        for ex in (left_eye_x, right_eye_x):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(0, 229, 255, 65)))
            p.drawRoundedRect(QRectF(ex - 7.5, eye_y - 8.5, 15, 17), 5.5, 5.5)

            p.setBrush(QBrush(QColor(0, 229, 255, 240)))
            p.drawRoundedRect(QRectF(ex - 5.5, eye_y - 6.5, 11, 13), 4, 4)

            pupil_x = ex + (gx * 3.2)
            pupil_y = eye_y + (gy * 2.4)
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.drawEllipse(QPointF(pupil_x, pupil_y), 3.2, 3.2)

            p.setBrush(QBrush(QColor(255, 255, 255, 230)))
            p.drawEllipse(QPointF(pupil_x + 1.6, pupil_y - 1.8), 1.3, 1.3)

        mouth_x = mid_x + (gx * 2.4)
        mouth_y = eye_y + 8.5
        p.setPen(QPen(QColor(255, 255, 255, 240), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        mpath = QPainterPath()
        mpath.moveTo(mouth_x - 4.2, mouth_y)
        mpath.quadTo(mouth_x, mouth_y + 2.6, mouth_x + 4.2, mouth_y)
        p.drawPath(mpath)

    draw_virtual_cursor(p, cur_x, cur_y, click_r, click_a)

# --- 2. INTERACTIVE MEDIA HUB WITH DANCING EQUALIZER & LIVE SEEKBAR ---

def render_media_scene(p, f_rel, f_dur, base_x, base_y):
    t = min(1.0, f_rel / 22.0)
    scale = ease_out_back(t, s=1.1)

    w = lerp(180.0, 380.0, min(1.0, scale))
    h = lerp(32.0, 156.0, min(1.0, scale))
    rad = lerp(16.0, 24.0, min(1.0, scale))
    px = base_x + (380.0 - w) / 2.0
    py = base_y

    draw_native_pill(p, px, py, w, h, rad)

    if scale >= 0.7:
        art_alpha = int(255 * min(1.0, (scale - 0.7) / 0.3))
        art_rect = QRectF(px + 16, py + 16, 54, 54)
        if spotify_art_pix and not spotify_art_pix.isNull():
            p.save()
            clip = QPainterPath()
            clip.addRoundedRect(art_rect, 10, 10)
            p.setClipPath(clip)
            p.setOpacity(art_alpha / 255.0)
            p.drawPixmap(art_rect.toRect(), spotify_art_pix)
            p.restore()
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(36, 36, 44)))
            p.drawRoundedRect(art_rect, 10, 10)

        # Close Button (✕)
        p.setFont(QFont("Cantarell", 11, QFont.Weight.Bold))
        p.setPen(QColor(180, 180, 195, art_alpha))
        p.drawText(QRect(int(px + w - 32), int(py + 12), 20, 20), Qt.AlignmentFlag.AlignCenter, "✕")

        # Track Info (Razor-sharp white: VOCE NA MIRA)
        info_x = int(px + 80)
        info_w = int(w - 80 - 36)
        p.setFont(QFont("Cantarell", 11, QFont.Weight.Bold))
        p.setPen(QColor(255, 255, 255, art_alpha))
        p.drawText(QRect(info_x, int(py + 18), info_w, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "VOCE NA MIRA")

        p.setFont(QFont("Cantarell", 9, QFont.Weight.Medium))
        p.setPen(QColor(190, 195, 210, art_alpha))
        p.drawText(QRect(info_x, int(py + 38), info_w, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "Sxilwix • Slowed")

        p.setFont(QFont("Cantarell", 8, QFont.Weight.Bold))
        p.setPen(QColor(0, 212, 255, art_alpha))
        p.drawText(QRect(info_x, int(py + 56), 65, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "SPOTIFY")

        # Equalizer bars dancing to Jumpstyle beat
        eq_x = info_x + 65
        eq_y = int(py + 68)
        tempo_phase = (f_rel * 2.0 * math.pi / 13.0)
        for i in range(4):
            bar_mod = (math.sin(tempo_phase + i * 1.5) + 1.0) / 2.0
            bh = 4 + int(bar_mod * 12)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(0, 212, 255, art_alpha)))
            p.drawRoundedRect(QRectF(eq_x + i * 5.5, eq_y - bh, 3.2, bh), 1.5, 1.5)

        # Progress Line
        bar_x = px + 18
        bar_y = py + 86
        bar_w = w - 36
        bar_h = 5

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, int(45 * (art_alpha / 255.0)))))
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 2.5, 2.5)

        total_sec = 162  # 2:42
        base_sec = 28 + int(f_rel * 0.4)

        is_seeked = (f_rel >= 70)
        if is_seeked:
            cur_sec = 78  # 1:18
        else:
            cur_sec = min(78, base_sec)

        ratio = cur_sec / float(total_sec)
        fill_w = max(4.0, bar_w * ratio)

        p.setBrush(QBrush(QColor(0, 212, 255, art_alpha)))
        p.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 2.5, 2.5)

        p.setFont(QFont("Cantarell", 8, QFont.Weight.Medium))
        p.setPen(QColor(190, 195, 210, art_alpha))
        pos_str = f"{cur_sec // 60}:{cur_sec % 60:02d}"
        len_str = f"{total_sec // 60}:{total_sec % 60:02d}"
        p.drawText(QRect(int(bar_x), int(bar_y + 7), 50, 14), Qt.AlignmentFlag.AlignLeft, pos_str)
        p.drawText(QRect(int(bar_x + bar_w - 50), int(bar_y + 7), 50, 14), Qt.AlignmentFlag.AlignRight, len_str)

        # Media Controls
        mid_x = int(px + w / 2)
        ctrl_y = int(py + 108)

        p.setFont(QFont("Cantarell", 14, QFont.Weight.Bold))
        p.setPen(QColor(230, 235, 245, art_alpha))
        p.drawText(QRect(mid_x - 55, ctrl_y, 30, 30), Qt.AlignmentFlag.AlignCenter, "⏮")

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, int(35 * (art_alpha / 255.0)))))
        p.drawEllipse(QPoint(mid_x, ctrl_y + 15), 18, 18)

        p.setFont(QFont("Cantarell", 13, QFont.Weight.Bold))
        p.setPen(QColor(255, 255, 255, art_alpha))
        p.drawText(QRect(mid_x - 15, ctrl_y, 30, 30), Qt.AlignmentFlag.AlignCenter, "⏸")

        p.setFont(QFont("Cantarell", 14, QFont.Weight.Bold))
        p.setPen(QColor(230, 235, 245, art_alpha))
        p.drawText(QRect(mid_x + 25, ctrl_y, 30, 30), Qt.AlignmentFlag.AlignCenter, "⏭")

        # Virtual cursor scrubbing & clicking seekbar
        if 25 < f_rel < 115:
            target_click_x = bar_x + bar_w * (78.0 / 162.0)
            target_click_y = bar_y + 2.0
            if f_rel < 70:
                c_t = (f_rel - 25) / 45.0
                cx = lerp(bar_x + 30, target_click_x, ease_out_cubic(c_t))
                cy = lerp(py + 160, target_click_y, ease_out_cubic(c_t))
                ring_r, ring_a = 0.0, 0
            else:
                cx, cy = target_click_x, target_click_y
                t_k = (f_rel - 70) / 14.0
                ring_r = lerp(4.0, 32.0, ease_out_cubic(t_k))
                ring_a = int(lerp(220.0, 0.0, min(1.0, t_k)))

            draw_virtual_cursor(p, cx, cy, ring_r, ring_a)

# --- 3. AUTO-COLLAPSE TRANSITION ---

def render_autoclose_scene(p, f_rel, f_dur, base_x, base_y):
    if f_rel < 40:
        c_t = f_rel / 40.0
        cur_x = lerp(base_x + 200, base_x - 40, ease_out_cubic(c_t))
        cur_y = lerp(base_y + 90, base_y + 240, ease_out_cubic(c_t))

        w = 380.0
        h = 156.0
        px = base_x
        py = base_y
        draw_native_pill(p, px, py, w, h, 24.0)

        fade_a = int(255 * (1.0 - c_t * 0.5))
        p.setFont(QFont("Cantarell", 11, QFont.Weight.Bold))
        p.setPen(QColor(255, 255, 255, fade_a))
        p.drawText(QRect(int(px + 80), int(py + 18), 240, 20), Qt.AlignmentFlag.AlignLeft, "VOCE NA MIRA")

        draw_virtual_cursor(p, cur_x, cur_y)
    else:
        col_t = min(1.0, (f_rel - 40) / 28.0)
        scale = ease_out_cubic(col_t)

        w = lerp(380.0, 190.0, scale)
        h = lerp(156.0, 32.0, scale)
        rad = lerp(24.0, 16.0, scale)
        px = base_x + (380.0 - w) / 2.0
        py = base_y

        draw_native_pill(p, px, py, w, h, rad)

        if scale > 0.6:
            c_alpha = int(255 * (scale - 0.6) / 0.4)
            art_rect = QRectF(px + 7, py + (h - 26) / 2.0, 26, 26)
            if spotify_art_pix and not spotify_art_pix.isNull():
                p.save()
                clip = QPainterPath()
                clip.addRoundedRect(art_rect, 6, 6)
                p.setClipPath(clip)
                p.setOpacity(c_alpha / 255.0)
                p.drawPixmap(art_rect.toRect(), spotify_art_pix)
                p.restore()

            p.setFont(QFont("Cantarell", 9, QFont.Weight.Bold))
            p.setPen(QColor(255, 255, 255, c_alpha))
            p.drawText(QRect(int(px + 38), int(py + 4), 95, 16), Qt.AlignmentFlag.AlignLeft, "VOCE NA MIRA")

            p.setFont(QFont("Cantarell", 8, QFont.Weight.Medium))
            p.setPen(QColor(180, 185, 200, c_alpha))
            p.drawText(QRect(int(px + 38), int(py + 18), 95, 12), Qt.AlignmentFlag.AlignLeft, "Sxilwix")

            eq_x = int(px + w - 30)
            eq_y = int(py + h - 8)
            for i in range(4):
                bh = 4 + int(abs(math.sin(f_rel * 0.35 + i * 1.2)) * 12)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(0, 212, 255, c_alpha)))
                p.drawRoundedRect(QRectF(eq_x + i * 5, eq_y - bh, 3, bh), 1.5, 1.5)

# --- 4. FLUID VOLUME OSD ---

def render_volume_scene(p, f_rel, f_dur, base_x, base_y):
    w = 260.0
    h = 40.0
    px = base_x + (380.0 - w) / 2.0
    py = base_y

    draw_native_pill(p, px, py, w, h, 20.0)

    t = f_rel / float(f_dur)
    if t < 0.35:
        vol = lerp(50, 85, ease_out_cubic(t / 0.35))
    else:
        vol = lerp(85, 135, ease_in_out_cubic((t - 0.35) / 0.65))

    vol_int = int(round(vol))
    is_boost = vol_int > 100

    icon = "🔈" if vol_int <= 33 else ("🔉" if vol_int <= 66 else ("🔊" if not is_boost else "🔥"))
    p.setFont(QFont("Cantarell", 12))
    p.setPen(QColor(255, 255, 255))
    p.drawText(QRect(int(px + 12), int(py), 24, int(h)), Qt.AlignmentFlag.AlignCenter, icon)

    bar_x = px + 42
    bar_y = py + (h - 6) / 2.0
    bar_w = w - 42 - 50
    bar_h = 6

    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(255, 255, 255, 45)))
    p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 3, 3)

    max_v = 150.0 if is_boost else 100.0
    ratio = min(1.0, max(0.0, vol / max_v))
    fill_w = max(4.0, bar_w * ratio)

    bar_color = QColor(0, 212, 255) if not is_boost else QColor(255, 179, 0)
    p.setBrush(QBrush(bar_color))
    p.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 3, 3)

    text = f"{vol_int}%"
    p.setFont(QFont("Cantarell", 9, QFont.Weight.Bold))
    p.setPen(bar_color if is_boost else QColor(255, 255, 255))
    p.drawText(QRect(int(px + w - 46), int(py), 40, int(h)), Qt.AlignmentFlag.AlignCenter, text)

# --- 5. NOTIFICATION & RAPID SUBUH-TO-ISYA CYBER GLITCH CYCLE ---

def render_notif_prayer_scene(p, f_rel, f_dur, base_x, base_y):
    w = 340.0
    h = 60.0
    px = base_x + (380.0 - w) / 2.0
    py = base_y

    draw_native_pill(p, px, py, w, h, 20.0)

    # First 25 frames (~0.8s): WhatsApp Notification
    if f_rel < 25:
        p.setFont(QFont("Cantarell", 20))
        p.drawText(QRect(int(px + 12), int(py + 10), 40, 40), Qt.AlignmentFlag.AlignCenter, "💬")

        p.setFont(QFont("Cantarell", 10, QFont.Weight.Bold))
        p.setPen(QColor(0, 230, 118))
        p.drawText(QRect(int(px + 60), int(py + 10), int(w - 70), 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "WhatsApp • Reza Rizki")

        p.setFont(QFont("Cantarell", 9, QFont.Weight.Medium))
        p.setPen(QColor(230, 235, 245))
        p.drawText(QRect(int(px + 60), int(py + 30), int(w - 70), 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "Project ixsland siap di-push ke GitHub!")
        return

    # From frame 25 to 140 (115 frames): Rapid Subuh -> Dzuhur -> Ashar -> Maghrib -> Isya Glitch Cycle!
    cycle_f = f_rel - 25
    step_frames = 23  # Each prayer displays for ~23 frames (~0.76s)
    prayer_idx = min(len(PRAYER_SCHEDULE) - 1, int(cycle_f // step_frames))
    p_name, p_time = PRAYER_SCHEDULE[prayer_idx]

    sub_f = cycle_f % step_frames
    is_glitching = (sub_f < 6)

    glitch_offset_x = 0
    if is_glitching:
        glitch_offset_x = int(math.sin(sub_f * 2.8) * 4)

    # Mosque Icon
    p.setFont(QFont("Cantarell", 20))
    p.drawText(QRect(int(px + 12 + glitch_offset_x), int(py + 10), 40, 40), Qt.AlignmentFlag.AlignCenter, "🕌")

    # Cyber Glitch Chromatic Text Shift
    title_text = f"WAKTU SHOLAT {p_name}"
    time_text = f"{p_time} • Otomatis jeda musik player"

    if is_glitching:
        p.setFont(QFont("Cantarell", 10, QFont.Weight.Bold))
        p.setPen(QColor(0, 255, 255, 180))
        p.drawText(QRect(int(px + 62), int(py + 12), int(w - 70), 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title_text)

        p.setPen(QColor(255, 0, 110, 180))
        p.drawText(QRect(int(px + 58), int(py + 12), int(w - 70), 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title_text)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 212, 255, 45)))
        p.drawRect(QRect(int(px + 10), int(py + 15 + sub_f * 6), int(w - 20), 3))

    # Main Crisp Text
    p.setFont(QFont("Cantarell", 10, QFont.Weight.Bold))
    p.setPen(QColor(255, 204, 0))
    p.drawText(QRect(int(px + 60), int(py + 12), int(w - 70), 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title_text)

    p.setFont(QFont("Cantarell", 9, QFont.Weight.Medium))
    p.setPen(QColor(240, 245, 255))
    p.drawText(QRect(int(px + 60), int(py + 32), int(w - 70), 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, time_text)

# --- 6. CLOSING SCENE & SEAMLESS LOOP CONNECTOR ---

def render_closing_scene(p, f_rel, f_dur, base_x, base_y):
    w = 180.0
    h = 32.0
    px = base_x + (380.0 - w) / 2.0
    py = base_y

    draw_native_pill(p, px, py, w, h, 16.0)

    # Green Dot
    mid_y = py + h / 2.0
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(16, 185, 129)))
    p.drawEllipse(QPointF(px + 13.0, mid_y), 2.8, 2.8)

    mid_x = px + w / 2.0
    eye_spacing = 17.5
    left_eye_x = mid_x - eye_spacing
    right_eye_x = mid_x + eye_spacing
    eye_y = mid_y - 2.0

    # In final 16 frames: seamlessly morph smile into sleeping line to match Frame 0!
    if f_rel > 114:
        p.setPen(QPen(QColor(0, 229, 255, 200), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for ex in (left_eye_x, right_eye_x):
            p.drawLine(QPointF(ex - 5.5, eye_y + 1), QPointF(ex + 5.5, eye_y + 1))

        p.setPen(QPen(QColor(255, 255, 255, 180), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(mid_x - 3.5, eye_y + 7.5), QPointF(mid_x + 3.5, eye_y + 7.5))
    else:
        # Smiling Eyes
        p.setPen(QPen(QColor(0, 229, 255, 255), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for ex in (left_eye_x, right_eye_x):
            epath = QPainterPath()
            epath.moveTo(ex - 6.0, eye_y + 3.2)
            epath.quadTo(ex, eye_y - 4.5, ex + 6.0, eye_y + 3.2)
            p.drawPath(epath)

        # Joyous Smile
        p.setPen(QPen(QColor(255, 255, 255, 245), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        mpath = QPainterPath()
        mpath.moveTo(mid_x - 6.0, eye_y + 7.2)
        mpath.quadTo(mid_x, eye_y + 12.5, mid_x + 6.0, eye_y + 7.2)
        p.drawPath(mpath)

    # SEAMLESS LOOP CONNECTOR:
    # Cursor smoothly glides back towards (730, 480) in the final 40 frames!
    if f_rel > 90:
        c_loop_t = (f_rel - 90) / 40.0
        cur_x = lerp(540.0, 730.0, ease_in_out_cubic(c_loop_t))
        cur_y = lerp(262.0, 480.0, ease_in_out_cubic(c_loop_t))
        draw_virtual_cursor(p, cur_x, cur_y)

# --- DYNAMIC BOTTOM CARD WITH HIGH-TECH HUD & GLITCH TRANSITIONS ---

def render_bottom_card(p, scene_idx, frame_num):
    card_x = 60
    card_y = 855
    card_w = 960
    card_h = 515

    scene = SCENES[scene_idx]
    f_rel = frame_num - scene["start"]

    t_in = min(1.0, f_rel / 14.0)
    card_slide_y = (1.0 - ease_out_cubic(t_in)) * 25.0
    content_alpha = int(255 * ease_out_cubic(t_in))

    # Glassmorphic Tech Container
    card_grad = QLinearGradient(card_x, card_y, card_x + card_w, card_y + card_h)
    card_grad.setColorAt(0.0, QColor(16, 18, 26, 250))
    card_grad.setColorAt(1.0, QColor(10, 11, 17, 252))

    p.setPen(QPen(QColor(255, 255, 255, 40), 1.5))
    p.setBrush(QBrush(card_grad))
    p.drawRoundedRect(QRectF(card_x, card_y, card_w, card_h), 28, 28)

    # Cyber Corner Brackets [ ]
    corner_len = 22
    p.setPen(QPen(QColor(0, 229, 255, 180), 2.0))
    # Top-left
    p.drawLine(QPointF(card_x + 12, card_y + 12), QPointF(card_x + 12 + corner_len, card_y + 12))
    p.drawLine(QPointF(card_x + 12, card_y + 12), QPointF(card_x + 12, card_y + 12 + corner_len))
    # Top-right
    p.drawLine(QPointF(card_x + card_w - 12, card_y + 12), QPointF(card_x + card_w - 12 - corner_len, card_y + 12))
    p.drawLine(QPointF(card_x + card_w - 12, card_y + 12), QPointF(card_x + card_w - 12, card_y + 12 + corner_len))
    # Bottom-left
    p.drawLine(QPointF(card_x + 12, card_y + card_h - 12), QPointF(card_x + 12 + corner_len, card_y + card_h - 12))
    p.drawLine(QPointF(card_x + 12, card_y + card_h - 12), QPointF(card_x + 12, card_y + card_h - 12 - corner_len))
    # Bottom-right
    p.drawLine(QPointF(card_x + card_w - 12, card_y + card_h - 12), QPointF(card_x + card_w - 12 - corner_len, card_y + card_h - 12))
    p.drawLine(QPointF(card_x + card_w - 12, card_y + card_h - 12), QPointF(card_x + card_w - 12, card_y + card_h - 12 - corner_len))

    # Background Cyber Spectrum visualizer bars (gives dynamic tech life!)
    for i in range(32):
        bx = card_x + 40 + i * 28
        by = card_y + card_h - 85
        bh = 8 + int(math.sin(frame_num * 0.18 + i * 0.45) * 20 + 20)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 212, 255, 12)))
        p.drawRoundedRect(QRectF(bx, by - bh, 14, bh), 3, 3)

    # Top Accent Beam
    p.setPen(Qt.PenStyle.NoPen)
    beam_sweep = (math.sin(frame_num / 25.0) + 1.0) / 2.0
    bar_grad = QLinearGradient(card_x + 40, card_y, card_x + card_w - 40, card_y)
    bar_grad.setColorAt(0.0, QColor(0, 212, 255, 240))
    bar_grad.setColorAt(lerp(0.2, 0.8, beam_sweep), QColor(170, 110, 255, 245))
    bar_grad.setColorAt(1.0, QColor(0, 212, 255, 240))
    p.setBrush(QBrush(bar_grad))
    p.drawRoundedRect(QRectF(card_x + 36, card_y, card_w - 72, 3.5), 1.75, 1.75)

    # SEGMENTED FEATURE NAVIGATION TABS
    nav_y = card_y + 24
    nav_w = card_w - 72
    nav_x = card_x + 36
    num_tabs = len(SCENES)
    tab_w = nav_w / float(num_tabs)

    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(255, 255, 255, 14)))
    p.drawRoundedRect(QRectF(nav_x, nav_y, nav_w, 36), 18, 18)

    target_tab_idx = float(scene_idx)
    # If in final 16 frames of closing scene, smoothly glide tab back to 0 (01 Mascot)!
    if scene_idx == len(SCENES) - 1 and f_rel > 114:
        ret_t = (f_rel - 114) / 16.0
        target_tab_idx = lerp(float(len(SCENES) - 1), 0.0, ease_in_out_cubic(ret_t))

    target_tab_x = nav_x + target_tab_idx * tab_w
    p.setBrush(QBrush(QColor(0, 212, 255, 50)))
    p.setPen(QPen(QColor(0, 212, 255, 200), 1.2))
    p.drawRoundedRect(QRectF(target_tab_x + 2, nav_y + 2, tab_w - 4, 32), 16, 16)

    p.setFont(QFont("Cantarell", 9, QFont.Weight.Bold))
    for i, sc in enumerate(SCENES):
        tx = nav_x + i * tab_w
        is_active = (i == scene_idx)
        p.setPen(QColor(255, 255, 255, 255) if is_active else QColor(150, 158, 175, 180))
        p.drawText(QRectF(tx, nav_y, tab_w, 36), Qt.AlignmentFlag.AlignCenter, sc["tab"])

    # High-Contrast Content Container with Cyber Glitch on Scene Transitions!
    cy = card_y + 75 + card_slide_y

    is_card_glitch = (f_rel < 10)
    glitch_dx = 0
    if is_card_glitch:
        glitch_dx = int(math.sin(f_rel * 3.8) * 4)
        # Scanline slice cuts across the card during transition
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 229, 255, 50)))
        p.drawRect(QRect(int(card_x + 36), int(cy + 10 + (f_rel * 14) % 110), int(card_w - 72), 3))
        p.setBrush(QBrush(QColor(255, 0, 110, 40)))
        p.drawRect(QRect(int(card_x + 60), int(cy + 35 + (f_rel * 9) % 130), int(card_w - 120), 2))

    # Title with chromatic glitch
    title_text = scene["title"]
    sub_text = scene["sub"]

    if is_card_glitch:
        # Cyan Chromatic Split
        p.setFont(QFont("Cantarell", 23, QFont.Weight.ExtraBold))
        p.setPen(QColor(0, 255, 255, int(180 * (content_alpha / 255.0))))
        p.drawText(QRectF(card_x + 40 + glitch_dx + 2, cy, card_w - 80, 36), Qt.AlignmentFlag.AlignLeft, title_text)
        # Magenta Chromatic Split
        p.setPen(QColor(255, 0, 110, int(180 * (content_alpha / 255.0))))
        p.drawText(QRectF(card_x + 40 + glitch_dx - 2, cy, card_w - 80, 36), Qt.AlignmentFlag.AlignLeft, title_text)

    # Main Title
    p.setFont(QFont("Cantarell", 23, QFont.Weight.ExtraBold))
    p.setPen(QColor(255, 255, 255, content_alpha))
    p.drawText(QRectF(card_x + 40 + glitch_dx, cy, card_w - 80, 36), Qt.AlignmentFlag.AlignLeft, title_text)

    # Subtitle
    p.setFont(QFont("Cantarell", 12, QFont.Weight.Medium))
    p.setPen(QColor(185, 195, 215, content_alpha))
    p.drawText(QRectF(card_x + 40, cy + 38, card_w - 80, 24), Qt.AlignmentFlag.AlignLeft, sub_text)

    # High-Contrast Numbered Bullets
    by = cy + 78
    for idx, (title_b, desc_b) in enumerate(scene["bullets"]):
        p.setPen(QPen(QColor(0, 212, 255, int(180 * (content_alpha / 255.0))), 1.4))
        p.setBrush(QBrush(QColor(0, 212, 255, int(30 * (content_alpha / 255.0)))))
        p.drawEllipse(QPointF(card_x + 58, by + 18), 16, 16)

        p.setFont(QFont("Cantarell", 9, QFont.Weight.Bold))
        p.setPen(QColor(0, 212, 255, content_alpha))
        p.drawText(QRectF(card_x + 42, by + 2, 32, 32), Qt.AlignmentFlag.AlignCenter, f"{idx+1:02d}")

        p.setFont(QFont("Cantarell", 12, QFont.Weight.Bold))
        p.setPen(QColor(255, 255, 255, content_alpha))
        p.drawText(QRectF(card_x + 88, by - 2, card_w - 135, 22), Qt.AlignmentFlag.AlignLeft, title_b)

        p.setFont(QFont("Cantarell", 10, QFont.Weight.Normal))
        p.setPen(QColor(200, 208, 225, content_alpha))
        p.drawText(QRectF(card_x + 88, by + 20, card_w - 135, 36), Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, desc_b)

        by += 68

    # Tags along bottom
    tx = card_x + 40
    ty = card_y + card_h - 52
    for t in scene["tags"]:
        tw = len(t) * 9 + 26
        p.setPen(QPen(QColor(0, 212, 255, int(90 * (content_alpha / 255.0))), 1))
        p.setBrush(QBrush(QColor(0, 212, 255, int(20 * (content_alpha / 255.0)))))
        p.drawRoundedRect(QRectF(tx, ty, tw, 28), 14, 14)

        p.setFont(QFont("Cantarell", 9, QFont.Weight.Bold))
        p.setPen(QColor(0, 229, 255, content_alpha))
        p.drawText(QRectF(tx, ty, tw, 28), Qt.AlignmentFlag.AlignCenter, t)
        tx += tw + 10

# --- MAIN COMPOSITOR ---

def render_frame(frame_num):
    pix = QPixmap(WIDTH, HEIGHT)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    # 1. Dark Tech Background
    bg_grad = QLinearGradient(0, 0, WIDTH, HEIGHT)
    bg_grad.setColorAt(0.0, QColor(10, 11, 16))
    bg_grad.setColorAt(0.4, QColor(14, 15, 24))
    bg_grad.setColorAt(1.0, QColor(9, 10, 14))
    p.fillRect(0, 0, WIDTH, HEIGHT, bg_grad)

    flare_phase = (math.sin(frame_num / 38.0) + 1.0) / 2.0

    # 2. Desktop Stage Mockup (Clean Sonoma Wallpaper)
    stage_rect = QRectF(60, 220, 960, 580)

    p.save()
    stage_clip = QPainterPath()
    stage_clip.addRoundedRect(stage_rect, 28, 28)
    p.setClipPath(stage_clip)

    if wallpaper_pix and not wallpaper_pix.isNull():
        scaled_wall = wallpaper_pix.scaled(
            int(stage_rect.width()), int(stage_rect.height()),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        p.drawPixmap(stage_rect.toRect(), scaled_wall)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 0, 0, 38)))
        p.drawRect(stage_rect.toRect())
    else:
        p.fillRect(stage_rect.toRect(), QColor(50, 70, 150))

    # Top Bezel Notch Mockup
    p.setPen(QPen(QColor(255, 255, 255, 30), 1))
    p.setBrush(QBrush(QColor(0, 0, 0, 140)))
    p.drawRoundedRect(QRectF(WIDTH / 2 - 60, 226, 120, 8), 4, 4)

    # Tech Telemetry inside Stage (Sleek Glass Badges with Perfect Contrast)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(10, 12, 18, 190)))
    p.drawRoundedRect(QRectF(96, 232, 165, 22), 11, 11)
    p.setPen(QPen(QColor(255, 255, 255, 40), 1.0))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(96, 232, 165, 22), 11, 11)

    p.setFont(QFont("Cantarell", 8, QFont.Weight.Bold))
    p.setPen(QColor(0, 230, 118))
    p.drawText(QRect(106, 232, 145, 22), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "● 60 FPS • WAYLAND")

    # Right Badge
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(10, 12, 18, 190)))
    p.drawRoundedRect(QRectF(WIDTH - 256, 232, 150, 22), 11, 11)
    p.setPen(QPen(QColor(255, 255, 255, 40), 1.0))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(WIDTH - 256, 232, 150, 22), 11, 11)

    p.setFont(QFont("Cantarell", 8, QFont.Weight.Medium))
    p.setPen(QColor(210, 220, 240, 220))
    p.drawText(QRect(WIDTH - 256, 232, 150, 22), Qt.AlignmentFlag.AlignCenter, "DYNAMIC ISLAND v2.4")

    # 3. Dynamic Island Rendering (Zoomed ~1.85x for massive focal view)
    base_island_x = (WIDTH - 380) / 2.0
    base_island_y = 246.0

    scene = get_current_scene(frame_num)
    scene_idx = get_scene_index(frame_num)
    f_rel = frame_num - scene["start"]
    f_dur = scene["end"] - scene["start"]

    p.save()
    p.translate(WIDTH / 2.0, base_island_y)
    p.scale(ISLAND_ZOOM, ISLAND_ZOOM)
    p.translate(-WIDTH / 2.0, -base_island_y)

    if scene["id"] == "MASCOT":
        render_mascot_scene(p, f_rel, f_dur, base_island_x, base_island_y)
    elif scene["id"] == "MEDIA":
        render_media_scene(p, f_rel, f_dur, base_island_x, base_island_y)
    elif scene["id"] == "AUTOCLOSE":
        render_autoclose_scene(p, f_rel, f_dur, base_island_x, base_island_y)
    elif scene["id"] == "VOLUME":
        render_volume_scene(p, f_rel, f_dur, base_island_x, base_island_y)
    elif scene["id"] == "NOTIF_PRAYER":
        render_notif_prayer_scene(p, f_rel, f_dur, base_island_x, base_island_y)
    elif scene["id"] == "CLOSING":
        render_closing_scene(p, f_rel, f_dur, base_island_x, base_island_y)

    p.restore()
    p.restore()

    # Stage border with cyber animated beam
    beam_pos = (math.sin(frame_num / 20.0) + 1.0) / 2.0
    stage_border_grad = QLinearGradient(stage_rect.left(), stage_rect.top(), stage_rect.right(), stage_rect.bottom())
    stage_border_grad.setColorAt(0.0, QColor(0, 212, 255, 120))
    stage_border_grad.setColorAt(beam_pos, QColor(170, 110, 255, 180))
    stage_border_grad.setColorAt(1.0, QColor(0, 212, 255, 120))

    p.setPen(QPen(stage_border_grad, 1.6))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(stage_rect, 28, 28)

    # Stage Cyber Corner Brackets [ ]
    s_corner = 20
    p.setPen(QPen(QColor(0, 229, 255, 190), 2.0))
    p.drawLine(QPointF(stage_rect.left() + 10, stage_rect.top() + 10), QPointF(stage_rect.left() + 10 + s_corner, stage_rect.top() + 10))
    p.drawLine(QPointF(stage_rect.left() + 10, stage_rect.top() + 10), QPointF(stage_rect.left() + 10, stage_rect.top() + 10 + s_corner))
    p.drawLine(QPointF(stage_rect.right() - 10, stage_rect.top() + 10), QPointF(stage_rect.right() - 10 - s_corner, stage_rect.top() + 10))
    p.drawLine(QPointF(stage_rect.right() - 10, stage_rect.top() + 10), QPointF(stage_rect.right() - 10, stage_rect.top() + 10 + s_corner))
    p.drawLine(QPointF(stage_rect.left() + 10, stage_rect.bottom() - 10), QPointF(stage_rect.left() + 10 + s_corner, stage_rect.bottom() - 10))
    p.drawLine(QPointF(stage_rect.left() + 10, stage_rect.bottom() - 10), QPointF(stage_rect.left() + 10, stage_rect.bottom() - 10 - s_corner))
    p.drawLine(QPointF(stage_rect.right() - 10, stage_rect.bottom() - 10), QPointF(stage_rect.right() - 10 - s_corner, stage_rect.bottom() - 10))
    p.drawLine(QPointF(stage_rect.right() - 10, stage_rect.bottom() - 10), QPointF(stage_rect.right() - 10, stage_rect.bottom() - 10 - s_corner))

    # 4. TOP BRANDING (Zero mention of DP-1!)
    gh_w = 440
    gh_h = 48
    gh_x = (WIDTH - gh_w) / 2
    gh_y = 48

    p.setPen(QPen(QColor(0, 212, 255, int(90 + flare_phase * 40)), 1.4))
    p.setBrush(QBrush(QColor(18, 20, 30, 235)))
    p.drawRoundedRect(QRectF(gh_x, gh_y, gh_w, gh_h), 24, 24)

    # Green pulse
    pulse_r = 5.0 + flare_phase * 1.5
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(0, 230, 118, int(80 + flare_phase * 100))))
    p.drawEllipse(QPointF(gh_x + 28, gh_y + 24), pulse_r + 3, pulse_r + 3)
    p.setBrush(QBrush(QColor(0, 230, 118)))
    p.drawEllipse(QPointF(gh_x + 28, gh_y + 24), 4.5, 4.5)

    p.setFont(QFont("Cantarell", 11, QFont.Weight.Bold))
    p.setPen(QColor(255, 255, 255))
    p.drawText(QRectF(gh_x + 44, gh_y, gh_w - 60, gh_h), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "github.com/rezariski/ixsland")

    p.setFont(QFont("Cantarell", 24, QFont.Weight.ExtraBold))
    p.setPen(QColor(255, 255, 255))
    p.drawText(QRectF(0, 112, WIDTH, 38), Qt.AlignmentFlag.AlignCenter, "IXSLAND DYNAMIC ISLAND")

    p.setFont(QFont("Cantarell", 11, QFont.Weight.Medium))
    p.setPen(QColor(185, 195, 215))
    p.drawText(QRectF(0, 154, WIDTH, 24), Qt.AlignmentFlag.AlignCenter, "Native Linux Dynamic Island • KDE Plasma 6 Wayland")

    # 5. BOTTOM CARD WITH SEGMENTED TABS & GLITCH
    render_bottom_card(p, scene_idx, frame_num)

    p.end()
    return pix

def build_synchronized_audio(output_audio_path):
    print("Building VOCE NA MIRA JUMPSTYLE soundtrack (starts at 12s, flat 0.18 with notification ducking)...")
    music_filter = (
        "[1:a]volume=0.18,afade=t=in:st=0:d=1.0,afade=t=out:st=26.0:d=2.0,"
        "volume=eval=frame:volume=\'"
        "if(between(t,19.0,21.5), if(lt(t,19.3), 1.0 - (t-19.0)/0.3 * 0.72, if(lt(t,20.6), 0.28, 0.28 + (t-20.6)/0.9 * 0.72)), 1.0)"
        "\'[mus]; "
        "[2:a]volume=0.40,adelay=300|300[sfx_intro]; "
        "[3:a]volume=0.90,adelay=4600|4600[sfx_pop]; "
        "[4:a]volume=0.90,adelay=7000|7000[sfx_seek]; "
        "[5:a]volume=0.70,adelay=9800|9800[sfx_collapse]; "
        "[6:a]volume=0.75,adelay=14200|14200[sfx_vol1]; "
        "[7:a]volume=0.80,adelay=16000|16000[sfx_vol2]; "
        "[8:a]volume=0.95,adelay=19000|19000[sfx_notif]; "
        "[9:a]volume=0.70,adelay=21000|21000[sfx_prayer]; "
        "[10:a]volume=0.75,adelay=24000|24000[sfx_close]; "
        "[0:a][mus][sfx_intro][sfx_pop][sfx_seek][sfx_collapse][sfx_vol1][sfx_vol2][sfx_notif][sfx_prayer][sfx_close]amix=inputs=11:duration=first:dropout_transition=0[outa]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-t", "28", "-i", "anullsrc=r=44100:cl=stereo",
        "-ss", "12", "-t", "28", "-i", SPOTIFY_SONG_PATH,
        "-i", "/usr/share/sounds/ocean/stereo/desktop-login.oga",
        "-i", "/usr/share/sounds/ocean/stereo/button-pressed.oga",
        "-i", "/usr/share/sounds/ocean/stereo/button-pressed.oga",
        "-i", "/usr/share/sounds/ocean/stereo/button-pressed.oga",
        "-i", "/usr/share/sounds/ocean/stereo/audio-volume-change.oga",
        "-i", "/usr/share/sounds/ocean/stereo/audio-volume-change.oga",
        "-i", "/usr/share/sounds/ocean/stereo/message-new-instant.oga",
        "-i", "/usr/share/sounds/ocean/stereo/completion-success.oga",
        "-i", "/usr/share/sounds/ocean/stereo/completion-success.oga",
        "-filter_complex", music_filter,
        "-map", "[outa]",
        "-t", "28",
        "-c:a", "aac",
        "-b:a", "256k",
        output_audio_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print("Soundtrack built successfully!")

def main():
    print("=== ixsland High-End Promo Generator (3:4 Ratio - 1080x1440 @ 30 FPS) ===")
    print(f"Total frames: {TOTAL_FRAMES} (~28 seconds)")

    temp_video = "/tmp/ixsland_temp_video.mp4"
    temp_audio = "/tmp/ixsland_temp_soundtrack.m4a"

    # Step 1: Build Audio
    build_synchronized_audio(temp_audio)

    # Step 2: Render Video Frames
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgba",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        temp_video
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    for i in range(TOTAL_FRAMES):
        pix = render_frame(i)
        img = pix.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        raw_bytes = img.bits().asstring(WIDTH * HEIGHT * 4)
        proc.stdin.write(raw_bytes)

        if i % 60 == 0 or i == TOTAL_FRAMES - 1:
            pct = int((i + 1) / TOTAL_FRAMES * 100)
            sys.stdout.write(f"\rRendering video frames: {pct}% ({i+1}/{TOTAL_FRAMES} frames)...")
            sys.stdout.flush()

    proc.stdin.close()
    proc.wait()
    print("\nVideo frames rendered!")

    # Step 3: Mux Video + Audio
    print("Muxing video with synchronized audio soundtrack...")
    mux_cmd = [
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", temp_audio,
        "-c:v", "copy",
        "-c:a", "copy",
        "-movflags", "+faststart",
        OUTPUT_VIDEO
    ]
    subprocess.run(mux_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Step 4: Save high-res cover thumbnail
    thumb = render_frame(210)
    thumb.save(THUMBNAIL_IMG)
    print(f"Thumbnail saved: {THUMBNAIL_IMG}")
    print(f"Final video ready: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
