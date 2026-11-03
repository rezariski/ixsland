#!/usr/bin/env python3
"""
Interactive Feature Showcase Runner for ixsland (Windows 10 & 11 64-bit)
Sends JSON commands to ixsland listening on 127.0.0.1:49281
"""

import sys
import time
import json
import socket

IPC_PORT = 49281

def send_cmd(cmd, **kwargs):
    payload_dict = {"cmd": cmd}
    payload_dict.update(kwargs)
    payload = json.dumps(payload_dict) + "\n"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        s.connect(("127.0.0.1", IPC_PORT))
        s.sendall(payload.encode("utf-8"))
        res = s.recv(1024)
        s.close()
        return True
    except ConnectionRefusedError:
        print("[!] ixsland belum aktif! Jalankan ixsland.exe atau start.bat terlebih dahulu.")
        return False
    except Exception as e:
        print(f"[!] Error koneksi IPC: {e}")
        return False

def run_step(num, total, name, action_fn, active_sec=2.0):
    print(f"[{num:02d}/{total:02d}] 🚀 MENAMPILKAN: {name} ...", flush=True)
    action_fn()
    time.sleep(active_sec)
    print(f"        ↩ Kembali ke mode normal ...", flush=True)
    send_cmd("collapse")
    time.sleep(0.5)

def main():
    print("=" * 60)
    print("   IXSLAND DYNAMIC ISLAND — WINDOWS 10 & 11 SHOWCASE")
    print("   Mendukung Windows 10 (64-bit) & Windows 11 (64-bit)")
    print("=" * 60)
    
    if not send_cmd("collapse"):
        sys.exit(1)

    steps = [
        ("Robot Mascot: OLED Gaze Tracking & Hover Smile (^  ^)", lambda: send_cmd("triggerMascotSmile")),
        ("Skala Ukuran Dinamis: Diperbesar (125% Large)", lambda: send_cmd("setScale", args=[1.25])),
        ("Skala Ukuran Dinamis: Kembali Normal (100% Default)", lambda: send_cmd("setScale", args=[1.00])),
        ("Media Hub: Spotify Track (WinRT GSMTC Synchronized)", lambda: send_cmd("media", title="VOCE NA MIRA JUMPSTYLE", artist="Sxilwix")),
        ("Windows CoreAudio Volume OSD (Level 45%)", lambda: send_cmd("volume", val=45)),
        ("Windows CoreAudio Volume OSD (Level 85%)", lambda: send_cmd("volume", val=85)),
        ("CoreAudio Overboost Alert (Level 135% 🔥)", lambda: send_cmd("volume", val=135)),
        ("Caps Lock / Shift Lock HUD (ON - Amber Persistent Glow)", lambda: send_cmd("caps", val=True)),
        ("Caps Lock / Shift Lock HUD (OFF - Elastic Gray Collapse)", lambda: send_cmd("caps", val=False)),
        ("Alarm Waktu Sholat: Ashar (Astronomical Engine)", lambda: send_cmd("prayer", prayer="Ashar")),
        ("Desktop Chat Banner: WhatsApp Pesan Masuk", lambda: send_cmd("notif", app="WhatsApp", summary="Reza Rizki", body="ixsland Dynamic Island berjalan mulus di Windows 10/11 64-bit!")),
        ("Dynamic Island Settings: Dialog Pengaturan Fluent UI", lambda: send_cmd("settings"))
    ]

    total = len(steps)
    for i, (name, fn) in enumerate(steps, 1):
        run_step(i, total, name, fn)

    print("\n" + "=" * 60)
    print("   ✓ DEMO SHOWCASE WINDOWS 10/11 SELESAI SEMPURNA!")
    print("=" * 60)

if __name__ == "__main__":
    main()
