#!/usr/bin/env python3
"""
ixsland Dynamic Island for Linux (KDE Wayland / X11)
Targeted for Primary / Main Display - Full Feature Parity & Fixed Anchoring
Includes Interactive Eye-Tracking Robot Mascot & Unclipped Fluid Morphing
"""

import sys
import os
import math
import time
import json
import glob
import tempfile
import urllib.request
import subprocess
from datetime import datetime, date

from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QRect, QRectF, QSize, QPointF,
    QVariantAnimation, QEasingCurve, pyqtSignal, pyqtSlot, QObject
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGraphicsDropShadowEffect, QMenu
)
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPainterPath,
    QFont, QPixmap, QAction, QRegion
)
from PyQt6 import QtDBus

CONFIG_DIR = os.path.expanduser("~/.local/share/ixsland")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
CACHE_DIR = "/tmp/ixsland_cache"
NOTIF_FILE = "/tmp/macos-notifications-history.json"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# Fixed Canvas Geometry (Wayland toplevel MUST never resize to keep KWin position permanent)
CANVAS_W = 380
CANVAS_H = 175

DEFAULT_CONFIG = {
    "target_screen": "primary",
    "top_margin": 16,
    "latitude": -6.2088,
    "longitude": 106.8456,
    "timezone": 7.0,
    "city": "Jakarta (WIB)",
    "pause_music_on_adzan": True
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
                return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

# --- PRAYER TIMES CALCULATION (OFFLINE PRAYER TIMES ENGINE) ---
def calculate_prayer_times(lat, lng, tz_offset, dt=None):
    if dt is None:
        dt = date.today()
    day_of_year = dt.timetuple().tm_yday
    b = 2 * math.pi * (day_of_year - 81) / 365.0
    eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    solar_noon_minutes = 720 - (4 * lng) - eot + (tz_offset * 60)
    
    decl = 23.45 * math.sin(math.radians(360 / 365.0 * (day_of_year - 81)))
    decl_rad = math.radians(decl)
    lat_rad = math.radians(lat)
    
    def hour_angle(alt):
        alt_rad = math.radians(alt)
        num = math.sin(alt_rad) - math.sin(lat_rad) * math.sin(decl_rad)
        den = math.cos(lat_rad) * math.cos(decl_rad)
        cos_ha = num / den
        if cos_ha > 1: return 0.0
        if cos_ha < -1: return 180.0
        return math.degrees(math.acos(cos_ha))
    
    ha_fajr = hour_angle(-20.0)
    ha_maghrib = hour_angle(-0.833)
    ha_isha = hour_angle(-18.0)
    
    asr_alt = math.degrees(math.atan(1.0 / (1.0 + math.tan(math.radians(abs(lat - decl))))))
    ha_asr = hour_angle(asr_alt)
    
    fajr_min = solar_noon_minutes - (ha_fajr * 4)
    dhuhr_min = solar_noon_minutes + 2
    asr_min = solar_noon_minutes + (ha_asr * 4)
    maghrib_min = solar_noon_minutes + (ha_maghrib * 4)
    isha_min = solar_noon_minutes + (ha_isha * 4)
    
    def min_to_str(m):
        m = int(round(m))
        h = (m // 60) % 24
        mn = m % 60
        return f"{h:02d}:{mn:02d}"

    def min_to_mins(m):
        return int(round(m))
    
    return [
        ("Subuh", min_to_str(fajr_min), min_to_mins(fajr_min)),
        ("Dzuhur", min_to_str(dhuhr_min), min_to_mins(dhuhr_min)),
        ("Ashar", min_to_str(asr_min), min_to_mins(asr_min)),
        ("Maghrib", min_to_str(maghrib_min), min_to_mins(maghrib_min)),
        ("Isya", min_to_str(isha_min), min_to_mins(isha_min))
    ]

# --- MPRIS MEDIA MONITOR ---
class MediaController(QObject):
    mediaChanged = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.bus = QtDBus.QDBusConnection.sessionBus()
        self.current_player = None
        self.current_info = {
            "status": "Stopped",
            "title": "",
            "artist": "",
            "art_url": "",
            "art_pixmap": None,
            "length": 0,
            "position": 0,
            "player": "",
            "trackid": ""
        }
        self.cached_art_url = None
        self.cached_pixmap = None
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_media)
        self.timer.start(500)
        self.poll_media()

    def get_active_players(self):
        interface = QtDBus.QDBusInterface(
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus",
            self.bus
        )
        reply = interface.call("ListNames")
        if reply.type() == QtDBus.QDBusMessage.MessageType.ReplyMessage:
            names = reply.arguments()[0]
            return [n for n in names if n.startswith("org.mpris.MediaPlayer2.")]
        return []

    def poll_media(self):
        players = self.get_active_players()
        if not players:
            if self.current_info["status"] != "Stopped":
                self.current_info = {
                    "status": "Stopped", "title": "", "artist": "",
                    "art_url": "", "art_pixmap": None, "length": 0, "position": 0, "player": ""
                }
                self.mediaChanged.emit(self.current_info)
            return

        best_player = players[0]
        best_props = None
        
        for p in players:
            msg = QtDBus.QDBusMessage.createMethodCall(
                p, "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties", "GetAll"
            )
            msg.setArguments(["org.mpris.MediaPlayer2.Player"])
            reply = self.bus.call(msg, QtDBus.QDBus.CallMode.Block, 100)
            if reply.type() == QtDBus.QDBusMessage.MessageType.ReplyMessage:
                props = reply.arguments()[0]
                status = str(props.get("PlaybackStatus", "Stopped"))
                if status == "Playing":
                    best_player = p
                    best_props = props
                    break
                elif best_props is None:
                    best_props = props

        if not best_props:
            return

        status = str(best_props.get("PlaybackStatus", "Stopped"))
        meta = best_props.get("Metadata", {})
        title = str(meta.get("xesam:title", ""))
        artists = meta.get("xesam:artist", [])
        artist = ", ".join(artists) if isinstance(artists, list) else str(artists)
        art_url = str(meta.get("mpris:artUrl", ""))
        trackid = str(meta.get("mpris:trackid", ""))
        
        try:
            length = int(meta.get("mpris:length", 0)) // 1000000
        except Exception:
            length = 0

        pos = 0
        try:
            pos_msg = QtDBus.QDBusMessage.createMethodCall(
                best_player, "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties", "Get"
            )
            pos_msg.setArguments(["org.mpris.MediaPlayer2.Player", "Position"])
            pos_reply = self.bus.call(pos_msg, QtDBus.QDBus.CallMode.Block, 80)
            if pos_reply.type() == QtDBus.QDBusMessage.MessageType.ReplyMessage:
                pos = int(pos_reply.arguments()[0]) // 1000000
        except Exception:
            pos = 0

        player_name = best_player.replace("org.mpris.MediaPlayer2.", "").capitalize()
        
        if art_url != self.cached_art_url:
            self.cached_art_url = art_url
            self.cached_pixmap = self.fetch_art(art_url)

        changed = (
            self.current_info["status"] != status or
            self.current_info["title"] != title or
            self.current_info["artist"] != artist or
            self.current_player != best_player or
            self.current_info.get("position", 0) != pos or
            self.current_info.get("length", 0) != length
        )

        self.current_player = best_player
        self.current_info = {
            "status": status,
            "title": title,
            "artist": artist,
            "art_url": art_url,
            "art_pixmap": self.cached_pixmap,
            "length": length,
            "position": pos,
            "player": player_name,
            "trackid": trackid
        }

        if changed:
            self.mediaChanged.emit(self.current_info)

    def seek(self, target_seconds):
        if not self.current_player:
            return
        trackid = self.current_info.get("trackid", "")
        if not trackid:
            return
        try:
            target_us = str(int(target_seconds * 1000000))
            subprocess.Popen([
                "qdbus6", self.current_player, "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.Player.SetPosition", trackid, target_us
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.current_info["position"] = int(target_seconds)
            self.mediaChanged.emit(self.current_info)
        except Exception:
            pass

    def fetch_art(self, url):
        if not url:
            return None
        try:
            if url.startswith("file://"):
                path = url[7:]
                pix = QPixmap(path)
                return pix if not pix.isNull() else None
            elif url.startswith("http://") or url.startswith("https://"):
                hashed = str(abs(hash(url))) + ".jpg"
                dest = os.path.join(CACHE_DIR, hashed)
                if not os.path.exists(dest):
                    urllib.request.urlretrieve(url, dest)
                pix = QPixmap(dest)
                return pix if not pix.isNull() else None
        except Exception:
            return None
        return None

    def play_pause(self):
        if self.current_player:
            msg = QtDBus.QDBusMessage.createMethodCall(
                self.current_player, "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.Player", "PlayPause"
            )
            self.bus.call(msg, QtDBus.QDBus.CallMode.NoBlock)
            QTimer.singleShot(80, self.poll_media)

    def next_track(self):
        if self.current_player:
            msg = QtDBus.QDBusMessage.createMethodCall(
                self.current_player, "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.Player", "Next"
            )
            self.bus.call(msg, QtDBus.QDBus.CallMode.NoBlock)
            QTimer.singleShot(120, self.poll_media)

    def prev_track(self):
        if self.current_player:
            msg = QtDBus.QDBusMessage.createMethodCall(
                self.current_player, "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.Player", "Previous"
            )
            self.bus.call(msg, QtDBus.QDBus.CallMode.NoBlock)
            QTimer.singleShot(120, self.poll_media)

# --- SYSTEM VOLUME HELPER ---
def get_volume():
    try:
        out = subprocess.check_output(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], timeout=1).decode()
        parts = out.strip().split()
        vol = float(parts[1]) if len(parts) > 1 else 0.0
        muted = "[MUTED]" in out
        return int(round(vol * 100)), muted
    except Exception:
        return 50, False

def change_volume(delta):
    try:
        sign = "+" if delta > 0 else "-"
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{abs(delta)}%{sign}"], timeout=1)
    except Exception:
        pass

# --- CAPS LOCK HELPER ---
def get_caps_lock_state():
    try:
        paths = glob.glob("/sys/class/leds/*capslock*/brightness")
        for p in paths:
            with open(p, "r") as f:
                val = f.read().strip()
                if val == "1":
                    return True
        return False
    except Exception:
        return False

# --- KWIN GLOBAL CURSOR TRACKER (FOR INTERACTIVE ROBOT MASCOT) ---
class KWinCursorTracker(QObject):
    def __init__(self):
        super().__init__()
        self.script_id = None
        self.script_file = None
        self.setup_kwin_script()

    def setup_kwin_script(self):
        try:
            try:
                subprocess.run([
                    "qdbus6", "org.kde.KWin", "/Scripting",
                    "org.kde.kwin.Scripting.unloadScript", "ixsland_cursor"
                ], stderr=subprocess.DEVNULL, timeout=1)
            except Exception:
                pass

            code = """
            var lastSent = 0;
            workspace.cursorPosChanged.connect(function() {
                var now = Date.now();
                if (now - lastSent > 35) {
                    lastSent = now;
                    callDBus('org.ixsland.Island', '/Island', '', 'setCursor', Math.round(workspace.cursorPos.x), Math.round(workspace.cursorPos.y));
                }
            });
            callDBus('org.ixsland.Island', '/Island', '', 'setCursor', Math.round(workspace.cursorPos.x), Math.round(workspace.cursorPos.y));
            """
            f = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False)
            f.write(code)
            f.flush()
            self.script_file = f.name

            out = subprocess.check_output([
                "qdbus6", "org.kde.KWin", "/Scripting",
                "org.kde.kwin.Scripting.loadScript", self.script_file, "ixsland_cursor"
            ], timeout=2).decode().strip()
            self.script_id = out
            subprocess.run([
                "qdbus6", "org.kde.KWin", f"/Scripting/Script{out}", "org.kde.kwin.Script.run"
            ], timeout=2)
        except Exception:
            pass

    def cleanup(self):
        try:
            if self.script_id:
                subprocess.run(["qdbus6", "org.kde.KWin", f"/Scripting/Script{self.script_id}", "org.kde.kwin.Script.stop"], timeout=1)
            subprocess.run(["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript", "ixsland_cursor"], timeout=1)
        except Exception:
            pass
        if self.script_file and os.path.exists(self.script_file):
            try:
                os.unlink(self.script_file)
            except Exception:
                pass


# --- MAIN DYNAMIC ISLAND WIDGET ---
class IxslandWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.mode = "IDLE"
        self.prev_mode = "IDLE"
        
        # Dimensions inside canvas
        self.curr_pill_w = 200
        self.curr_pill_h = 36
        self.target_pill_w = 200
        self.target_pill_h = 36
        
        # PERMANENT ANCHOR: Top margin inside fixed canvas is always 6
        self.pill_y = 6
        
        # Subsystems
        self.media_ctrl = MediaController()
        self.media_ctrl.mediaChanged.connect(self.on_media_changed)
        self.media_info = self.media_ctrl.current_info
        
        self.vol_percent, self.vol_muted = get_volume()
        self.display_vol = float(self.vol_percent)
        self.last_known_vol = self.vol_percent
        self.last_known_mute = self.vol_muted
        self.vol_anim = None
        
        self.caps_lock_state = get_caps_lock_state()
        self.last_caps_state = self.caps_lock_state
        
        self.prayer_times = calculate_prayer_times(
            self.cfg["latitude"], self.cfg["longitude"], self.cfg["timezone"]
        )
        self.last_announced_prayer = None
        
        # Cursor & Robot Mascot State
        self.cursor_x = 2460
        self.cursor_y = 500
        self.curr_gaze_x = 0.0
        self.curr_gaze_y = 0.0
        self.last_cursor_move_time = time.time()
        
        # D-Bus IPC & KWin Integration
        self.bus = QtDBus.QDBusConnection.sessionBus()
        self.bus.registerService("org.ixsland.Island")
        self.bus.registerObject("/Island", self, QtDBus.QDBusConnection.RegisterOption.ExportAllSlots)
        self.cursor_tracker = KWinCursorTracker()
        
        # Notification System
        self.last_notif_id = None
        self.active_notif = {"app": "", "summary": "", "body": ""}
        
        # Animation & Timers
        self.anim = None
        self.eq_bars = [4, 8, 12, 6]
        
        self.eq_timer = QTimer(self)
        self.eq_timer.timeout.connect(self.animate_eq)
        self.eq_timer.start(120)
        
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.on_tick_1s)
        self.clock_timer.start(1000)
        self.idle_view_counter = 0
        
        # Smooth Mascot Gaze & Blinking Engine (25 FPS)
        self.mascot_timer = QTimer(self)
        self.mascot_timer.timeout.connect(self.on_mascot_tick)
        self.mascot_timer.start(40)
        
        # Hardware Poller (Caps Lock, Volume keys, Notifications)
        self.hw_timer = QTimer(self)
        self.hw_timer.timeout.connect(self.poll_hardware_state)
        self.hw_timer.start(120)
        
        # Transient OSD / Notif Revert Timer
        self.revert_timer = QTimer(self)
        self.revert_timer.setSingleShot(True)
        self.revert_timer.timeout.connect(self.revert_transient_mode)
        
        # Auto-Collapse on Mouse Leave (Expanded Area)
        self.expanded_at = 0.0
        self.auto_collapse_timer = QTimer(self)
        self.auto_collapse_timer.setSingleShot(True)
        self.auto_collapse_timer.timeout.connect(self.check_and_collapse_expanded)
        
        # Window Flags & Fixed Size
        self.setObjectName("ixsland")
        self.setWindowTitle("ixsland Dynamic Island")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        self.init_placement()
        self.update_mask_for_mode()
        self.show()

    def get_target_screen(self):
        screens = QApplication.screens()
        target = self.cfg.get("target_screen", "primary")
        if target and target.lower() not in ("primary", "main", "default"):
            for s in screens:
                if s.name() == target:
                    return s
        primary = QApplication.primaryScreen()
        return primary if primary else (screens[0] if screens else None)

    def init_placement(self):
        s = self.get_target_screen()
        geom = s.geometry() if s else QRect(0, 0, 1920, 1080)
        
        self.winId()
        if self.windowHandle() and s:
            self.windowHandle().setScreen(s)
            
        canvas_x = geom.x() + (geom.width() - CANVAS_W) // 2
        canvas_y = geom.y() + self.cfg.get("top_margin", 16)
        
        # FIXED CANVAS SIZE: Never resize window to keep KWin Wayland position permanent
        self.setGeometry(canvas_x, canvas_y, CANVAS_W, CANVAS_H)
        self.setFixedSize(CANVAS_W, CANVAS_H)

    def update_mask_for_mode(self):
        # FIX FOR HORIZONTAL CLIPPING:
        # Full horizontal width (rx=0, rw=CANVAS_W=380) ensures pill is NEVER clipped horizontally!
        if self.mode == "EXPANDED_MEDIA":
            self.clearMask()
        else:
            # Allows clicks below y=52 to pass straight through while protecting full pill width
            self.setMask(QRegion(QRect(0, 0, CANVAS_W, 54)))

    def update_mode_targets(self):
        if self.mode == "IDLE":
            self.target_pill_w, self.target_pill_h = 200, 36
        elif self.mode == "COMPACT_MEDIA":
            self.target_pill_w, self.target_pill_h = 340, 40
        elif self.mode == "OSD_VOLUME":
            self.target_pill_w, self.target_pill_h = 260, 38
        elif self.mode == "CAPS_OSD":
            self.target_pill_w, self.target_pill_h = 230, 38
        elif self.mode == "NOTIFICATION":
            self.target_pill_w, self.target_pill_h = 360, 56
        elif self.mode == "PRAYER_ALERT":
            self.target_pill_w, self.target_pill_h = 360, 52
        elif self.mode == "EXPANDED_MEDIA":
            self.target_pill_w, self.target_pill_h = 380, 156

        self.start_morph_animation()

    def start_morph_animation(self):
        if self.anim and self.anim.state() == QVariantAnimation.State.Running:
            self.anim.stop()

        start_w, start_h = self.curr_pill_w, self.curr_pill_h
        end_w, end_h = self.target_pill_w, self.target_pill_h

        # Clear mask during animation to eliminate any clip artifacts
        self.clearMask()

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)

        def step(progress):
            self.curr_pill_w = int(round(start_w + (end_w - start_w) * progress))
            self.curr_pill_h = int(round(start_h + (end_h - start_h) * progress))
            self.update()

        def on_finished():
            self.curr_pill_w = end_w
            self.curr_pill_h = end_h
            self.update_mask_for_mode()
            self.update()

        self.anim.valueChanged.connect(step)
        self.anim.finished.connect(on_finished)
        self.anim.start()

    def is_cursor_inside_expanded(self):
        if self.mode != "EXPANDED_MEDIA":
            return False
        cw = self.geometry().x()
        cy = self.geometry().y()
        pill_w = self.target_pill_w
        pill_h = self.target_pill_h
        pill_x = cw + (CANVAS_W - pill_w) // 2
        pill_y = cy + int(self.pill_y)
        rect = QRect(pill_x - 8, pill_y - 8, pill_w + 16, pill_h + 16)
        return rect.contains(self.cursor_x, self.cursor_y)

    def check_and_collapse_expanded(self):
        if self.mode == "EXPANDED_MEDIA":
            if not self.is_cursor_inside_expanded():
                self.collapse_to_base_mode()

    def collapse_to_base_mode(self):
        if self.auto_collapse_timer.isActive():
            self.auto_collapse_timer.stop()
        if self.media_info.get("status") == "Playing":
            self.mode = "COMPACT_MEDIA"
        else:
            self.mode = "IDLE"
        self.update_mode_targets()

    @pyqtSlot(int, int)
    def setCursor(self, x, y):
        self.on_global_cursor_moved(x, y)

    @pyqtSlot(str)
    def triggerPrayer(self, name):
        self.trigger_prayer_alert(name)

    @pyqtSlot(str, str, str)
    def triggerNotification(self, app, summary, body):
        self.trigger_notification(app, summary, body)

    @pyqtSlot(int, bool)
    def triggerVolume(self, percent, muted):
        self.trigger_volume_osd(percent, muted)

    @pyqtSlot(bool)
    def triggerCaps(self, on):
        self.caps_lock_state = on
        self.last_caps_state = on
        self.trigger_caps_osd(on)

    @pyqtSlot()
    def triggerExpand(self):
        self.mode = "EXPANDED_MEDIA"
        self.expanded_at = time.time()
        self.update_mode_targets()

    @pyqtSlot()
    def triggerCollapse(self):
        self.collapse_to_base_mode()

    @pyqtSlot(int)
    def triggerIdlePhase(self, phase):
        self.mode = "IDLE"
        self.idle_view_counter = phase * 5
        self.update_mode_targets()
        self.update()

    @pyqtSlot(bool)
    def triggerMascotSleep(self, sleep):
        if sleep:
            self.last_cursor_move_time = time.time() - 30.0
        else:
            self.last_cursor_move_time = time.time()
        self.update()

    def on_global_cursor_moved(self, x, y):
        if abs(self.cursor_x - x) > 2 or abs(self.cursor_y - y) > 2:
            self.cursor_x = x
            self.cursor_y = y
            self.last_cursor_move_time = time.time()
            
            # Auto-collapse expanded island when mouse leaves area
            if self.mode == "EXPANDED_MEDIA" and (time.time() - self.expanded_at > 0.3):
                if not self.is_cursor_inside_expanded():
                    if not self.auto_collapse_timer.isActive():
                        self.auto_collapse_timer.start(120)
                else:
                    if self.auto_collapse_timer.isActive():
                        self.auto_collapse_timer.stop()

    def mouseMoveEvent(self, event):
        gpos = event.globalPosition()
        self.on_global_cursor_moved(int(gpos.x()), int(gpos.y()))
        
        # Local widget check for fast response inside canvas
        if self.mode == "EXPANDED_MEDIA" and (time.time() - self.expanded_at > 0.3):
            pill_x = (CANVAS_W - self.target_pill_w) // 2
            pill_y = int(self.pill_y)
            rect = QRect(pill_x - 8, pill_y - 8, self.target_pill_w + 16, self.target_pill_h + 16)
            if not rect.contains(event.position().toPoint()):
                if not self.auto_collapse_timer.isActive():
                    self.auto_collapse_timer.start(120)
            else:
                if self.auto_collapse_timer.isActive():
                    self.auto_collapse_timer.stop()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self.mode == "EXPANDED_MEDIA" and (time.time() - self.expanded_at > 0.3):
            if not self.auto_collapse_timer.isActive():
                self.auto_collapse_timer.start(100)
        super().leaveEvent(event)

    def enterEvent(self, event):
        if self.mode == "EXPANDED_MEDIA":
            if self.auto_collapse_timer.isActive():
                self.auto_collapse_timer.stop()
        super().enterEvent(event)

    def on_mascot_tick(self):
        if self.mode == "IDLE":
            phase = (self.idle_view_counter // 5) % 3
            if phase == 2:
                # Calculate gaze towards cursor
                island_cx = self.geometry().x() + (CANVAS_W / 2.0)
                island_cy = self.geometry().y() + self.pill_y + (self.curr_pill_h / 2.0)
                
                dx = self.cursor_x - island_cx
                dy = self.cursor_y - island_cy
                
                target_gx = math.tanh(dx / 350.0)
                target_gy = math.tanh(dy / 400.0)
                
                # Smooth interpolation (Pixar-like gaze follow)
                self.curr_gaze_x += (target_gx - self.curr_gaze_x) * 0.28
                self.curr_gaze_y += (target_gy - self.curr_gaze_y) * 0.28
                self.update()

    def on_media_changed(self, info):
        self.media_info = info
        if self.mode not in ("OSD_VOLUME", "CAPS_OSD", "NOTIFICATION", "PRAYER_ALERT", "EXPANDED_MEDIA"):
            if info["status"] == "Playing":
                if self.mode != "COMPACT_MEDIA":
                    self.mode = "COMPACT_MEDIA"
                    self.update_mode_targets()
            else:
                if self.mode != "IDLE":
                    self.mode = "IDLE"
                    self.update_mode_targets()
        self.update()

    def animate_eq(self):
        if self.mode in ("COMPACT_MEDIA", "EXPANDED_MEDIA") and self.media_info.get("status") == "Playing":
            import random
            self.eq_bars = [
                random.randint(4, 18),
                random.randint(6, 20),
                random.randint(3, 16),
                random.randint(5, 19)
            ]
            self.update()

    def on_tick_1s(self):
        self.idle_view_counter += 1
        now = datetime.now()
        now_mins = now.hour * 60 + now.minute
        
        # Check prayer time arrival
        for name, t_str, t_mins in self.prayer_times:
            if t_mins == now_mins and self.last_announced_prayer != name:
                self.last_announced_prayer = name
                self.trigger_prayer_alert(name)
                break
                
        if self.mode in ("IDLE", "EXPANDED_MEDIA", "COMPACT_MEDIA"):
            if self.mode == "EXPANDED_MEDIA":
                self.media_ctrl.poll_media()
            self.update()

    def poll_hardware_state(self):
        # 1. Caps Lock Check
        caps = get_caps_lock_state()
        if caps != self.last_caps_state:
            self.last_caps_state = caps
            self.caps_lock_state = caps
            self.trigger_caps_osd(caps)
            return

        # 2. System Volume Keys Check (External changes)
        vol, muted = get_volume()
        if vol != self.last_known_vol or muted != self.last_known_mute:
            self.last_known_vol = vol
            self.last_known_mute = muted
            self.trigger_volume_osd(vol, muted)
            return

        # 3. Notification Check from /tmp/macos-notifications-history.json
        if os.path.exists(NOTIF_FILE):
            try:
                with open(NOTIF_FILE, "r") as f:
                    notifs = json.load(f)
                    if notifs and isinstance(notifs, list):
                        latest = notifs[0]
                        notif_id = latest.get("id")
                        if self.last_notif_id is None:
                            self.last_notif_id = notif_id
                        elif notif_id != self.last_notif_id:
                            self.last_notif_id = notif_id
                            self.trigger_notification(
                                latest.get("app", "Notification"),
                                latest.get("summary", ""),
                                latest.get("body", "")
                            )
            except Exception:
                pass

    # --- OSD TRIGGERS ---
    def trigger_volume_osd(self, target_vol=None, target_muted=None):
        if target_vol is not None:
            self.vol_percent = target_vol
            self.vol_muted = target_muted if target_muted is not None else False
        else:
            self.vol_percent, self.vol_muted = get_volume()
            
        self.last_known_vol = self.vol_percent
        self.last_known_mute = self.vol_muted

        # Fluid volume animation
        if self.vol_anim and self.vol_anim.state() == QVariantAnimation.State.Running:
            self.vol_anim.stop()

        start_v = float(self.display_vol)
        end_v = float(self.vol_percent)

        self.vol_anim = QVariantAnimation(self)
        self.vol_anim.setDuration(160)
        self.vol_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.vol_anim.setStartValue(start_v)
        self.vol_anim.setEndValue(end_v)

        def on_vol_step(val):
            self.display_vol = float(val)
            if self.mode == "OSD_VOLUME":
                self.update()

        def on_vol_end():
            self.display_vol = end_v
            if self.mode == "OSD_VOLUME":
                self.update()

        self.vol_anim.valueChanged.connect(on_vol_step)
        self.vol_anim.finished.connect(on_vol_end)
        self.vol_anim.start()

        if self.mode != "OSD_VOLUME":
            if self.mode not in ("CAPS_OSD", "NOTIFICATION", "PRAYER_ALERT"):
                self.prev_mode = self.mode
            self.mode = "OSD_VOLUME"
            self.update_mode_targets()
        else:
            self.update()
        self.revert_timer.start(2200)

    def trigger_caps_osd(self, state):
        if self.mode != "CAPS_OSD":
            if self.mode not in ("OSD_VOLUME", "NOTIFICATION", "PRAYER_ALERT"):
                self.prev_mode = self.mode
            self.mode = "CAPS_OSD"
            self.update_mode_targets()
        else:
            self.update()
        self.revert_timer.start(1800)

    def trigger_notification(self, app_name, summary, body):
        self.active_notif = {"app": app_name, "summary": summary, "body": body}
        if self.mode not in ("OSD_VOLUME", "CAPS_OSD", "PRAYER_ALERT"):
            self.prev_mode = self.mode
        self.mode = "NOTIFICATION"
        self.update_mode_targets()
        self.revert_timer.start(4500)

    def trigger_prayer_alert(self, prayer_name):
        self.active_prayer_alert = prayer_name
        self.prev_mode = self.mode
        self.mode = "PRAYER_ALERT"
        self.update_mode_targets()
        
        if self.cfg.get("pause_music_on_adzan", True):
            if self.media_info.get("status") == "Playing":
                self.media_ctrl.play_pause()
                
        try:
            sound_file = "/usr/share/sounds/freedesktop/stereo/complete.oga"
            if os.path.exists(sound_file):
                subprocess.Popen(["paplay", sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
            
        self.revert_timer.start(8000)

    def revert_transient_mode(self):
        self.collapse_to_base_mode()

    # --- INPUT EVENTS ---
    def wheelEvent(self, event):
        delta = 3 if event.angleDelta().y() > 0 else -3
        change_volume(delta)
        new_v = max(0, min(150, self.vol_percent + delta))
        self.trigger_volume_osd(new_v, False)

    def mousePressEvent(self, event):
        pos = event.position()
        pill_x = (CANVAS_W - self.curr_pill_w) // 2
        pill_y = self.pill_y
        
        inside_pill = (
            pill_x <= pos.x() <= pill_x + self.curr_pill_w and
            pill_y <= pos.y() <= pill_y + self.curr_pill_h
        )

        if event.button() == Qt.MouseButton.LeftButton:
            if self.mode == "EXPANDED_MEDIA":
                # Close button on top-right of pill (✕)
                close_rect = QRect(int(pill_x + self.curr_pill_w - 36), int(pill_y), 36, 36)
                if close_rect.contains(pos.toPoint()) or not inside_pill:
                    self.collapse_to_base_mode()
                    return

                # Progress bar Seek
                bar_x = pill_x + 18
                bar_y = pill_y + 86
                bar_w = int(self.curr_pill_w - 36)
                if bar_x - 6 <= pos.x() <= bar_x + bar_w + 6 and bar_y - 8 <= pos.y() <= bar_y + 16:
                    length = self.media_info.get("length", 0)
                    if length > 0:
                        click_ratio = max(0.0, min(1.0, (pos.x() - bar_x) / float(bar_w)))
                        target_sec = click_ratio * length
                        self.media_ctrl.seek(target_sec)
                        return

                # Controls row: Previous / Play-Pause / Next
                ctrl_top = pill_y + 104
                ctrl_bot = pill_y + 146
                if ctrl_top <= pos.y() <= ctrl_bot:
                    mid_x = CANVAS_W // 2
                    if mid_x - 60 <= pos.x() <= mid_x - 20:
                        self.media_ctrl.prev_track()
                        return
                    elif mid_x - 20 <= pos.x() <= mid_x + 20:
                        self.media_ctrl.play_pause()
                        return
                    elif mid_x + 20 <= pos.x() <= mid_x + 60:
                        self.media_ctrl.next_track()
                        return
                
                # Clicking elsewhere inside stays open (mouse exit handles auto-collapse)
                return

            # Non-expanded modes
            if inside_pill:
                if self.mode in ("IDLE", "COMPACT_MEDIA", "NOTIFICATION"):
                    self.mode = "EXPANDED_MEDIA"
                    self.expanded_at = time.time()
                    self.update_mode_targets()
                elif self.mode in ("OSD_VOLUME", "CAPS_OSD", "PRAYER_ALERT"):
                    self.revert_timer.stop()
                    self.collapse_to_base_mode()

        elif event.button() == Qt.MouseButton.MiddleButton:
            self.media_ctrl.play_pause()
        elif event.button() == Qt.MouseButton.RightButton:
            if inside_pill:
                self.show_context_menu(event.globalPosition().toPoint())

    def show_context_menu(self, point):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a1e;
                color: #e0e0e0;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #007acc;
                color: white;
            }
        """)
        
        act_toggle = QAction("Play / Pause Musik", self)
        act_toggle.triggered.connect(self.media_ctrl.play_pause)
        menu.addAction(act_toggle)
        
        act_spec = QAction("Ambil Screenshot (Spectacle)", self)
        act_spec.triggered.connect(lambda: subprocess.Popen(["spectacle", "-r"]))
        menu.addAction(act_spec)
        
        menu.addSeparator()
        act_quit = QAction("Tutup ixsland", self)
        act_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_quit)
        
        menu.exec(point)

    # --- PAINT ENGINE ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        pill_w = self.curr_pill_w
        pill_h = self.curr_pill_h
        pill_x = (CANVAS_W - pill_w) / 2.0
        
        # PERMANENT TOP ANCHOR: Always 6.0 inside fixed canvas
        pill_y = self.pill_y
        radius = pill_h / 2.0 if self.mode != "EXPANDED_MEDIA" else 22.0

        # Background Pill Glass
        path = QPainterPath()
        path.addRoundedRect(QRectF(pill_x, pill_y, pill_w, pill_h), radius, radius)
        
        painter.fillPath(path, QBrush(QColor(12, 12, 14, 250)))
        
        # Border highlight
        border_col = QColor(255, 255, 255, 34)
        if self.mode == "CAPS_OSD" and self.caps_lock_state:
            border_col = QColor(255, 179, 0, 180)
        elif self.mode == "NOTIFICATION":
            border_col = QColor(0, 230, 118, 140)
        elif self.mode == "PRAYER_ALERT":
            border_col = QColor(0, 180, 216, 200)
            
        painter.strokePath(path, QPen(border_col, 1.2))

        # Draw Content inside pill coordinate space
        painter.save()
        painter.translate(pill_x, pill_y)
        
        if self.mode == "IDLE":
            self.paint_idle(painter, pill_w, pill_h)
        elif self.mode == "COMPACT_MEDIA":
            self.paint_compact_media(painter, pill_w, pill_h)
        elif self.mode == "EXPANDED_MEDIA":
            self.paint_expanded_media(painter, pill_w, pill_h)
        elif self.mode == "OSD_VOLUME":
            self.paint_osd_volume(painter, pill_w, pill_h)
        elif self.mode == "CAPS_OSD":
            self.paint_caps_osd(painter, pill_w, pill_h)
        elif self.mode == "NOTIFICATION":
            self.paint_notification(painter, pill_w, pill_h)
        elif self.mode == "PRAYER_ALERT":
            self.paint_prayer_alert(painter, pill_w, pill_h)
            
        painter.restore()

    def paint_idle(self, p, w, h):
        now = datetime.now()
        # 3-Phase Rotation: 0 = Time, 1 = Prayer, 2 = Interactive Mascot
        phase = (self.idle_view_counter // 5) % 3
        
        # Green status indicator dot
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 230, 118, 220)))
        p.drawEllipse(QPoint(16, int(h // 2)), 4, 4)

        if phase == 0:
            # Digital Clock
            p.setFont(QFont("Cantarell", 10, QFont.Weight.Bold))
            p.setPen(QColor(245, 245, 245))
            rect = QRect(26, 0, int(w - 36), int(h))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, now.strftime("%H:%M:%S"))
        elif phase == 1:
            # Prayer Schedule
            now_mins = now.hour * 60 + now.minute
            next_prayer_name = "Subuh"
            next_prayer_time = "04:30"
            for name, t_str, t_mins in self.prayer_times:
                if t_mins > now_mins:
                    next_prayer_name = name
                    next_prayer_time = t_str
                    break
            p.setFont(QFont("Cantarell", 10, QFont.Weight.Bold))
            p.setPen(QColor(245, 245, 245))
            rect = QRect(26, 0, int(w - 36), int(h))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"🕌 {next_prayer_name} {next_prayer_time}")
        else:
            # Interactive Robot Mascot (Gaze & Mouth follow cursor)
            self.paint_mascot(p, w, h)

    def paint_mascot(self, p, w, h):
        mid_x = w / 2.0
        mid_y = h / 2.0
        
        # Check hover proximity
        island_cx = self.geometry().x() + (CANVAS_W / 2.0)
        island_cy = self.geometry().y() + self.pill_y + (h / 2.0)
        dist = math.hypot(self.cursor_x - island_cx, self.cursor_y - island_cy)
        is_hover = dist < 95.0
        
        # Inactivity Sleep Check
        now = time.time()
        is_sleeping = (now - self.last_cursor_move_time) > 22.0
        
        # Natural Blink Engine (every 3.8s for 160ms)
        blink_cycle = (now % 3.8)
        is_blinking = blink_cycle < 0.16 and not is_sleeping and not is_hover

        eye_spacing = 17.0
        left_eye_x = mid_x - eye_spacing
        right_eye_x = mid_x + eye_spacing
        eye_y = mid_y - 2.0
        
        gx = self.curr_gaze_x
        gy = self.curr_gaze_y

        if is_sleeping:
            # Sleep state: eyes closed with floating zzZ
            p.setPen(QPen(QColor(0, 229, 255, 200), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for ex in (left_eye_x, right_eye_x):
                p.drawLine(QPointF(ex - 5, eye_y + 1), QPointF(ex + 5, eye_y + 1))
            # Resting mouth
            p.setPen(QPen(QColor(255, 255, 255, 180), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(mid_x - 3, eye_y + 8), QPointF(mid_x + 3, eye_y + 8))
            # zzZ text
            p.setFont(QFont("Cantarell", 8, QFont.Weight.Bold))
            p.setPen(QColor(0, 229, 255, 180))
            p.drawText(QRect(int(mid_x + 28), int(eye_y - 8), 30, 20), Qt.AlignmentFlag.AlignLeft, "zZ")
            return

        if is_hover:
            # Hover Happy Joy: squinting eyes (^  ^) + blush + wide smile
            p.setPen(QPen(QColor(0, 229, 255, 255), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for ex in (left_eye_x, right_eye_x):
                epath = QPainterPath()
                epath.moveTo(ex - 5.5, eye_y + 3)
                epath.quadTo(ex, eye_y - 4, ex + 5.5, eye_y + 3)
                p.drawPath(epath)
            
            # Pink Blush on Cheeks
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(255, 105, 180, 140)))
            p.drawEllipse(QPointF(left_eye_x - 8, eye_y + 5.5), 3.5, 2.2)
            p.drawEllipse(QPointF(right_eye_x + 8, eye_y + 5.5), 3.5, 2.2)
            
            # Wide smile
            p.setPen(QPen(QColor(255, 255, 255, 240), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            mpath = QPainterPath()
            mpath.moveTo(mid_x - 5.5, eye_y + 7.5)
            mpath.quadTo(mid_x, eye_y + 12.0, mid_x + 5.5, eye_y + 7.5)
            p.drawPath(mpath)
            return

        if is_blinking:
            # Quick blink: horizontal sleek lines
            p.setPen(QPen(QColor(0, 229, 255, 240), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for ex in (left_eye_x, right_eye_x):
                p.drawLine(QPointF(ex - 5, eye_y), QPointF(ex + 5, eye_y))
        else:
            # Active OLED Eyes tracking cursor gaze
            for ex in (left_eye_x, right_eye_x):
                # Outer glow aura
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(0, 229, 255, 60)))
                p.drawRoundedRect(QRectF(ex - 7, eye_y - 8, 14, 16), 5, 5)
                
                # Main Eye Capsule
                p.setBrush(QBrush(QColor(0, 229, 255, 240)))
                p.drawRoundedRect(QRectF(ex - 5.5, eye_y - 6.5, 11, 13), 4, 4)
                
                # Dynamic pupil shifted by gaze direction
                pupil_x = ex + (gx * 2.8)
                pupil_y = eye_y + (gy * 2.2)
                p.setBrush(QBrush(QColor(255, 255, 255, 255)))
                p.drawEllipse(QPointF(pupil_x, pupil_y), 3.0, 3.0)

        # Dynamic Mouth Expression tracking cursor
        mouth_x = mid_x + (gx * 2.2)
        mouth_y = eye_y + 8.5
        p.setPen(QPen(QColor(255, 255, 255, 230), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        
        mpath = QPainterPath()
        if gx < -0.3:
            # Curiously smirking towards left cursor
            mpath.moveTo(mouth_x - 4, mouth_y + 1.2)
            mpath.quadTo(mouth_x, mouth_y + 2.8, mouth_x + 4, mouth_y)
        elif gx > 0.3:
            # Curiously smirking towards right cursor
            mpath.moveTo(mouth_x - 4, mouth_y)
            mpath.quadTo(mouth_x, mouth_y + 2.8, mouth_x + 4, mouth_y + 1.2)
        else:
            # Gentle cute smile
            mpath.moveTo(mouth_x - 4, mouth_y)
            mpath.quadTo(mouth_x, mouth_y + 2.8, mouth_x + 4, mouth_y)
            
        p.drawPath(mpath)

    def paint_compact_media(self, p, w, h):
        art = self.media_info.get("art_pixmap")
        art_rect = QRectF(7, (h - 26) / 2.0, 26, 26)
        if art and not art.isNull():
            p.save()
            clip = QPainterPath()
            clip.addRoundedRect(art_rect, 6, 6)
            p.setClipPath(clip)
            p.drawPixmap(art_rect.toRect(), art)
            p.restore()
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(40, 40, 48)))
            p.drawRoundedRect(art_rect, 6, 6)
            p.setFont(QFont("Cantarell", 11))
            p.setPen(QColor(200, 200, 200))
            p.drawText(art_rect, Qt.AlignmentFlag.AlignCenter, "🎵")

        # Equalizer bars
        eq_right = w - 12
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(29, 185, 84)))
        for i, bar_h in enumerate(self.eq_bars):
            bx = eq_right - (4 - i) * 6
            by = (h - bar_h) / 2.0
            p.drawRoundedRect(QRectF(bx, by, 3.5, bar_h), 1.5, 1.5)

        title = self.media_info.get("title", "")
        artist = self.media_info.get("artist", "")
        text_rect_w = int(w - 42 - 34)
        
        p.setFont(QFont("Cantarell", 9, QFont.Weight.Bold))
        p.setPen(QColor(255, 255, 255))
        elided_title = p.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, text_rect_w)
        p.drawText(QRect(38, 4, text_rect_w, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)

        p.setFont(QFont("Cantarell", 8, QFont.Weight.Normal))
        p.setPen(QColor(160, 160, 165))
        elided_artist = p.fontMetrics().elidedText(artist, Qt.TextElideMode.ElideRight, text_rect_w)
        p.drawText(QRect(38, 20, text_rect_w, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_artist)

    def paint_expanded_media(self, p, w, h):
        title = self.media_info.get("title", "")
        artist = self.media_info.get("artist", "")
        player = self.media_info.get("player", "Media")
        status = self.media_info.get("status", "Stopped")
        art = self.media_info.get("art_pixmap")

        art_rect = QRectF(16, 16, 54, 54)
        if art and not art.isNull():
            p.save()
            clip = QPainterPath()
            clip.addRoundedRect(art_rect, 10, 10)
            p.setClipPath(clip)
            p.drawPixmap(art_rect.toRect(), art)
            p.restore()
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(36, 36, 44)))
            p.drawRoundedRect(art_rect, 10, 10)
            p.setFont(QFont("Cantarell", 18))
            p.setPen(QColor(220, 220, 220))
            p.drawText(art_rect, Qt.AlignmentFlag.AlignCenter, "🎵")

        # Top-Right Close Button (✕)
        p.setFont(QFont("Cantarell", 11, QFont.Weight.Bold))
        p.setPen(QColor(160, 160, 170))
        p.drawText(QRect(int(w - 32), 12, 20, 20), Qt.AlignmentFlag.AlignCenter, "✕")

        info_x = 80
        info_w = int(w - info_x - 36)
        p.setFont(QFont("Cantarell", 11, QFont.Weight.Bold))
        p.setPen(QColor(255, 255, 255))
        elided_title = p.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, info_w)
        p.drawText(QRect(info_x, 18, info_w, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)

        p.setFont(QFont("Cantarell", 9, QFont.Weight.Normal))
        p.setPen(QColor(170, 170, 175))
        elided_artist = p.fontMetrics().elidedText(artist, Qt.TextElideMode.ElideRight, info_w)
        p.drawText(QRect(info_x, 38, info_w, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_artist)

        p.setFont(QFont("Cantarell", 8, QFont.Weight.Bold))
        p.setPen(QColor(0, 180, 216))
        p.drawText(QRect(info_x, 56, info_w, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, player.upper())

        # Progress Line
        pos = int(self.media_info.get("position", 0))
        length = int(self.media_info.get("length", 0))
        ratio = min(1.0, max(0.0, pos / float(length))) if length > 0 else 0.0

        bar_x = 18
        bar_y = 86
        bar_w = int(w - 36)
        bar_h = 5
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 40)))
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 2.5, 2.5)
        if ratio > 0:
            fill_w = max(4.0, bar_w * ratio)
            p.setBrush(QBrush(QColor(0, 212, 255)))
            p.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 2.5, 2.5)

        p.setFont(QFont("Cantarell", 8, QFont.Weight.Medium))
        p.setPen(QColor(170, 170, 175))
        pos_str = f"{pos // 60}:{pos % 60:02d}"
        len_str = f"{length // 60}:{length % 60:02d}" if length > 0 else "--:--"
        p.drawText(QRect(bar_x, bar_y + 7, 50, 14), Qt.AlignmentFlag.AlignLeft, pos_str)
        p.drawText(QRect(bar_x + bar_w - 50, bar_y + 7, 50, 14), Qt.AlignmentFlag.AlignRight, len_str)

        # Controls
        mid_x = int(w // 2)
        ctrl_y = 108
        
        p.setFont(QFont("Cantarell", 14, QFont.Weight.Bold))
        p.setPen(QColor(220, 220, 225))
        p.drawText(QRect(mid_x - 55, ctrl_y, 30, 30), Qt.AlignmentFlag.AlignCenter, "⏮")
        
        play_icon = "⏸" if status == "Playing" else "▶"
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 30)))
        p.drawEllipse(QPoint(mid_x, ctrl_y + 15), 18, 18)
        p.setFont(QFont("Cantarell", 13, QFont.Weight.Bold))
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRect(mid_x - 15, ctrl_y, 30, 30), Qt.AlignmentFlag.AlignCenter, play_icon)
        
        p.setFont(QFont("Cantarell", 14, QFont.Weight.Bold))
        p.setPen(QColor(220, 220, 225))
        p.drawText(QRect(mid_x + 25, ctrl_y, 30, 30), Qt.AlignmentFlag.AlignCenter, "⏭")

    def paint_osd_volume(self, p, w, h):
        vol_int = int(round(self.display_vol))
        if self.vol_muted or vol_int == 0:
            icon = "🔇"
        elif vol_int <= 33:
            icon = "🔈"
        elif vol_int <= 66:
            icon = "🔉"
        else:
            icon = "🔊"
            
        p.setFont(QFont("Cantarell", 12))
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRect(12, 0, 24, int(h)), Qt.AlignmentFlag.AlignCenter, icon)

        bar_x = 42
        bar_y = (h - 6) / 2.0
        bar_w = int(w - 42 - 50)
        bar_h = 6

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 45)))
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 3, 3)

        max_v = 150.0 if self.display_vol > 100.0 else 100.0
        ratio = min(1.0, max(0.0, self.display_vol / max_v))
        if ratio > 0 and not self.vol_muted:
            fill_w = max(4.0, bar_w * ratio)
            bar_color = QColor(0, 212, 255) if self.display_vol <= 100.0 else QColor(255, 179, 0)
            p.setBrush(QBrush(bar_color))
            p.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 3, 3)

        text = "Mute" if self.vol_muted else f"{vol_int}%"
        p.setFont(QFont("Cantarell", 9, QFont.Weight.Bold))
        p.setPen(QColor(240, 240, 240))
        p.drawText(QRect(int(w - 46), 0, 40, int(h)), Qt.AlignmentFlag.AlignCenter, text)

    def paint_caps_osd(self, p, w, h):
        is_on = self.caps_lock_state
        icon = "🔠" if is_on else "🔤"
        text = "CAPS LOCK ON" if is_on else "CAPS LOCK OFF"
        color = QColor(255, 183, 77) if is_on else QColor(180, 180, 185)
        
        p.setFont(QFont("Cantarell", 11))
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRect(14, 0, 24, int(h)), Qt.AlignmentFlag.AlignCenter, icon)
        
        p.setFont(QFont("Cantarell", 9, QFont.Weight.Bold))
        p.setPen(color)
        p.drawText(QRect(42, 0, int(w - 48), int(h)), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

    def paint_notification(self, p, w, h):
        app = self.active_notif.get("app", "Notification")
        summary = self.active_notif.get("summary", "")
        body = self.active_notif.get("body", "")
        
        p.setFont(QFont("Cantarell", 8, QFont.Weight.Bold))
        p.setPen(QColor(0, 230, 118))
        header = f"💬 {app.upper()}"
        if summary:
            header += f" · {summary}"
        elided_header = p.fontMetrics().elidedText(header, Qt.TextElideMode.ElideRight, int(w - 28))
        p.drawText(QRect(14, 8, int(w - 28), 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_header)

        p.setFont(QFont("Cantarell", 8, QFont.Weight.Normal))
        p.setPen(QColor(240, 240, 245))
        elided_body = p.fontMetrics().elidedText(body if body else "(Pesan baru)", Qt.TextElideMode.ElideRight, int(w - 28))
        p.drawText(QRect(14, 26, int(w - 28), 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_body)

    def paint_prayer_alert(self, p, w, h):
        name = getattr(self, "active_prayer_alert", "Sholat")
        p.setFont(QFont("Cantarell", 9, QFont.Weight.Bold))
        p.setPen(QColor(0, 212, 255))
        p.drawText(QRect(14, 6, int(w - 28), 18), Qt.AlignmentFlag.AlignCenter, f"🕌 WAKTU {name.upper()} TELAH TIBA")
        
        p.setFont(QFont("Cantarell", 8, QFont.Weight.Normal))
        p.setPen(QColor(220, 220, 225))
        p.drawText(QRect(14, 26, int(w - 28), 16), Qt.AlignmentFlag.AlignCenter, "Mari tunaikan sholat tepat waktu")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ixsland")
    island = IxslandWidget()
    
    def on_exit():
        island.cursor_tracker.cleanup()
    app.aboutToQuit.connect(on_exit)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
