#!/usr/bin/env python3
"""
ixsland Dynamic Island for Windows 10 & 11
Ported directly from Linux Wayland (ixsland.py) with 100% Visual & Feature Parity:
- Top-Anchored Fluid Morphing Dynamic Island (380x175 Canvas)
- Interactive Eye-Tracking Robot Mascot (Blinks, Gaze Tracking, Sleep & Hover Joy)
- Windows CoreAudio Volume OSD (PyCaw) with Overboost
- Hardware Caps Lock OSD (Win32 API)
- Windows WinRT GSMTC Media Hub with Zero-Blink Seekbar & Looping Marquee
- 100% Offline Astronomical Prayer Engine (Subuh, Dzuhur, Ashar, Maghrib, Isya)
- Extra Feature 1: Minimize / Hide Dynamic Island (Top Notch Trigger & Tray)
- Extra Feature 2: Sleek Fluent UI Settings GUI (Pengaturan Lengkap)
- TCP IPC Server on 127.0.0.1:49281 for Demonstrations & Extensibility
"""

import sys
import os
import math
import time
import json
import glob
import tempfile
import urllib.request
import threading
import socket
import queue
from datetime import datetime, date

from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QRect, QRectF, QSize, QPointF,
    QVariantAnimation, QEasingCurve, pyqtSignal, pyqtSlot, QObject, QThread
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGraphicsDropShadowEffect, QMenu, QSystemTrayIcon,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QComboBox, QCheckBox,
    QPushButton, QTabWidget, QGroupBox, QMessageBox
)
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPainterPath,
    QFont, QPixmap, QAction, QRegion, QIcon, QCursor
)
from PyQt6.QtNetwork import QTcpServer, QHostAddress

# --- TOP-LEVEL WINDOWS AUDIO IMPORT ---
if sys.platform == "win32":
    try:
        import comtypes
        from pycaw.pycaw import AudioUtilities
    except Exception:
        pass

# --- DIRECTORY CONFIGURATION ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(APP_DIR, "assets")

if sys.platform == "win32":
    CONFIG_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ixsland")
    CACHE_DIR = os.path.join(tempfile.gettempdir(), "ixsland_cache")
else:
    CONFIG_DIR = os.path.expanduser("~/.local/share/ixsland")
    CACHE_DIR = "/tmp/ixsland_cache"

CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# Fixed Canvas Geometry (Identical to Linux Anchor)
CANVAS_W = 380
CANVAS_H = 175
IPC_PORT = 49281

CITY_COORDINATES = {
    "Jakarta (WIB)": (-6.2088, 106.8456, 7.0),
    "Surabaya (WIB)": (-7.2575, 112.7521, 7.0),
    "Bandung (WIB)": (-6.9175, 107.6191, 7.0),
    "Semarang (WIB)": (-6.9667, 110.4167, 7.0),
    "Yogyakarta (WIB)": (-7.7956, 110.3695, 7.0),
    "Medan (WIB)": (3.5952, 98.6722, 7.0),
    "Makassar (WITA)": (-5.1477, 119.4327, 8.0),
    "Denpasar (WITA)": (-8.6705, 115.2126, 8.0),
    "Jayapura (WIT)": (-2.5337, 140.7181, 9.0)
}

DEFAULT_CONFIG = {
    "target_screen": "primary",
    "top_margin": 12,
    "scale": 1.0,
    "bg_opacity": 98,
    "enable_mascot": True,
    "enable_marquee": True,
    "city": "Jakarta (WIB)",
    "latitude": -6.2088,
    "longitude": 106.8456,
    "timezone": 7.0,
    "pause_music_on_adzan": True,
    "autostart": True
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception:
        pass

# --- OFFLINE ASTRONOMICAL PRAYER TIMES ENGINE ---
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

# --- WINDOWS HARDWARE INTEROP (VOLUME & CAPS LOCK) ---
_pycaw_vol_device = None

def init_audio():
    global _pycaw_vol_device
    if sys.platform != "win32":
        return None
    try:
        from pycaw.pycaw import AudioUtilities
        _pycaw_vol_device = AudioUtilities.GetSpeakers()
        return _pycaw_vol_device
    except Exception:
        _pycaw_vol_device = None
        return None

def get_volume():
    global _pycaw_vol_device
    if sys.platform == "win32":
        if _pycaw_vol_device is None:
            init_audio()
        if _pycaw_vol_device is not None:
            try:
                v = int(round(_pycaw_vol_device.volume_percent))
                m = bool(_pycaw_vol_device.EndpointVolume.GetMute())
                return v, m
            except Exception:
                _pycaw_vol_device = None
    return 70, False

def change_volume(delta):
    global _pycaw_vol_device
    if sys.platform == "win32":
        if _pycaw_vol_device is None:
            init_audio()
        if _pycaw_vol_device is not None:
            try:
                curr = _pycaw_vol_device.volume_percent
                new_v = max(0.0, min(100.0, curr + float(delta)))
                _pycaw_vol_device.volume_percent = new_v
                if new_v > 0 and _pycaw_vol_device.EndpointVolume.GetMute():
                    _pycaw_vol_device.EndpointVolume.SetMute(0, None)
                return
            except Exception:
                _pycaw_vol_device = None
        # Fallback to keybd_event
        try:
            import ctypes
            key = 0xAF if delta > 0 else 0xAE
            for _ in range(abs(delta) // 2 or 1):
                ctypes.windll.user32.keybd_event(key, 0, 0, 0)
                ctypes.windll.user32.keybd_event(key, 0, 2, 0)
        except Exception:
            pass

def get_caps_lock_state():
    if sys.platform == "win32":
        try:
            import ctypes
            return bool(ctypes.windll.user32.GetKeyState(0x14) & 1)
        except Exception:
            return False
    return False

# --- DEDICATED REAL-TIME HARDWARE CAPS LOCK MONITOR ---
class CapsLockMonitorThread(QThread):
    capsChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hook = None
        self._proc = None
        self.thread_id = 0
        self._running = True
        self.current_state = get_caps_lock_state()

    def run(self):
        if sys.platform != "win32":
            return
        import ctypes
        from ctypes import wintypes
        import time
        import threading

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        self.thread_id = kernel32.GetCurrentThreadId()

        WH_KEYBOARD_LL = 13
        WM_KEYUP = 0x0101
        WM_SYSKEYUP = 0x0105
        VK_CAPITAL = 0x14
        VK_SHIFT = 0x10
        VK_LSHIFT = 0xA0
        VK_RSHIFT = 0xA1

        HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", wintypes.DWORD),
                ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_ulonglong)
            ]

        def check_after_keystroke():
            time.sleep(0.04)
            try:
                st = get_caps_lock_state()
                if st != self.current_state:
                    self.current_state = st
                    self.capsChanged.emit(st)
            except Exception:
                pass

        def hook_proc(nCode, wParam, lParam):
            if nCode >= 0:
                try:
                    kb = KBDLLHOOKSTRUCT.from_address(lParam)
                    if kb.vkCode in (VK_CAPITAL, VK_SHIFT, VK_LSHIFT, VK_RSHIFT) and wParam in (WM_KEYUP, WM_SYSKEYUP):
                        st = get_caps_lock_state()
                        if st != self.current_state:
                            self.current_state = st
                            self.capsChanged.emit(st)
                        threading.Thread(target=check_after_keystroke, daemon=True).start()
                except Exception:
                    pass
            return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

        self._proc = HOOKPROC(hook_proc)
        self._hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, None, 0)

        # Background verification loop every 200ms so state never drifts
        def poller():
            while self._running:
                time.sleep(0.2)
                try:
                    st = get_caps_lock_state()
                    if st != self.current_state:
                        self.current_state = st
                        self.capsChanged.emit(st)
                except Exception:
                    pass

        poll_t = threading.Thread(target=poller, daemon=True)
        poll_t.start()

        if self._hook:
            msg = wintypes.MSG()
            while self._running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

            if self._hook:
                try:
                    user32.UnhookWindowsHookEx(self._hook)
                except Exception:
                    pass
                self._hook = None

    def stop(self):
        self._running = False
        if sys.platform == "win32":
            import ctypes
            if self._hook:
                try:
                    ctypes.windll.user32.UnhookWindowsHookEx(self._hook)
                    self._hook = None
                except Exception:
                    pass
            if self.thread_id:
                try:
                    ctypes.windll.user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)
                except Exception:
                    pass
        self.quit()
        self.wait(250)

# --- COMPREHENSIVE AUDIO SOURCE & APP RECOGNITION ---
def detect_player_source(app_id: str, title: str = "", artist: str = ""):
    aid = (app_id or "").lower()
    raw_title = (title or "").lower()
    raw_art = (artist or "").lower()

    if "spotify" in aid:
        return {"name": "Spotify", "icon": "🟢", "brand_color": "#1DB954", "badge": "Spotify"}
    elif "brave" in aid:
        is_yt = "youtube" in raw_title or "youtube" in raw_art
        return {"name": "Brave Browser", "icon": "🦁", "brand_color": "#FB542B", "badge": "Brave • YouTube" if is_yt else "Brave"}
    elif "msedge" in aid or "microsoftedge" in aid or "edge" in aid:
        is_yt = "youtube" in raw_title or "youtube" in raw_art
        return {"name": "Microsoft Edge", "icon": "🌊", "brand_color": "#0078D7", "badge": "Edge • YouTube" if is_yt else "Edge"}
    elif "chrome" in aid:
        is_yt = "youtube" in raw_title or "youtube" in raw_art
        return {"name": "Google Chrome", "icon": "🌐", "brand_color": "#4285F4", "badge": "Chrome • YouTube" if is_yt else "Chrome"}
    elif "firefox" in aid:
        is_yt = "youtube" in raw_title or "youtube" in raw_art
        return {"name": "Mozilla Firefox", "icon": "🦊", "brand_color": "#FF7139", "badge": "Firefox • YouTube" if is_yt else "Firefox"}
    elif "opera" in aid:
        return {"name": "Opera Browser", "icon": "⭕", "brand_color": "#FF1B2D", "badge": "Opera"}
    elif "vivaldi" in aid:
        return {"name": "Vivaldi", "icon": "🔴", "brand_color": "#EF3939", "badge": "Vivaldi"}
    elif "apple" in aid and "music" in aid:
        return {"name": "Apple Music", "icon": "🍎", "brand_color": "#FA2D48", "badge": "Apple Music"}
    elif "vlc" in aid:
        return {"name": "VLC Media Player", "icon": "🚧", "brand_color": "#FF8800", "badge": "VLC"}
    elif "discord" in aid:
        return {"name": "Discord", "icon": "💬", "brand_color": "#5865F2", "badge": "Discord"}
    elif "telegram" in aid:
        return {"name": "Telegram", "icon": "✈️", "brand_color": "#229ED9", "badge": "Telegram"}
    elif "whatsapp" in aid:
        return {"name": "WhatsApp", "icon": "📱", "brand_color": "#25D366", "badge": "WhatsApp"}
    elif "foobar" in aid:
        return {"name": "foobar2000", "icon": "🎼", "brand_color": "#5C6BC0", "badge": "foobar2000"}
    elif "aimp" in aid:
        return {"name": "AIMP", "icon": "🎵", "brand_color": "#FF9800", "badge": "AIMP"}
    elif "musicbee" in aid:
        return {"name": "MusicBee", "icon": "🐝", "brand_color": "#FBC02D", "badge": "MusicBee"}
    elif "itunes" in aid:
        return {"name": "iTunes", "icon": "🎵", "brand_color": "#EA4CC0", "badge": "iTunes"}
    elif "wmplayer" in aid or "zunemusic" in aid or "media.player" in aid or "groove" in aid:
        return {"name": "Windows Media Player", "icon": "🎵", "brand_color": "#00A4EF", "badge": "Media Player"}
    else:
        clean = app_id.replace(".exe", "").replace("_", " ").split("!")[-1].split("\\")[-1]
        name = clean.capitalize() if clean else "Media Player"
        return {"name": name, "icon": "🎵", "brand_color": "#00D4FF", "badge": name[:14]}

