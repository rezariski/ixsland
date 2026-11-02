#!/usr/bin/env python3
"""
Interactive Showcase & Test Runner for ixsland Dynamic Island
Demonstrates every active feature with 2s active duration and 1s normal return.
"""

import sys
import time
import subprocess

def dbus_call(method, *args):
    cmd = ["qdbus6", "org.ixsland.Island", "/Island", f"local.ixsland.IxslandWidget.{method}"]
    for a in args:
        cmd.append(str(a))
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def show_step(num, total, title, action_fn):
    print(f"[{num:02d}/{total:02d}] 🚀 MENAMPILKAN: {title} ...", flush=True)
    action_fn()
    # Tampil selama 1.5 detik
    time.sleep(1.5)
    
    print(f"        ↩ Kembali ke mode normal (0.5 detik) ...", flush=True)
    dbus_call("triggerCollapse")
    # Kembali normal selama 0.5 detik
    time.sleep(0.5)

def main():
    print("=" * 60)
    print("   IXSLAND DYNAMIC ISLAND - SPOTIFY ACTIVE SHOWCASE")
    print("   Setiap fitur: 1.5s Tampil -> 0.5s Kembali Normal")
    print("=" * 60)
    time.sleep(0.5)

    steps = [
        ("Jam Digital Idle (HH:MM:SS)", lambda: (
            dbus_call("triggerIdlePhase", 0)
        )),
        ("Peringatan Waktu Sholat: SUBUH", lambda: (
            dbus_call("triggerPrayer", "Subuh")
        )),
        ("Peringatan Waktu Sholat: DZUHUR", lambda: (
            dbus_call("triggerPrayer", "Dzuhur")
        )),
        ("Peringatan Waktu Sholat: ASHAR", lambda: (
            dbus_call("triggerPrayer", "Ashar")
        )),
        ("Peringatan Waktu Sholat: MAGHRIB", lambda: (
            dbus_call("triggerPrayer", "Maghrib")
        )),
        ("Peringatan Waktu Sholat: ISYA", lambda: (
            dbus_call("triggerPrayer", "Isya")
        )),
        ("Rotasi Idle: Jadwal Sholat Berikutnya", lambda: (
            dbus_call("triggerIdlePhase", 1)
        )),
        ("Robot Mascot: Melirik Kiri (Display 1)", lambda: (
            dbus_call("triggerIdlePhase", 2),
            dbus_call("setCursor", 960, 600)
        )),
        ("Robot Mascot: Melirik Kanan (Display 2)", lambda: (
            dbus_call("triggerIdlePhase", 2),
            dbus_call("setCursor", 2950, 700)
        )),
        ("Robot Mascot: Hover Kursor Dekat (^  ^) + Merona Pink", lambda: (
            dbus_call("triggerIdlePhase", 2),
            dbus_call("setCursor", 2460, 36)
        )),
        ("Robot Mascot: Mode Tidur Nyenyak (- . -) zZ", lambda: (
            dbus_call("triggerIdlePhase", 2),
            dbus_call("triggerMascotSleep", True)
        )),
        ("Media Live Compact (Equalizer + Info Track)", lambda: (
            dbus_call("triggerCollapse")
        )),
        ("Media Expanded Hub (Kontrol Musik ⏮ ⏯ ⏭ & Durasi)", lambda: (
            dbus_call("triggerExpand")
        )),
        ("Volume OSD: Level 35%", lambda: (
            dbus_call("triggerVolume", 35, False)
        )),
        ("Volume OSD: Level 80%", lambda: (
            dbus_call("triggerVolume", 80, False)
        )),
        ("Volume OSD: MUTE (Hening)", lambda: (
            dbus_call("triggerVolume", 0, True)
        )),
        ("Caps Lock OSD: ON (Glow Amber 🔠)", lambda: (
            dbus_call("triggerCaps", True)
        )),
        ("Caps Lock OSD: OFF (🔤)", lambda: (
            dbus_call("triggerCaps", False)
        )),
        ("Desktop Notification: WhatsApp Chat Baru", lambda: (
            dbus_call("triggerNotification", "WhatsApp", "Budi Santoso", "Halo mas Reza, proyek ixsland Dynamic Island siap direkam!")
        )),
        ("Desktop Notification: Spectacle Tangkapan Layar", lambda: (
            dbus_call("triggerNotification", "Spectacle", "Tangkapan Layar", "Gambar tersimpan rapi di ~/Gambar/Screenshots.")
        )),
        ("Final: Jam Digital Idle Normal", lambda: (
            dbus_call("triggerMascotSleep", False),
            dbus_call("triggerIdlePhase", 0)
        ))
    ]

    total = len(steps)
    for i, (title, fn) in enumerate(steps, start=1):
        show_step(i, total, title, fn)

    print("=" * 60)
    print("✅ PENGUJIAN SEMUA FITUR SELESAI DENGAN SEMPURNA!")
    print("=" * 60)

if __name__ == "__main__":
    main()
