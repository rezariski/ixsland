# 🏝️ ixsland Dynamic Island (Windows)
> **Modern Dynamic Island Native untuk Windows 10 & Windows 11 (64-bit)**  
> Ringan, 60 FPS, Zero Electron Bloat, Mendukung Standalone Portable Installer `Setup.exe`.

---

## ⚡ Cara Instalasi Cepat

### Cara 1: Installer Mandiri (Paling Mudah, Tanpa Perlu Install Python)
1. Unduh dan jalankan file **`Setup.exe`** (38 MB).
2. Ikuti panduan wizard instalasi:
   - Pilih direktori pemasangan (default: `C:\ixsland`).
   - Opsi aktifkan autostart saat Windows menyala.
3. Klik **Pasang Sekarang**. `ixsland` akan otomatis langsung aktif di layar monitor utama Anda.

### Cara 2: Menjalankan dari Source Code (Developer)
Pastikan Anda memiliki Python 3.10+ (64-bit) terinstal di Windows:
```cmd
pip install PyQt6 pycaw comtypes winsdk
python ixsland_win.py
```

---

## 🧪 Menjalankan Demo Interaktif (Windows 10 / 11)

Untuk melihat simulasi seluruh modul dan animasi Dynamic Island beraksi:
1. Pastikan `ixsland` sedang menyala di desktop Anda.
2. Cukup klik ganda file **`run-demo.bat`** (atau jalankan `run-demo.ps1` via PowerShell).
3. Island akan otomatis memperagakan:
   - 🤖 **Robot Mascot**: Melirik kursor mouse dan tersenyum malu (^  ^).
   - 📏 **Resizing Dinamis**: Perubahan skala ukuran (125% -> 100%).
   - 🎵 **Media Hub**: Sinkronisasi track musik Spotify/browser (GSMTC) & kontrol playback.
   - 🔊 **CoreAudio Volume HUD**: Slider volume persisten & alert overboost 135%.
   - 🔠 **Shift Lock / Caps Lock OSD**: Animasi pop kuning saat aktif dan kolaps abu-abu saat nonaktif.
   - 🔴 **Indikator Privasi Hardware**: Sensor kamera (hijau) & mikrofon (oranye).
   - 🕌 **Pengingat Sholat**: Notifikasi otomatis saat waktu sholat tiba.
   - 💬 **Desktop Banner**: Notifikasi pesan chat masuk.

---

## 💻 Kompatibilitas Sistem
- **Windows 10** (64-bit, Versi 1903 ke atas)
- **Windows 11** (64-bit, Semua Versi)
- Kompatibel dengan semua jenis kartu grafis (Intel HD, AMD Radeon, NVIDIA GeForce).
- Tidak membutuhkan runtime tambahan atau hak administrator penuh.