# --- WINDOWS AUTOSTART REGISTRY SYNCHRONIZER ---
def sync_autostart_registration(enabled=True):
    if sys.platform != "win32":
        return
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        exe_path = os.path.join(APP_DIR, "ixsland.exe")
        if not os.path.exists(exe_path):
            exe_path = sys.executable
        if enabled:
            winreg.SetValueEx(key, "ixsland", 0, winreg.REG_SZ, f'"{exe_path}"')
        else:
            try:
                winreg.DeleteValue(key, "ixsland")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass

# --- WINDOWS WINRT GSMTC MEDIA WORKER (ASYNCHRONOUS) ---
class WindowsGSMTCWorker(threading.Thread):
    def __init__(self, on_info_callback):
        super().__init__(daemon=True)
        self.on_info_callback = on_info_callback
        self.cmd_queue = queue.Queue()
        self.running = True

    def run(self):
        try:
            import asyncio
            asyncio.run(self._loop())
        except Exception:
            pass

    async def _loop(self):
        try:
            from winsdk.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager as MediaManager,
                GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
            )
            from datetime import timedelta
        except Exception:
            return

        mgr = None
        last_valid_info = None
        stopped_count = 0

        while self.running:
            try:
                if mgr is None:
                    mgr = await MediaManager.request_async()

                # Process commands from main UI thread
                while not self.cmd_queue.empty():
                    cmd, arg = self.cmd_queue.get_nowait()
                    sessions = mgr.get_sessions()
                    target_s = None
                    for s in sessions:
                        info = s.get_playback_info()
                        if info and info.playback_status == PlaybackStatus.PLAYING:
                            target_s = s
                            break
                    if not target_s:
                        target_s = mgr.get_current_session()
                    if not target_s and sessions:
                        target_s = sessions[0]

                    if target_s:
                        if cmd == "play_pause":
                            info = target_s.get_playback_info()
                            if info and info.playback_status == PlaybackStatus.PLAYING:
                                await target_s.try_pause_async()
                            else:
                                await target_s.try_play_async()
                        elif cmd == "next":
                            await target_s.try_skip_next_async()
                        elif cmd == "prev":
                            await target_s.try_skip_previous_async()
                        elif cmd == "seek":
                            target_sec = float(arg)
                            ticks = int(target_sec * 10_000_000)
                            try:
                                await target_s.try_change_playback_position_async(ticks)
                            except Exception:
                                try:
                                    await target_s.try_change_playback_position_async(timedelta(seconds=target_sec))
                                except Exception:
                                    pass

                # Find active playback session across background apps
                best_session = None
                sessions = mgr.get_sessions()
                for s in sessions:
                    info = s.get_playback_info()
                    if info and info.playback_status == PlaybackStatus.PLAYING:
                        best_session = s
                        break

                if not best_session:
                    curr = mgr.get_current_session()
                    if curr:
                        info = curr.get_playback_info()
                        if info and info.playback_status in (PlaybackStatus.PLAYING, PlaybackStatus.PAUSED):
                            best_session = curr

                if not best_session:
                    for s in sessions:
                        info = s.get_playback_info()
                        if info and info.playback_status == PlaybackStatus.PAUSED:
                            best_session = s
                            break

                if best_session:
                    info = best_session.get_playback_info()
                    st = info.playback_status if info else None
                    if st == PlaybackStatus.PLAYING:
                        status_str = "Playing"
                    elif st == PlaybackStatus.PAUSED:
                        status_str = "Paused"
                    else:
                        status_str = "Stopped"

                    if status_str in ("Playing", "Paused"):
                        props = await best_session.try_get_media_properties_async()
                        timeline = best_session.get_timeline_properties()
                        app_id = best_session.source_app_user_model_id or ""
                        
                        raw_title = props.title if props and props.title else ""
                        artist = props.artist if props and props.artist else ""

                        if " - " in raw_title and not artist:
                            p_title = raw_title.split(" - ", 1)
                            artist = p_title[0].strip()
                            song_title = p_title[1].strip()
                        else:
                            song_title = raw_title

                        if not song_title and last_valid_info and last_valid_info.get("title"):
                            song_title = last_valid_info["title"]
                            artist = last_valid_info.get("artist", artist)

                        source_meta = detect_player_source(app_id, raw_title, artist)
                        player_name = source_meta["name"]
                        player_icon = source_meta["icon"]
                        player_color = source_meta["brand_color"]
                        player_badge = source_meta["badge"]

                        if not artist:
                            artist = player_name

                        length = int(timeline.end_time.total_seconds()) if timeline and timeline.end_time else 0
                        base_pos = float(timeline.position.total_seconds()) if timeline and timeline.position else 0.0

                        if length <= 0 and last_valid_info and last_valid_info.get("length", 0) > 0:
                            length = last_valid_info["length"]

                        if status_str == "Playing" and timeline and timeline.last_updated_time:
                            try:
                                from datetime import timezone
                                now_utc = datetime.now(timezone.utc)
                                diff = (now_utc - timeline.last_updated_time).total_seconds()
                                pos = int(base_pos + diff) if 0.0 <= diff < 3600.0 else int(base_pos)
                            except Exception:
                                pos = int(base_pos)
                        else:
                            pos = int(base_pos)

                        if length > 0:
                            pos = max(0, min(pos, length))

                        # Extract high quality thumbnail bytes from WinRT stream
                        thumb_bytes = None
                        if props and props.thumbnail:
                            try:
                                from winsdk.windows.storage.streams import DataReader
                                stream = await props.thumbnail.open_read_async()
                                tsize = stream.size
                                if 0 < tsize < 10_000_000:
                                    reader = DataReader(stream)
                                    await reader.load_async(tsize)
                                    buf = bytearray(tsize)
                                    reader.read_bytes(buf)
                                    thumb_bytes = bytes(buf)
                            except Exception:
                                thumb_bytes = None

                        stopped_count = 0
                        info_dict = {
                            "status": status_str,
                            "title": song_title,
                            "artist": artist,
                            "player": player_name,
                            "player_icon": player_icon,
                            "player_color": player_color,
                            "player_badge": player_badge,
                            "length": length,
                            "position": pos,
                            "art_pixmap": None,
                            "thumb_bytes": thumb_bytes
                        }
                        if song_title:
                            last_valid_info = info_dict
                        self.on_info_callback(info_dict)
                    else:
                        stopped_count += 1
                        if stopped_count >= 1:
                            last_valid_info = None
                            self.on_info_callback({
                                "status": "Stopped", "title": "", "artist": "", "player": "",
                                "player_icon": "🎵", "player_color": "#00D4FF", "player_badge": "",
                                "length": 0, "position": 0, "art_pixmap": None, "thumb_bytes": None
                            })
                        elif last_valid_info:
                            self.on_info_callback(dict(last_valid_info))
                else:
                    # Detect background active audio sessions via PyCaw
                    active_audio_proc = None
                    try:
                        from pycaw.pycaw import AudioUtilities
                        for asess in AudioUtilities.GetAllSessions():
                            if asess.State == 1 and asess.Process:
                                pname = asess.Process.name()
                                if pname.lower() not in ("idle", "system", "ixsland.exe"):
                                    active_audio_proc = pname
                                    break
                    except Exception:
                        pass

                    if active_audio_proc:
                        src = detect_player_source(active_audio_proc, "", "")
                        self.on_info_callback({
                            "status": "Playing",
                            "title": f"Memutar Audio ({src['name']})",
                            "artist": src["name"],
                            "player": src["name"],
                            "player_icon": src["icon"],
                            "player_color": src["brand_color"],
                            "player_badge": src["badge"],
                            "length": 0,
                            "position": 0,
                            "art_pixmap": None,
                            "thumb_bytes": None
                        })
                    else:
                        stopped_count += 1
                        if stopped_count >= 1:
                            last_valid_info = None
                            self.on_info_callback({
                                "status": "Stopped", "title": "", "artist": "", "player": "",
                                "player_icon": "🎵", "player_color": "#00D4FF", "player_badge": "",
                                "length": 0, "position": 0, "art_pixmap": None, "thumb_bytes": None
                            })
                        elif last_valid_info:
                            self.on_info_callback(dict(last_valid_info))

            except Exception:
                pass

            import asyncio
            await asyncio.sleep(0.4)

# --- MEDIA CONTROLLER BRIDGE ---
class WindowsMediaController(QObject):
    mediaChanged = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.current_info = {
            "status": "Stopped",
            "title": "",
            "artist": "",
            "art_url": "",
            "art_pixmap": None,
            "length": 0,
            "position": 0,
            "player": ""
        }
        self.seek_ignore_until = 0.0
        self.has_gsm = False

        # Launch background GSMTC worker
        if sys.platform == "win32":
            try:
                import winsdk.windows.media.control
                self.worker = WindowsGSMTCWorker(self._on_worker_info)
                self.worker.start()
                self.has_gsm = True
            except Exception:
                self.worker = None
        else:
            self.worker = None

        # Fallback poller for demo / mock tracks
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.on_poll_tick)
        self.poll_timer.start(1000)

    def _on_worker_info(self, info):
        # Prevent slider jump during active user seek
        if time.time() < self.seek_ignore_until:
            info["position"] = self.current_info.get("position", 0)

        # Extract art_pixmap from thumb_bytes if present
        if info.get("thumb_bytes"):
            try:
                pix = QPixmap()
                if pix.loadFromData(info["thumb_bytes"]):
                    info["art_pixmap"] = pix.scaled(
                        64, 64,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
            except Exception:
                pass

        # Retain mock art if worker has none
        if not info.get("art_pixmap") and self.current_info.get("art_pixmap"):
            info["art_pixmap"] = self.current_info["art_pixmap"]

        changed = (
            self.current_info["status"] != info["status"] or
            self.current_info["title"] != info["title"] or
            self.current_info["artist"] != info["artist"] or
            self.current_info.get("position", 0) != info.get("position", 0) or
            self.current_info.get("length", 0) != info.get("length", 0) or
            self.current_info.get("art_pixmap") != info.get("art_pixmap") or
            self.current_info.get("player") != info.get("player")
        )
        self.current_info.update(info)
        if changed:
            self.mediaChanged.emit(self.current_info)

    def on_poll_tick(self):
        # Progress ticking for active mock or local playback
        if not self.has_gsm and self.current_info["status"] == "Playing":
            length = self.current_info.get("length", 0)
            if length > 0:
                self.current_info["position"] = (self.current_info["position"] + 1) % length
                self.mediaChanged.emit(self.current_info)

    def set_mock_track(self, title, artist, art_path=None, duration=195):
        pix = QPixmap(art_path) if art_path and os.path.exists(art_path) else None
        self.current_info = {
            "status": "Playing",
            "title": title,
            "artist": artist,
            "art_url": art_path or "",
            "art_pixmap": pix,
            "length": duration,
            "position": 18,
            "player": "Spotify"
        }
        self.mediaChanged.emit(self.current_info)

    def play_pause(self):
        if self.worker:
            self.worker.cmd_queue.put(("play_pause", None))
        else:
            new_st = "Paused" if self.current_info["status"] == "Playing" else "Playing"
            self.current_info["status"] = new_st
            self.mediaChanged.emit(self.current_info)

    def next_track(self):
        if self.worker:
            self.worker.cmd_queue.put(("next", None))
        else:
            self.current_info["position"] = 0
            self.mediaChanged.emit(self.current_info)

    def prev_track(self):
        if self.worker:
            self.worker.cmd_queue.put(("prev", None))
        else:
            self.current_info["position"] = 0
            self.mediaChanged.emit(self.current_info)

    def seek(self, target_seconds):
        self.seek_ignore_until = time.time() + 1.2
        self.current_info["position"] = int(target_seconds)
        if self.worker:
            self.worker.cmd_queue.put(("seek", float(target_seconds)))
        self.mediaChanged.emit(self.current_info)

# --- EXTRA FEATURE 1: MINIMIZE TOP NOTCH TRIGGER ---
class HiddenTriggerWidget(QWidget):
    def __init__(self, parent_island):
        super().__init__(None)
        self.island = parent_island
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(130, 8)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Dynamic Island diminimalkan\nSentuh kursor atau klik di sini untuk memunculkan")

    def enterEvent(self, event):
        self.island.toggle_minimize()
        super().enterEvent(event)

    def mousePressEvent(self, event):
        self.island.toggle_minimize()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        # Subtle glowing top notch indicator
        grad = QBrush(QColor(0, 180, 216, 180))
        p.setBrush(grad)
        p.drawRoundedRect(QRectF(15, 0, 100, 5), 2.5, 2.5)

# --- EXTRA FEATURE 2: SLEEK FLUENT UI SETTINGS DIALOG ---
class SettingsDialog(QDialog):
    def __init__(self, parent_island):
        super().__init__(None)
        self.island = parent_island
        self.cfg = self.island.cfg.copy()
        self.orig_bg_opacity = self.island.cfg.get("bg_opacity", 98)
        self.orig_scale = self.island.cfg.get("scale", 1.0)

        self.setWindowTitle("Pengaturan Dynamic Island")
        icon_path = os.path.join(ASSETS_DIR, "icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(ASSETS_DIR, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.resize(520, 480)
        self.setMinimumSize(480, 420)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #101218;
                color: #EDEDED;
                font-family: 'Segoe UI', Arial;
            }
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.12);
                background: #151822;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #0E1016;
                color: #A0A5B5;
                padding: 10px 18px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: #181C28;
                color: #00D4FF;
                border-bottom: 2px solid #00D4FF;
            }
            QGroupBox {
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin-top: 14px;
                font-weight: bold;
                color: #00D4FF;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 4px;
            }
            QLabel {
                color: #E0E2EC;
                font-size: 12px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #252A38;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #00D4FF;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QComboBox {
                background: #1E2332;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QCheckBox {
                color: #E0E2EC;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.25);
                background: #1C202C;
            }
            QCheckBox::indicator:checked {
                background: #00D4FF;
            }
            QPushButton {
                background: #202636;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #2B3348;
                border-color: #00D4FF;
            }
            QPushButton#btnSave {
                background: #0078D7;
                color: white;
                border: none;
                font-size: 13px;
            }
            QPushButton#btnSave:hover {
                background: #1084E3;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header with App Icon + Title
        hdr_layout = QHBoxLayout()
        hdr_layout.setSpacing(12)
        if os.path.exists(icon_path):
            lbl_ico = QLabel()
            pix = QPixmap(icon_path).scaled(38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_ico.setPixmap(pix)
            hdr_layout.addWidget(lbl_ico)

        v_hdr = QVBoxLayout()
        v_hdr.setSpacing(2)
        header = QLabel("PENGATURAN DYNAMIC ISLAND")
        header.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF; letter-spacing: 0.5px;")
        sub_header = QLabel("Mendukung Windows 10 & 11")
        sub_header.setStyleSheet("font-size: 11px; color: #8F9BB3;")
        v_hdr.addWidget(header)
        v_hdr.addWidget(sub_header)
        hdr_layout.addLayout(v_hdr)
        hdr_layout.addStretch()

        layout.addLayout(hdr_layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # --- TAB 1: TAMPILAN & SKALA ---
        tab_view = QWidget()
        v_box = QVBoxLayout(tab_view)

        grp_scale = QGroupBox("Skala Ukuran (Island Size)")
        sc_lay = QVBoxLayout(grp_scale)
        self.lbl_scale = QLabel(f"Ukuran Saat Ini: {int(self.cfg.get('scale', 1.0) * 100)}%")
        self.slider_scale = QSlider(Qt.Orientation.Horizontal)
        self.slider_scale.setRange(80, 150)
        self.slider_scale.setValue(int(self.cfg.get('scale', 1.0) * 100))
        self.slider_scale.valueChanged.connect(self.on_scale_slide)
        sc_lay.addWidget(self.lbl_scale)
        sc_lay.addWidget(self.slider_scale)
        v_box.addWidget(grp_scale)

        grp_op = QGroupBox("Transparansi Kaca (Glass Opacity)")
        op_lay = QVBoxLayout(grp_op)
        cur_op = int(self.cfg.get("bg_opacity", 98))
        self.lbl_op = QLabel(f"Tingkat Kegelapan: {cur_op}%")
        self.slider_op = QSlider(Qt.Orientation.Horizontal)
        self.slider_op.setRange(40, 100)
        self.slider_op.setValue(cur_op)
        self.slider_op.valueChanged.connect(self.on_opacity_slide)
        op_lay.addWidget(self.lbl_op)
        op_lay.addWidget(self.slider_op)
        v_box.addWidget(grp_op)
        v_box.addStretch()
        tabs.addTab(tab_view, "Tampilan")

        # --- TAB 2: FITUR & ANIMASI ---
        tab_feat = QWidget()
        f_box = QVBoxLayout(tab_feat)

        self.chk_mascot = QCheckBox("Aktifkan Maskot Robot OLED Interaktif (Gaze Tracking)")
        self.chk_mascot.setChecked(self.cfg.get("enable_mascot", True))
        f_box.addWidget(self.chk_mascot)

        self.chk_marquee = QCheckBox("Teks Berjalan Halus (Smooth Marquee untuk judul panjang)")
        self.chk_marquee.setChecked(self.cfg.get("enable_marquee", True))
        f_box.addWidget(self.chk_marquee)

        self.chk_adzan_pause = QCheckBox("Jeda Musik Otomatis saat Waktu Sholat Tiba (Adzan)")
        self.chk_adzan_pause.setChecked(self.cfg.get("pause_music_on_adzan", True))
        f_box.addWidget(self.chk_adzan_pause)

        f_box.addStretch()
        tabs.addTab(tab_feat, "Fitur & Perilaku")

        # --- TAB 3: WAKTU SHOLAT ---
        tab_prayer = QWidget()
        p_box = QVBoxLayout(tab_prayer)

        grp_city = QGroupBox("Lokasi Jadwal Sholat")
        c_lay = QVBoxLayout(grp_city)
        c_lay.addWidget(QLabel("Pilih Kota Anda:"))
        self.cb_city = QComboBox()
        self.cb_city.addItems(list(CITY_COORDINATES.keys()))
        cur_c = self.cfg.get("city", "Jakarta (WIB)")
        if cur_c in CITY_COORDINATES:
            self.cb_city.setCurrentText(cur_c)
        c_lay.addWidget(self.cb_city)
        p_box.addWidget(grp_city)
        p_box.addStretch()
        tabs.addTab(tab_prayer, "Jadwal Sholat")

        # --- TAB 4: SISTEM ---
        tab_sys = QWidget()
        s_box = QVBoxLayout(tab_sys)

        self.chk_autostart = QCheckBox("Jalankan otomatis saat Windows Startup")
        self.chk_autostart.setChecked(self.cfg.get("autostart", True))
        s_box.addWidget(self.chk_autostart)

        lbl_desc = QLabel(
            "Dynamic Island dirancang terintegrasi native dengan Windows 11 & 10.\n"
            "Mendukung deteksi media Spotify, browser Chrome/Edge/Firefox, serta OSD Volume & Caps Lock."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #8C92A4; margin-top: 10px; line-height: 140%;")
        s_box.addWidget(lbl_desc)

        s_box.addStretch()
        tabs.addTab(tab_sys, "Sistem")

        # Bottom Button Row
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Batal")
        btn_cancel.clicked.connect(self.close)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Simpan Pengaturan")
        btn_save.setObjectName("btnSave")
        btn_save.clicked.connect(self.save_and_apply)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def on_scale_slide(self, v):
        self.lbl_scale.setText(f"Ukuran Saat Ini: {v}%")
        self.island.scale = v / 100.0
        self.island.cfg["scale"] = v / 100.0
        self.island.init_placement()
        self.island.update_mask_for_mode()
        self.island.update()

    def on_opacity_slide(self, v):
        self.lbl_op.setText(f"Tingkat Kegelapan: {v}%")
        self.island.cfg["bg_opacity"] = v
        self.island.update()

    def closeEvent(self, event):
        self.island.settings_dialog = None
        super().closeEvent(event)

    def reject(self):
        self.island.cfg["bg_opacity"] = self.orig_bg_opacity
        self.island.scale = self.orig_scale
        self.island.cfg["scale"] = self.orig_scale
        self.island.init_placement()
        self.island.update_mask_for_mode()
        self.island.update()
        self.island.settings_dialog = None
        super().reject()

    def save_and_apply(self):
        self.cfg["scale"] = self.slider_scale.value() / 100.0
        self.cfg["bg_opacity"] = self.slider_op.value()
        self.orig_scale = self.cfg["scale"]
        self.orig_bg_opacity = self.cfg["bg_opacity"]
        self.cfg["enable_mascot"] = self.chk_mascot.isChecked()
        self.cfg["enable_marquee"] = self.chk_marquee.isChecked()
        self.cfg["pause_music_on_adzan"] = self.chk_adzan_pause.isChecked()
        self.cfg["autostart"] = self.chk_autostart.isChecked()

        city_name = self.cb_city.currentText()
        if city_name in CITY_COORDINATES:
            lat, lng, tz = CITY_COORDINATES[city_name]
            self.cfg["city"] = city_name
            self.cfg["latitude"] = lat
            self.cfg["longitude"] = lng
            self.cfg["timezone"] = tz

        # Windows Startup Registry Configuration
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE
                )
                exe_path = os.path.join(APP_DIR, "ixsland.exe")
                if not os.path.exists(exe_path):
                    exe_path = sys.executable
                if self.cfg["autostart"]:
                    winreg.SetValueEx(key, "ixsland", 0, winreg.REG_SZ, f'"{exe_path}"')
                else:
                    try:
                        winreg.DeleteValue(key, "ixsland")
                    except FileNotFoundError:
                        pass
                winreg.CloseKey(key)
            except Exception:
                pass

        save_config(self.cfg)
        self.island.apply_config(self.cfg)
        self.island.settings_dialog = None
        self.close()

# --- SMOOTH MARQUEE TEXT DRAWER ---
def draw_marquee_text(p, text, rect, font, color, offset):
    p.setFont(font)
    fm = p.fontMetrics()
    text_w = fm.horizontalAdvance(text)
    if text_w <= rect.width():
        p.setPen(color)
        p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
    else:
        p.save()
        p.setClipRect(rect)
        gap = 40
        span = text_w + gap
        shift = int(offset) % span
        p.setPen(color)
        p.drawText(int(rect.x() - shift), rect.y(), text_w, rect.height(), Qt.AlignmentFlag.AlignVCenter, text)
        p.drawText(int(rect.x() - shift + span), rect.y(), text_w, rect.height(), Qt.AlignmentFlag.AlignVCenter, text)
        p.restore()

# --- MAIN DYNAMIC ISLAND WIDGET ---
class IxslandWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.is_minimized = False
        self.is_hovered = False
        self.hidden_trigger = None
        self.settings_dialog = None

        # Base Window Flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.resize(CANVAS_W, CANVAS_H)

        # Scale Factor & Anchor
        self.scale = float(self.cfg.get("scale", 1.0))
        self.pill_y = 6.0

        # Dynamic Modes & Fluid Morphing Geometry
        # Base: IDLE (110x30), COMPACT_MEDIA (200x32), EXPANDED_MEDIA (340x148)
        self.mode = "IDLE"
        self.prev_mode = "IDLE"
        self.target_pill_w = 110
        self.target_pill_h = 30
        self.curr_pill_w = 110
        self.curr_pill_h = 30

        # Subsystems & States
        self.cursor_x = 0
        self.cursor_y = 0
        self.last_cursor_move_time = time.time()
        self.curr_gaze_x = 0.0
        self.curr_gaze_y = 0.0

        self.vol_percent, self.vol_muted = get_volume()
        self.display_vol = float(self.vol_percent)
        self.last_known_vol = self.vol_percent
        self.last_known_mute = self.vol_muted
        self.vol_anim = None

        self.is_seeking = False
        self.caps_lock_state = get_caps_lock_state()
        self.caps_anim = None
        self.caps_glow_pulse = 0.0
        self.caps_badge_pop = 1.0
        self.caps_text_slide = 0.0
        if self.caps_lock_state:
            self.mode = "CAPS_OSD"
            self.target_pill_w = 196
            self.target_pill_h = 32
            self.curr_pill_w = 196
            self.curr_pill_h = 32
        self.caps_monitor = CapsLockMonitorThread(self)
        self.caps_monitor.capsChanged.connect(self.trigger_caps_osd)
        self.caps_monitor.start()

        sync_autostart_registration(self.cfg.get("autostart", True))

        self.active_notif = {}
        self.active_prayer_alert = None

        # Media Hub Setup
        self.media_ctrl = WindowsMediaController()
        self.media_info = self.media_ctrl.current_info.copy()
        self.media_ctrl.mediaChanged.connect(self.on_media_changed)

        # Prayer Engine Setup
        lat = self.cfg.get("latitude", -6.2088)
        lng = self.cfg.get("longitude", 106.8456)
        tz = self.cfg.get("timezone", 7.0)
        self.prayer_times = calculate_prayer_times(lat, lng, tz)
        self.last_prayer_day = date.today().day
        self.notified_prayers = set()

        # Equalizer & Marquee
        self.eq_bars = [3, 8, 14, 7, 12]
        self.marquee_offset = 0.0

        # Timers
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.on_tick_1s)
        self.clock_timer.start(1000)
        self.idle_view_counter = 0

        self.mascot_timer = QTimer(self)
        self.mascot_timer.timeout.connect(self.on_mascot_tick)
        self.mascot_timer.start(40)

        self.eq_timer = QTimer(self)
        self.eq_timer.timeout.connect(self.animate_eq)
        self.eq_timer.start(120)

        self.hw_timer = QTimer(self)
        self.hw_timer.timeout.connect(self.poll_hardware_state)
        self.hw_timer.start(50)

        self.revert_timer = QTimer(self)
        self.revert_timer.setSingleShot(True)
        self.revert_timer.timeout.connect(self.revert_transient_mode)

        self.expanded_at = 0.0
        self.auto_collapse_timer = QTimer(self)
        self.auto_collapse_timer.timeout.connect(self.check_and_collapse_expanded)

        self.anim = None

        # System Tray & Placement
        self.setup_system_tray()
        self.setup_ipc_server()
        self.init_placement()
        self.update_mask_for_mode()

        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.cleanup)

    def cleanup(self):
        if hasattr(self, "caps_monitor") and self.caps_monitor:
            self.caps_monitor.stop()

    def apply_config(self, cfg):
        self.cfg = cfg
        self.scale = float(cfg.get("scale", 1.0))
        lat = cfg.get("latitude", -6.2088)
        lng = cfg.get("longitude", 106.8456)
        tz = cfg.get("timezone", 7.0)
        self.prayer_times = calculate_prayer_times(lat, lng, tz)
        self.init_placement()
        self.update()

    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(ASSETS_DIR, "icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        elif os.path.exists(os.path.join(ASSETS_DIR, "icon.ico")):
            self.tray_icon.setIcon(QIcon(os.path.join(ASSETS_DIR, "icon.ico")))

        self.tray_icon.activated.connect(self.on_tray_activated)

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #141822;
                color: #e0e0e0;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
                padding: 6px;
                font-family: 'Segoe UI', Arial;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #0078D7;
                color: white;
            }
        """)

        act_min = QAction("👁️ Sembunyikan / Munculkan Pulau", self)
        act_min.triggered.connect(self.toggle_minimize)
        menu.addAction(act_min)

        act_settings = QAction("⚙️ Pengaturan (Settings)", self)
        act_settings.triggered.connect(self.open_settings)
        menu.addAction(act_settings)

        menu.addSeparator()

        act_media = QAction("🎵 Demo Media Player", self)
        act_media.triggered.connect(lambda: self.media_ctrl.set_mock_track("Starboy", "The Weeknd, Daft Punk"))
        menu.addAction(act_media)

        act_recenter = QAction("🔄 Reset Posisi Tengah", self)
        act_recenter.triggered.connect(self.init_placement)
        menu.addAction(act_recenter)

        menu.addSeparator()

        act_quit = QAction("Keluar (Exit)", self)
        act_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_quit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip("ixsland Dynamic Island")
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            if self.is_minimized:
                self.toggle_minimize()
            else:
                self.open_settings()

    def open_settings(self):
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def toggle_minimize(self):
        self.is_minimized = not self.is_minimized
        if self.is_minimized:
            self.hide()
            s = self.get_target_screen()
            geom = s.geometry() if s else QRect(0, 0, 1920, 1080)
            if not self.hidden_trigger:
                self.hidden_trigger = HiddenTriggerWidget(self)
            self.hidden_trigger.move(geom.x() + (geom.width() - 130) // 2, geom.y())
            self.hidden_trigger.show()
            self.tray_icon.showMessage(
                "Dynamic Island Diminimalkan",
                "Sentuh bar atas atau klik tray icon untuk memunculkan kembali.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            if self.hidden_trigger:
                self.hidden_trigger.hide()
            self.show()
            self.init_placement()

    def setup_ipc_server(self):
        self.ipc_server = QTcpServer(self)
        self.ipc_server.newConnection.connect(self.on_ipc_connection)
        for port in [IPC_PORT, IPC_PORT + 1, 49283]:
            if self.ipc_server.listen(QHostAddress.SpecialAddress.LocalHost, port):
                break

    def on_ipc_connection(self):
        sock = self.ipc_server.nextPendingConnection()
        if not sock:
            return
        def read_data():
            try:
                raw = bytes(sock.readAll()).decode("utf-8", errors="ignore").strip()
                if raw:
                    for line in raw.splitlines():
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            self.handle_ipc_command(data)
                sock.write(b"OK\n")
                sock.flush()
            except Exception:
                pass
            sock.close()
        sock.readyRead.connect(read_data)

    def handle_ipc_command(self, data):
        cmd = data.get("cmd") or data.get("method")
        args = data.get("args", [])
        if cmd in ("volume", "setVolume"):
            val = int(data.get("val") if "val" in data else (args[0] if args else 75))
            self.trigger_volume_osd(val, False)
        elif cmd in ("caps", "setCapsLock"):
            val = bool(data.get("val") if "val" in data else (args[0] if args else True))
            self.caps_lock_state = val
            self.trigger_caps_osd(val)
        elif cmd in ("media", "setMediaTrack"):
            title = data.get("title") or (args[0] if len(args) > 0 else "Song")
            artist = data.get("artist") or (args[1] if len(args) > 1 else "Artist")
            self.media_ctrl.set_mock_track(
                title,
                artist,
                data.get("art_path"),
                data.get("duration", 210)
            )
        elif cmd in ("notif", "showNotification"):
            app = data.get("app") or (args[0] if len(args) > 0 else "Notification")
            summary = data.get("summary") or (args[1] if len(args) > 1 else "")
            body = data.get("body") or (args[2] if len(args) > 2 else "")
            self.trigger_notification(app, summary, body)
        elif cmd in ("prayer", "showPrayerAlert"):
            p = data.get("prayer") or (args[0] if args else "Dzuhur")
            self.trigger_prayer_alert(p)
        elif cmd == "triggerMascotSmile":
            self.mode = "IDLE"
            self.idle_view_counter = 1
            self.last_cursor_move_time = time.time()
            self.start_morph_animation(180, 36)
            self.update()
        elif cmd == "setScale":
            sc = float(args[0]) if args else 1.0
            self.scale = sc
            self.init_placement()
            self.update()
        elif cmd in ("triggerCollapse", "collapse"):
            self.mode = "IDLE"
            self.start_morph_animation(180, 36)
            self.update()
        elif cmd == "minimize":
            self.toggle_minimize()
        elif cmd == "activate":
            if self.is_minimized:
                self.toggle_minimize()
            self.show()
            self.raise_()
            self.activateWindow()
        elif cmd == "settings":
            if self.is_minimized:
                self.toggle_minimize()
            self.open_settings()

    def get_target_screen(self):
        app = QApplication.instance()
        screens = app.screens()
        return app.primaryScreen() if screens else None

    def init_placement(self):
        screen = self.get_target_screen()
        if not screen:
            return
        geo = screen.geometry()
        scale = getattr(self, "scale", 1.0)
        target_w = int(round(CANVAS_W * scale))
        target_h = int(round(CANVAS_H * scale))
        top_margin = int(round(self.cfg.get("top_margin", 12) * scale))

        x = geo.x() + (geo.width() - target_w) // 2
        y = geo.y() + top_margin
        self.setGeometry(x, y, target_w, target_h)

    def update_mask_for_mode(self):
        scale = getattr(self, "scale", 1.0)
        pill_w = int(round(self.curr_pill_w * scale))
        pill_h = int(round(self.curr_pill_h * scale))
        canvas_w = int(round(CANVAS_W * scale))
        pill_x = (canvas_w - pill_w) // 2
        pill_y = int(round(self.pill_y * scale))
        # Mask only the visible pill area so desktop clicks pass through
        region = QRegion(pill_x - 4, pill_y - 2, pill_w + 8, pill_h + 8, QRegion.RegionType.Rectangle)
        self.setMask(region)

    def on_tick_1s(self):
        self.idle_view_counter += 1
        now = datetime.now()

        # Daily recalculation of prayer times
        if now.day != self.last_prayer_day:
            lat = self.cfg.get("latitude", -6.2088)
            lng = self.cfg.get("longitude", 106.8456)
            tz = self.cfg.get("timezone", 7.0)
            self.prayer_times = calculate_prayer_times(lat, lng, tz)
            self.last_prayer_day = now.day
            self.notified_prayers.clear()

        # Offline Adzan Trigger
        now_mins = now.hour * 60 + now.minute
        for name, t_str, t_mins in self.prayer_times:
            if t_mins == now_mins and name not in self.notified_prayers:
                self.notified_prayers.add(name)
                self.trigger_prayer_alert(name)
                break

        if self.mode == "IDLE":
            self.update()

    def on_mascot_tick(self):
        # Update global cursor tracking via native Windows coordinates
        pos = QCursor.pos()
        if pos.x() != self.cursor_x or pos.y() != self.cursor_y:
            self.cursor_x = pos.x()
            self.cursor_y = pos.y()
            self.last_cursor_move_time = time.time()

        # Global auto-collapse when cursor leaves Dynamic Island expanded bounds
        if self.mode == "EXPANDED_MEDIA" and not getattr(self, "is_seeking", False):
            if time.time() - getattr(self, "expanded_at", 0) > 0.35:
                scale = getattr(self, "scale", 1.0)
                cw = self.geometry().x()
                cy = self.geometry().y()
                pill_w = int(round(self.curr_pill_w * scale))
                pill_h = int(round(self.curr_pill_h * scale))
                canvas_w = int(round(CANVAS_W * scale))
                pill_x = cw + (canvas_w - pill_w) // 2
                pill_y = cy + int(round(self.pill_y * scale))
                rect = QRect(pill_x - 10, pill_y - 10, pill_w + 20, pill_h + 20)
                if not rect.contains(self.cursor_x, self.cursor_y):
                    self.collapse_to_base_mode()

        # Marquee running text advance
        if self.mode in ("COMPACT_MEDIA", "EXPANDED_MEDIA") and self.cfg.get("enable_marquee", True):
            self.marquee_offset += 1.2
            self.update()

        if self.mode == "IDLE" and self.cfg.get("enable_mascot", True):
            phase = (self.idle_view_counter // 5) % 3
            if phase == 2:
                scale = getattr(self, "scale", 1.0)
                canvas_w = CANVAS_W * scale
                island_cx = self.geometry().x() + (canvas_w / 2.0)
                island_cy = self.geometry().y() + ((self.pill_y + (self.curr_pill_h / 2.0)) * scale)
                
                dx = self.cursor_x - island_cx
                dy = self.cursor_y - island_cy
                
                target_gx = math.tanh(dx / 350.0)
                target_gy = math.tanh(dy / 400.0)
                
                # Fluid gaze lerp
                self.curr_gaze_x += (target_gx - self.curr_gaze_x) * 0.25
                self.curr_gaze_y += (target_gy - self.curr_gaze_y) * 0.25
                self.update()

    def animate_eq(self):
        if self.mode in ("COMPACT_MEDIA", "EXPANDED_MEDIA"):
            if self.media_info.get("status") == "Playing":
                import random
                self.eq_bars = [random.randint(4, 18) for _ in range(5)]
            else:
                self.eq_bars = [3, 4, 3, 4, 3]
            self.update()

    def poll_hardware_state(self):
        # Hardware Volume polling
        vol, muted = get_volume()
        if vol != self.last_known_vol or muted != self.last_known_mute:
            self.trigger_volume_osd(vol, muted)

    def on_media_changed(self, info):
        self.media_info = info
        status = info.get("status", "Stopped")

        # Transient OSDs (Volume, Caps Lock, Notifications, Prayer Alert) have top priority!
        if self.mode in ("OSD_VOLUME", "CAPS_OSD", "NOTIFICATION", "PRAYER_ALERT"):
            return

        if status == "Playing":
            if self.mode in ("IDLE", "COMPACT_MEDIA"):
                self.mode = "COMPACT_MEDIA"
                self.update_mode_targets()
            elif self.mode == "EXPANDED_MEDIA":
                self.update()
        elif status == "Paused":
            # Music paused: if compact, return to IDLE (emot mata). If expanded, stay until mouse leaves!
            if self.mode == "COMPACT_MEDIA":
                self.mode = "IDLE"
                self.update_mode_targets()
            else:
                self.update()
        else: # Stopped or player closed
            self.media_info = {"status": "Stopped", "title": "", "artist": "", "player": "", "length": 0, "position": 0, "art_pixmap": None}
            if self.mode == "COMPACT_MEDIA":
                self.mode = "IDLE"
                self.update_mode_targets()
            else:
                self.update()

    def update_mode_targets(self):
        has_media = bool(self.media_info.get("title")) and self.media_info.get("status") in ("Playing", "Paused")
        targets = {
            "IDLE": (110, 30),
            "COMPACT_MEDIA": (200, 32),
            "EXPANDED_MEDIA": (340, 148) if has_media else (320, 84),
            "OSD_VOLUME": (210, 32),
            "CAPS_OSD": (196, 32),
            "NOTIFICATION": (260, 52),
            "PRAYER_ALERT": (280, 50)
        }
        tw, th = targets.get(self.mode, (110, 30))
        self.animate_morph(tw, th)

    def collapse_to_base_mode(self):
        if self.caps_lock_state:
            self.mode = "CAPS_OSD"
            self.update_mode_targets()
            return
        st = self.media_info.get("status", "Stopped")
        self.mode = "COMPACT_MEDIA" if st == "Playing" else "IDLE"
        self.update_mode_targets()

    def animate_morph(self, target_w, target_h):
        if self.anim and self.anim.state() == QVariantAnimation.State.Running:
            self.anim.stop()

        self.target_pill_w = target_w
        self.target_pill_h = target_h
        start_w = self.curr_pill_w
        start_h = self.curr_pill_h

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(240)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)

        def step(val):
            progress = float(val)
            self.curr_pill_w = int(round(start_w + (target_w - start_w) * progress))
            self.curr_pill_h = int(round(start_h + (target_h - start_h) * progress))
            self.update_mask_for_mode()
            self.update()

        def on_finished():
            self.curr_pill_w = target_w
            self.curr_pill_h = target_h
            self.update_mask_for_mode()
            self.update()

        self.anim.valueChanged.connect(step)
        self.anim.finished.connect(on_finished)
        self.anim.start()

    def check_and_collapse_expanded(self):
        if self.mode == "EXPANDED_MEDIA" and not getattr(self, "is_seeking", False):
            if time.time() - getattr(self, "expanded_at", 0) > 0.35:
                scale = getattr(self, "scale", 1.0)
                cw = self.geometry().x()
                cy = self.geometry().y()
                pill_w = int(round(self.curr_pill_w * scale))
                pill_h = int(round(self.curr_pill_h * scale))
                canvas_w = int(round(CANVAS_W * scale))
                pill_x = cw + (canvas_w - pill_w) // 2
                pill_y = cy + int(round(self.pill_y * scale))
                rect = QRect(pill_x - 10, pill_y - 10, pill_w + 20, pill_h + 20)
                pos = QCursor.pos()
                if not rect.contains(pos):
                    self.auto_collapse_timer.stop()
                    self.collapse_to_base_mode()

    def enterEvent(self, event):
        self.is_hovered = True
        if self.mode == "IDLE":
            self.animate_morph(145, 30)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        if self.mode == "IDLE":
            self.animate_morph(110, 30)
        elif self.mode == "EXPANDED_MEDIA" and not getattr(self, "is_seeking", False):
            if time.time() - getattr(self, "expanded_at", 0) > 0.35:
                self.collapse_to_base_mode()
        super().leaveEvent(event)

    # --- OSD TRIGGERS ---
    def trigger_volume_osd(self, target_vol=None, target_muted=None):
        if target_vol is not None:
            self.vol_percent = target_vol
            self.vol_muted = target_muted if target_muted is not None else False
        else:
            self.vol_percent, self.vol_muted = get_volume()
            
        self.last_known_vol = self.vol_percent
        self.last_known_mute = self.vol_muted

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

        if self.mode not in ("OSD_VOLUME", "CAPS_OSD", "NOTIFICATION", "PRAYER_ALERT"):
            self.prev_mode = self.mode
        self.mode = "OSD_VOLUME"
        self.update_mode_targets()
        self.update()
        self.revert_timer.start(2000)

    def start_caps_animation(self, is_on):
        if hasattr(self, "caps_anim") and self.caps_anim and self.caps_anim.state() == QVariantAnimation.State.Running:
            self.caps_anim.stop()

        target_w = 196
        target_h = 32
        start_w = self.curr_pill_w
        start_h = self.curr_pill_h

        # Elastic pop punch: punch expansion to 212px width then settle back to 196px
        punch_w = 212 if start_w >= 180 else 196

        self.caps_glow_pulse = 1.0
        self.caps_text_slide = 1.0

        self.caps_anim = QVariantAnimation(self)
        self.caps_anim.setDuration(360)
        self.caps_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.caps_anim.setStartValue(0.0)
        self.caps_anim.setEndValue(1.0)

        def on_step(val):
            progress = float(val)
            self.caps_glow_pulse = max(0.0, 1.0 - progress)
            self.caps_text_slide = max(0.0, 1.0 - progress)
            
            # Key badge press & spring rebound
            if progress < 0.35:
                self.caps_badge_pop = 1.0 - 0.28 * (progress / 0.35)
            else:
                p2 = (progress - 0.35) / 0.65
                self.caps_badge_pop = 0.72 + 0.28 * (1.0 + 0.18 * (1.0 - p2))

            # Morph pill dimensions with dynamic spring overshoot
            if start_w >= 180:
                if progress < 0.35:
                    p1 = progress / 0.35
                    self.curr_pill_w = int(round(start_w + (punch_w - start_w) * p1))
                    self.curr_pill_h = int(round(start_h + 3.0 * p1))
                else:
                    p2 = (progress - 0.35) / 0.65
                    self.curr_pill_w = int(round(punch_w + (target_w - punch_w) * p2))
                    self.curr_pill_h = int(round((start_h + 3) + (target_h - (start_h + 3)) * p2))
            else:
                self.curr_pill_w = int(round(start_w + (target_w - start_w) * progress))
                self.curr_pill_h = int(round(start_h + (target_h - start_h) * progress))

            self.target_pill_w = target_w
            self.target_pill_h = target_h
            self.update_mask_for_mode()
            self.update()

        def on_done():
            self.curr_pill_w = target_w
            self.curr_pill_h = target_h
            self.caps_glow_pulse = 0.0
            self.caps_text_slide = 0.0
            self.caps_badge_pop = 1.0
            self.update_mask_for_mode()
            self.update()

        self.caps_anim.valueChanged.connect(on_step)
        self.caps_anim.finished.connect(on_done)
        self.caps_anim.start()

    def trigger_caps_osd(self, state):
        self.caps_lock_state = bool(state)
        if self.mode not in ("OSD_VOLUME", "CAPS_OSD", "NOTIFICATION", "PRAYER_ALERT"):
            self.prev_mode = self.mode
        self.mode = "CAPS_OSD"
        self.start_caps_animation(self.caps_lock_state)

        if self.caps_lock_state:
            # Shift Lock / Caps Lock is ON: stay visible persistently while locked!
            self.revert_timer.stop()
        else:
            # Shift Lock / Caps Lock is OFF: show CAPS LOCK OFF briefly (1.5s), then revert to normal
            self.revert_timer.start(1500)

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

        self.revert_timer.start(8000)

    def revert_transient_mode(self):
        # If Caps Lock is still physically ON, return to CAPS_OSD
        if self.caps_lock_state:
            self.mode = "CAPS_OSD"
            self.update_mode_targets()
            return

        st = self.media_info.get("status", "Stopped")
        if getattr(self, "prev_mode", None) == "EXPANDED_MEDIA":
            self.mode = "EXPANDED_MEDIA"
        elif st == "Playing":
            self.mode = "COMPACT_MEDIA"
        else:
            self.mode = "IDLE"
        self.prev_mode = None
        self.update_mode_targets()

    # --- INPUT EVENTS ---
    def wheelEvent(self, event):
        delta = 3 if event.angleDelta().y() > 0 else -3
        change_volume(delta)
        v, m = get_volume()
        self.trigger_volume_osd(v, m)

    def mousePressEvent(self, event):
        scale = getattr(self, "scale", 1.0)
        pos = event.position()
        canvas_w = CANVAS_W * scale
        pill_w = self.curr_pill_w * scale
        pill_h = self.curr_pill_h * scale
        pill_x = (canvas_w - pill_w) / 2.0
        pill_y = self.pill_y * scale

        inside_pill = (
            pill_x <= pos.x() <= pill_x + pill_w and
            pill_y <= pos.y() <= pill_y + pill_h
        )

        if event.button() == Qt.MouseButton.LeftButton:
            if not inside_pill:
                if self.mode == "EXPANDED_MEDIA":
                    self.collapse_to_base_mode()
                return

            nx = (pos.x() - pill_x) / scale
            ny = (pos.y() - pill_y) / scale
            w = self.curr_pill_w
            h = self.curr_pill_h

            if self.mode == "EXPANDED_MEDIA":
                # Top action buttons: Settings [⚙], Minimize [🗕]
                if 4 <= ny <= 34:
                    if w - 30 <= nx <= w - 6:
                        self.toggle_minimize()
                        return
                    elif w - 56 <= nx <= w - 32:
                        self.open_settings()
                        return

                has_media = bool(self.media_info.get("title")) and self.media_info.get("status") in ("Playing", "Paused")
                if not has_media:
                    return

                # Progress bar Seek (Click or start Drag)
                bar_x = 18
                bar_y = 86
                bar_w = w - 36
                if (bar_x - 6) <= nx <= (bar_x + bar_w + 6) and (bar_y - 8) <= ny <= (bar_y + 16):
                    length = self.media_info.get("length", 0)
                    if length > 0:
                        click_ratio = max(0.0, min(1.0, (nx - bar_x) / float(bar_w)))
                        target_sec = click_ratio * length
                        self.is_seeking = True
                        self.media_info["position"] = int(target_sec)
                        self.media_ctrl.seek(target_sec)
                        self.update()
                        return

                # Controls row: Prev / Play-Pause / Next
                ctrl_top = 104
                ctrl_bot = 146
                if ctrl_top <= ny <= ctrl_bot:
                    mid_x = w / 2.0
                    if mid_x - 60 <= nx <= mid_x - 20:
                        self.media_ctrl.prev_track()
                        return
                    elif mid_x - 20 <= nx <= mid_x + 20:
                        was_playing = (self.media_info.get("status") == "Playing")
                        self.media_ctrl.play_pause()
                        if was_playing:
                            # Music was paused from dynamic island: immediately collapse to emot mata!
                            self.media_info["status"] = "Paused"
                            self.mode = "IDLE"
                            self.update_mode_targets()
                        else:
                            self.media_info["status"] = "Playing"
                            self.update()
                        return
                    elif mid_x + 20 <= nx <= mid_x + 60:
                        self.media_ctrl.next_track()
                        return
                return

            # Non-expanded modes
            if self.mode == "IDLE":
                if w >= 135:
                    if w - 26 <= nx <= w - 4 and 4 <= ny <= 26:
                        self.open_settings()
                        return
                    elif w - 48 <= nx <= w - 27 and 4 <= ny <= 26:
                        self.toggle_minimize()
                        return
                self.mode = "EXPANDED_MEDIA"
                self.expanded_at = time.time()
                self.update_mode_targets()
                return

            elif self.mode == "COMPACT_MEDIA":
                self.mode = "EXPANDED_MEDIA"
                self.expanded_at = time.time()
                self.update_mode_targets()
                return

            elif self.mode in ("OSD_VOLUME", "CAPS_OSD", "PRAYER_ALERT"):
                self.revert_timer.stop()
                self.collapse_to_base_mode()
                return

            elif self.mode == "NOTIFICATION":
                self.mode = "EXPANDED_MEDIA"
                self.expanded_at = time.time()
                self.update_mode_targets()
                return

        elif event.button() == Qt.MouseButton.MiddleButton:
            self.media_ctrl.play_pause()
        elif event.button() == Qt.MouseButton.RightButton:
            if inside_pill:
                self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        scale = getattr(self, "scale", 1.0)
        pos = event.position()
        canvas_w = CANVAS_W * scale
        pill_w = self.curr_pill_w * scale
        pill_x = (canvas_w - pill_w) / 2.0
        nx = (pos.x() - pill_x) / scale
        ny = (pos.y() - (self.pill_y * scale)) / scale

        if getattr(self, "is_seeking", False) and self.mode == "EXPANDED_MEDIA":
            length = self.media_info.get("length", 0)
            bar_x = 18
            bar_w = self.curr_pill_w - 36
            if length > 0 and bar_w > 0:
                ratio = max(0.0, min(1.0, (nx - bar_x) / float(bar_w)))
                target_sec = ratio * length
                self.media_info["position"] = int(target_sec)
                self.media_ctrl.seek(target_sec)
                self.update()
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, "is_seeking", False):
            self.is_seeking = False
            self.update()
        super().mouseReleaseEvent(event)

    def show_context_menu(self, point):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #141822;
                color: #e0e0e0;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
                padding: 6px;
                font-family: 'Segoe UI', Arial;
            }
            QMenu::item {
                padding: 6px 22px;
                border-radius: 4px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #0078D7;
                color: white;
            }
        """)

        act_toggle = QAction("Play / Pause Musik", self)
        act_toggle.triggered.connect(self.media_ctrl.play_pause)
        menu.addAction(act_toggle)

        act_min = QAction("👁️ Sembunyikan / Minimize Pulau", self)
        act_min.triggered.connect(self.toggle_minimize)
        menu.addAction(act_min)

        act_settings = QAction("⚙️ Pengaturan...", self)
        act_settings.triggered.connect(self.open_settings)
        menu.addAction(act_settings)

        menu.addSeparator()

        act_quit = QAction("Tutup ixsland", self)
        act_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_quit)

        menu.exec(point)

    # --- VECTOR PAINT ENGINE ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        scale = getattr(self, "scale", 1.0)
        canvas_w = CANVAS_W * scale
        pill_w = self.curr_pill_w * scale
        pill_h = self.curr_pill_h * scale
        pill_x = (canvas_w - pill_w) / 2.0
        pill_y = self.pill_y * scale
        radius = pill_h / 2.0 if self.mode != "EXPANDED_MEDIA" else (22.0 * scale)

        # Background Pill Glass
        path = QPainterPath()
        path.addRoundedRect(QRectF(pill_x, pill_y, pill_w, pill_h), radius, radius)

        opacity_val = int(self.cfg.get("bg_opacity", 98) * 2.55)
        painter.fillPath(path, QBrush(QColor(12, 12, 14, opacity_val)))

        # Border highlight
        border_col = QColor(255, 255, 255, 34)
        if self.mode == "CAPS_OSD":
            pulse = getattr(self, "caps_glow_pulse", 0.0)
            if self.caps_lock_state:
                border_alpha = int(190 + 65 * pulse)
                border_col = QColor(255, 179, 0, min(255, border_alpha))
            else:
                border_alpha = int(120 + 90 * pulse)
                border_col = QColor(160, 175, 195, min(255, border_alpha))
        elif self.mode == "OSD_VOLUME":
            border_col = QColor(0, 212, 255, 180)
        elif self.mode == "NOTIFICATION":
            border_col = QColor(0, 230, 118, 140)
        elif self.mode == "PRAYER_ALERT":
            border_col = QColor(0, 180, 216, 200)

        painter.strokePath(path, QPen(border_col, 1.2))

        # Render Content inside normalized pill coordinate space
        painter.save()
        painter.translate(pill_x, pill_y)
        painter.scale(scale, scale)

        w = self.curr_pill_w
        h = self.curr_pill_h

        if self.mode == "IDLE":
            self.paint_idle(painter, w, h)
        elif self.mode == "COMPACT_MEDIA":
            self.paint_compact_media(painter, w, h)
        elif self.mode == "EXPANDED_MEDIA":
            self.paint_expanded_media(painter, w, h)
        elif self.mode == "OSD_VOLUME":
            self.paint_osd_volume(painter, w, h)
        elif self.mode == "CAPS_OSD":
            self.paint_caps_osd(painter, w, h)
        elif self.mode == "NOTIFICATION":
            self.paint_notification(painter, w, h)
        elif self.mode == "PRAYER_ALERT":
            self.paint_prayer_alert(painter, w, h)

        painter.restore()

    def paint_idle(self, p, w, h):
        # 13-second rotating cycle:
        # 0.0s to 7.0s (7s): Robot mascot ("emot mata")
        # 7.0s to 10.0s (3s): Jam digital
        # 10.0s to 13.0s (3s): Waktu sholat
        cycle = time.time() % 13.0
        if cycle < 7.0:
            self.paint_mascot(p, w, h)
        elif cycle < 10.0:
            self.paint_idle_clock(p, w, h)
        else:
            self.paint_idle_prayer(p, w, h)

        if w >= 135:
            # Minimalist hover action buttons without square box background
            btn_min_rect = QRectF(w - 44, (h - 20) / 2.0, 18, 20)
            p.setFont(QFont("Segoe UI Emoji", 9))
            p.setPen(QColor(190, 200, 220))
            p.drawText(btn_min_rect, Qt.AlignmentFlag.AlignCenter, "🗕")

            btn_set_rect = QRectF(w - 22, (h - 20) / 2.0, 18, 20)
            p.setFont(QFont("Segoe UI Emoji", 9))
            p.setPen(QColor(190, 200, 220))
            p.drawText(btn_set_rect, Qt.AlignmentFlag.AlignCenter, "⚙")

    def paint_idle_clock(self, p, w, h):
        now = datetime.now()
        t_str = now.strftime("%H:%M")

        # Soft green indicator dot on the left
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 230, 118, 220)))
        p.drawEllipse(QPoint(16, int(h // 2)), 3, 3)

        # Clean, glowing digital clock
        p.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        p.setPen(QColor(255, 255, 255))
        clock_rect = QRect(22, 0, int(w - 28), int(h))
        p.drawText(clock_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, t_str)

    def paint_idle_prayer(self, p, w, h):
        now = datetime.now()
        next_prayer_name = "Dzuhur"
        next_prayer_time = "12:05"
        now_mins = now.hour * 60 + now.minute
        for name, t_str, t_mins in self.prayer_times:
            if t_mins > now_mins:
                next_prayer_name = name
                next_prayer_time = t_str
                break

        # Soft cyan indicator dot on the left
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 212, 255, 220)))
        p.drawEllipse(QPoint(14, int(h // 2)), 3, 3)

        # Prayer time text e.g. "🕌 Dzuhur 12:05"
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        p.setPen(QColor(230, 240, 255))
        prayer_str = f"🕌 {next_prayer_name} {next_prayer_time}"
        p.drawText(QRect(20, 0, int(w - 24), int(h)), Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, prayer_str)

    def paint_mascot(self, p, w, h):
        mid_x = w / 2.0
        mid_y = h / 2.0

        scale = getattr(self, "scale", 1.0)
        canvas_w = CANVAS_W * scale
        island_cx = self.geometry().x() + (canvas_w / 2.0)
        island_cy = self.geometry().y() + ((self.pill_y + (h / 2.0)) * scale)
        dist = math.hypot(self.cursor_x - island_cx, self.cursor_y - island_cy)
        is_hover = dist < (95.0 * scale)

        now = time.time()
        is_sleeping = (now - self.last_cursor_move_time) > 22.0
        blink_cycle = (now % 3.8)
        is_blinking = blink_cycle < 0.16 and not is_sleeping and not is_hover

        eye_spacing = 17.0
        left_eye_x = mid_x - eye_spacing
        right_eye_x = mid_x + eye_spacing
        eye_y = mid_y - 2.0

        gx = self.curr_gaze_x
        gy = self.curr_gaze_y

        if is_sleeping:
            # Sleep state: eyes closed with zzZ
            p.setPen(QPen(QColor(0, 229, 255, 200), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for ex in (left_eye_x, right_eye_x):
                p.drawLine(QPointF(ex - 5, eye_y + 1), QPointF(ex + 5, eye_y + 1))
            p.setPen(QPen(QColor(255, 255, 255, 180), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(mid_x - 3, eye_y + 8), QPointF(mid_x + 3, eye_y + 8))
            p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            p.setPen(QColor(0, 229, 255, 180))
            p.drawText(QRect(int(mid_x + 28), int(eye_y - 8), 30, 20), Qt.AlignmentFlag.AlignLeft, "zZ")
            return

        if is_hover:
            # Hover Joy (^  ^)
            p.setPen(QPen(QColor(0, 229, 255, 255), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for ex in (left_eye_x, right_eye_x):
                epath = QPainterPath()
                epath.moveTo(ex - 5.5, eye_y + 3)
                epath.quadTo(ex, eye_y - 4, ex + 5.5, eye_y + 3)
                p.drawPath(epath)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(255, 105, 180, 140)))
            p.drawEllipse(QPointF(left_eye_x - 8, eye_y + 5.5), 3.5, 2.2)
            p.drawEllipse(QPointF(right_eye_x + 8, eye_y + 5.5), 3.5, 2.2)

            p.setPen(QPen(QColor(255, 255, 255, 240), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            mpath = QPainterPath()
            mpath.moveTo(mid_x - 5.5, eye_y + 7.5)
            mpath.quadTo(mid_x, eye_y + 12.0, mid_x + 5.5, eye_y + 7.5)
            p.drawPath(mpath)
            return

        if is_blinking:
            p.setPen(QPen(QColor(0, 229, 255, 240), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for ex in (left_eye_x, right_eye_x):
                p.drawLine(QPointF(ex - 5, eye_y), QPointF(ex + 5, eye_y))
        else:
            for ex in (left_eye_x, right_eye_x):
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(0, 229, 255, 60)))
                p.drawRoundedRect(QRectF(ex - 7, eye_y - 8, 14, 16), 5, 5)

                p.setBrush(QBrush(QColor(0, 229, 255, 240)))
                p.drawRoundedRect(QRectF(ex - 5.5, eye_y - 6.5, 11, 13), 4, 4)

                pupil_x = ex + (gx * 2.8)
                pupil_y = eye_y + (gy * 2.2)
                p.setBrush(QBrush(QColor(255, 255, 255, 255)))
                p.drawEllipse(QPointF(pupil_x, pupil_y), 3.0, 3.0)

        mouth_x = mid_x + (gx * 2.2)
        mouth_y = eye_y + 8.5
        p.setPen(QPen(QColor(255, 255, 255, 230), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)

        mpath = QPainterPath()
        if gx < -0.3:
            mpath.moveTo(mouth_x - 4, mouth_y + 1.2)
            mpath.quadTo(mouth_x, mouth_y + 2.8, mouth_x + 4, mouth_y)
        elif gx > 0.3:
            mpath.moveTo(mouth_x - 4, mouth_y)
            mpath.quadTo(mouth_x, mouth_y + 2.8, mouth_x + 4, mouth_y + 1.2)
        else:
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
            p_col = QColor(self.media_info.get("player_color", "#00D4FF"))
            p_icon = self.media_info.get("player_icon", "🎵")
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(p_col.red(), p_col.green(), p_col.blue(), 50)))
            p.drawRoundedRect(art_rect, 6, 6)
            p.setFont(QFont("Segoe UI Emoji", 10))
            p.setPen(p_col)
            p.drawText(art_rect, Qt.AlignmentFlag.AlignCenter, p_icon)

        # Equalizer bars
        eq_right = w - 12
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 212, 255)))
        for i, bar_h in enumerate(self.eq_bars):
            bx = eq_right - (4 - i) * 6
            by = (h - bar_h) / 2.0
            p.drawRoundedRect(QRectF(bx, by, 3.5, bar_h), 1.5, 1.5)

        title = self.media_info.get("title", "")
        artist = self.media_info.get("artist", "")
        text_rect_w = int(w - 42 - 34)

        # Smooth Running Marquee
        draw_marquee_text(
            p, title,
            QRect(38, 4, text_rect_w, 16),
            QFont("Segoe UI", 9, QFont.Weight.Bold),
            QColor(255, 255, 255),
            self.marquee_offset
        )

        draw_marquee_text(
            p, artist,
            QRect(38, 20, text_rect_w, 14),
            QFont("Segoe UI", 8, QFont.Weight.Normal),
            QColor(160, 160, 165),
            self.marquee_offset * 0.8
        )

    def paint_top_action_buttons(self, p, w):
        # Settings [⚙] at w - 50
        set_rect = QRectF(w - 50, 10, 20, 20)
        p.setFont(QFont("Segoe UI Emoji", 10))
        p.setPen(QColor(170, 178, 195))
        p.drawText(set_rect, Qt.AlignmentFlag.AlignCenter, "⚙")

        # Minimize [🗕] at w - 24
        min_rect = QRectF(w - 24, 10, 20, 20)
        p.setFont(QFont("Segoe UI Emoji", 10))
        p.setPen(QColor(170, 178, 195))
        p.drawText(min_rect, Qt.AlignmentFlag.AlignCenter, "🗕")

    def paint_island_hub(self, p, w, h):
        self.paint_top_action_buttons(p, w)

        # Mascot Avatar
        art_rect = QRectF(16, 16, 52, 52)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(16, 22, 34)))
        p.drawRoundedRect(art_rect, 12, 12)
        p.setFont(QFont("Segoe UI Emoji", 22))
        p.setPen(QColor(0, 212, 255))
        p.drawText(art_rect, Qt.AlignmentFlag.AlignCenter, "🏝️")

        info_x = 78
        info_w = int(w - info_x - 56)

        p.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRect(info_x, 18, info_w, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "ixsland Dynamic Island")

        now = datetime.now()
        next_prayer_name = "Dzuhur"
        next_prayer_time = "12:05"
        now_mins = now.hour * 60 + now.minute
        for name, t_str, t_mins in self.prayer_times:
            if t_mins > now_mins:
                next_prayer_name = name
                next_prayer_time = t_str
                break

        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        p.setPen(QColor(150, 160, 180))
        p.drawText(QRect(info_x, 42, info_w, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"🕒 {now.strftime('%H:%M')}  •  🕌 {next_prayer_name} {next_prayer_time}")

    def paint_expanded_media(self, p, w, h):
        title = self.media_info.get("title", "")
        artist = self.media_info.get("artist", "")
        player = self.media_info.get("player", "Media")
        status = self.media_info.get("status", "Stopped")
        art = self.media_info.get("art_pixmap")

        has_media = bool(title) and status in ("Playing", "Paused")
        if not has_media:
            self.paint_island_hub(p, w, h)
            return

        # Top-Right Action Buttons: Settings [⚙], Minimize [🗕]
        self.paint_top_action_buttons(p, w)

        art_rect = QRectF(16, 16, 54, 54)
        if art and not art.isNull():
            p.save()
            clip = QPainterPath()
            clip.addRoundedRect(art_rect, 10, 10)
            p.setClipPath(clip)
            p.drawPixmap(art_rect.toRect(), art)
            p.restore()
        else:
            p_col = QColor(self.media_info.get("player_color", "#00D4FF"))
            p_icon = self.media_info.get("player_icon", "🎵")
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(p_col.red(), p_col.green(), p_col.blue(), 50)))
            p.drawRoundedRect(art_rect, 10, 10)
            p.setFont(QFont("Segoe UI Emoji", 20))
            p.setPen(p_col)
            p.drawText(art_rect, Qt.AlignmentFlag.AlignCenter, p_icon)

        info_x = 80
        info_w = int(w - info_x - 84)

        draw_marquee_text(
            p, title,
            QRect(info_x, 18, info_w, 20),
            QFont("Segoe UI", 11, QFont.Weight.Bold),
            QColor(255, 255, 255),
            self.marquee_offset
        )

        draw_marquee_text(
            p, artist,
            QRect(info_x, 38, info_w, 16),
            QFont("Segoe UI", 9, QFont.Weight.Normal),
            QColor(170, 170, 175),
            self.marquee_offset * 0.8
        )

        p_badge = self.media_info.get("player_badge") or self.media_info.get("player", "MEDIA")
        p_col = QColor(self.media_info.get("player_color", "#00B4D8"))
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        p.setPen(p_col)
        p.drawText(QRect(info_x, 56, info_w, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, p_badge.upper())

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
            # Scrub handle knob
            knob_x = bar_x + fill_w
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.drawEllipse(QPointF(knob_x, bar_y + (bar_h / 2.0)), 4.0, 4.0)

        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))
        p.setPen(QColor(170, 170, 175))
        pos_str = f"{pos // 60}:{pos % 60:02d}"
        len_str = f"{length // 60}:{length % 60:02d}" if length > 0 else "--:--"
        p.drawText(QRect(bar_x, bar_y + 7, 50, 14), Qt.AlignmentFlag.AlignLeft, pos_str)
        p.drawText(QRect(bar_x + bar_w - 50, bar_y + 7, 50, 14), Qt.AlignmentFlag.AlignRight, len_str)

        # Playback Controls
        mid_x = int(w // 2)
        ctrl_y = 108

        p.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        p.setPen(QColor(220, 220, 225))
        p.drawText(QRect(mid_x - 55, ctrl_y, 30, 30), Qt.AlignmentFlag.AlignCenter, "⏮")

        play_icon = "⏸" if status == "Playing" else "▶"
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 30)))
        p.drawEllipse(QPoint(mid_x, ctrl_y + 15), 18, 18)
        p.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRect(mid_x - 15, ctrl_y, 30, 30), Qt.AlignmentFlag.AlignCenter, play_icon)

        p.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
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

        p.setFont(QFont("Segoe UI Emoji", 12))
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
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.setPen(QColor(240, 240, 240))
        p.drawText(QRect(int(w - 46), 0, 40, int(h)), Qt.AlignmentFlag.AlignCenter, text)

    def paint_caps_osd(self, p, w, h):
        is_on = self.caps_lock_state
        text = "CAPS LOCK ON" if is_on else "CAPS LOCK OFF"
        text_color = QColor(255, 193, 7) if is_on else QColor(175, 180, 190)

        pulse = getattr(self, "caps_glow_pulse", 0.0)
        badge_scale = getattr(self, "caps_badge_pop", 1.0)
        text_slide = getattr(self, "caps_text_slide", 0.0)

        # Key badge on left with scale/pop animation
        badge_x = 12
        badge_y = (h - 20) / 2.0
        badge_w = 22
        badge_h = 20

        p.save()
        # Scale badge around its center
        cx = badge_x + badge_w / 2.0
        cy = badge_y + badge_h / 2.0
        p.translate(cx, cy)
        p.scale(badge_scale, badge_scale)
        p.translate(-cx, -cy)

        badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)

        if is_on:
            # Badge glow flash on activation
            if pulse > 0.05:
                p.setBrush(QBrush(QColor(255, 179, 0, int(120 * pulse))))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(badge_rect.adjusted(-2, -2, 2, 2), 6.0, 6.0)

            p.setPen(QPen(QColor(255, 179, 0, 210), 1.2))
            p.setBrush(QBrush(QColor(255, 179, 0, 45)))
            p.drawRoundedRect(badge_rect, 5.0, 5.0)

            p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            p.setPen(QColor(255, 193, 7))
            p.drawText(QRect(badge_x, int(badge_y), badge_w, int(badge_h)), Qt.AlignmentFlag.AlignCenter, "⇪")
        else:
            if pulse > 0.05:
                p.setBrush(QBrush(QColor(255, 255, 255, int(60 * pulse))))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(badge_rect.adjusted(-2, -2, 2, 2), 6.0, 6.0)

            p.setPen(QPen(QColor(255, 255, 255, 40), 1.0))
            p.setBrush(QBrush(QColor(255, 255, 255, 15)))
            p.drawRoundedRect(badge_rect, 5.0, 5.0)

            p.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
            p.setPen(QColor(160, 165, 175))
            p.drawText(QRect(badge_x, int(badge_y), badge_w, int(badge_h)), Qt.AlignmentFlag.AlignCenter, "⇪")

        p.restore()

        # Status text with smooth micro-slide & fade animation
        p.save()
        slide_offset = int(round(8.0 * text_slide))
        alpha = int(round(255 * (1.0 - 0.45 * text_slide)))
        col = QColor(text_color)
        col.setAlpha(alpha)

        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.setPen(col)
        p.drawText(QRect(42 + slide_offset, 0, int(w - 68), int(h)), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
        p.restore()

        # Status indicator dot on right with expanding pulse wave
        dot_x = w - 18
        dot_y = h / 2.0
        p.setPen(Qt.PenStyle.NoPen)

        if is_on:
            # Expanding halo wave pulse
            if pulse > 0.02:
                wave_r = 3.0 + 8.0 * (1.0 - pulse)
                wave_alpha = int(140 * pulse)
                p.setBrush(QBrush(QColor(255, 193, 7, wave_alpha)))
                p.drawEllipse(QPointF(dot_x, dot_y), wave_r, wave_r)

            # Active glowing LED
            p.setBrush(QBrush(QColor(255, 179, 0, 70)))
            p.drawEllipse(QPointF(dot_x, dot_y), 5.5, 5.5)
            p.setBrush(QBrush(QColor(255, 193, 7)))
            p.drawEllipse(QPointF(dot_x, dot_y), 3.0, 3.0)
        else:
            if pulse > 0.02:
                wave_r = 3.0 + 7.0 * (1.0 - pulse)
                wave_alpha = int(100 * pulse)
                p.setBrush(QBrush(QColor(200, 210, 225, wave_alpha)))
                p.drawEllipse(QPointF(dot_x, dot_y), wave_r, wave_r)

            p.setBrush(QBrush(QColor(130, 135, 145, 160)))
            p.drawEllipse(QPointF(dot_x, dot_y), 3.0, 3.0)

    def paint_notification(self, p, w, h):
        app = self.active_notif.get("app", "Notification")
        summary = self.active_notif.get("summary", "")
        body = self.active_notif.get("body", "")

        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        p.setPen(QColor(0, 230, 118))
        header = f"💬 {app.upper()}"
        if summary:
            header += f" · {summary}"
        elided_header = p.fontMetrics().elidedText(header, Qt.TextElideMode.ElideRight, int(w - 28))
        p.drawText(QRect(14, 8, int(w - 28), 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_header)

        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal))
        p.setPen(QColor(240, 240, 245))
        elided_body = p.fontMetrics().elidedText(body if body else "(Pesan baru)", Qt.TextElideMode.ElideRight, int(w - 28))
        p.drawText(QRect(14, 26, int(w - 28), 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_body)

    def paint_prayer_alert(self, p, w, h):
        name = getattr(self, "active_prayer_alert", "Sholat")
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.setPen(QColor(0, 212, 255))
        p.drawText(QRect(14, 6, int(w - 28), 18), Qt.AlignmentFlag.AlignCenter, f"🕌 WAKTU {name.upper()} TELAH TIBA")

        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal))
        p.setPen(QColor(220, 220, 225))
        p.drawText(QRect(14, 26, int(w - 28), 16), Qt.AlignmentFlag.AlignCenter, "Mari tunaikan sholat tepat waktu")


def check_single_instance():
    # 1. Try TCP IPC ping to existing instance
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.4)
        s.connect(("127.0.0.1", IPC_PORT))
        cmd = {"cmd": "settings"} if "--settings" in sys.argv else {"cmd": "activate"}
        s.sendall(json.dumps(cmd).encode("utf-8") + b"\n")
        s.close()
        print("Existing ixsland instance found. Signaled existing instance.")
        sys.exit(0)
    except Exception:
        pass

    # 2. Win32 Named Mutex
    if sys.platform == "win32":
        try:
            import ctypes
            mutex_name = "Global\\ixsland_dynamic_island_single_instance_mutex"
            mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
            last_err = ctypes.windll.kernel32.GetLastError()
            if last_err == 183: # ERROR_ALREADY_EXISTS
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.4)
                    s.connect(("127.0.0.1", IPC_PORT))
                    cmd = {"cmd": "settings"} if "--settings" in sys.argv else {"cmd": "activate"}
                    s.sendall(json.dumps(cmd).encode("utf-8") + b"\n")
                    s.close()
                except Exception:
                    pass
                sys.exit(0)
            return mutex
        except Exception:
            pass
    return None


def main():
    _mutex = check_single_instance()
    app = QApplication(sys.argv)
    app.setApplicationName("ixsland")
    app.setQuitOnLastWindowClosed(False)
    island = IxslandWidget()
    island.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
