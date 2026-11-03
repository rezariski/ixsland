# ixsland Dynamic Island - Windows 10 & 11 Demo Showcase Runner
# Mendukung Windows 10 & Windows 11 (64-bit) tanpa memerlukan instalasi Python!

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   🏝️  IXSLAND DYNAMIC ISLAND — WINDOWS 10/11 DEMO RUNNER" -ForegroundColor Green
Write-Host "   Native 60 FPS • Windows 10 & 11 (64-bit) Supported" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$port = 49281

function Send-IpcCommand($cmd, $params = @{}) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $connect = $tcp.BeginConnect("127.0.0.1", $port, $null, $null)
        $success = $connect.AsyncWaitHandle.WaitOne(1000, $false)
        if (-not $success) {
            $tcp.Close()
            return $false
        }
        $tcp.EndConnect($connect)
        
        $stream = $tcp.GetStream()
        $writer = New-Object System.IO.StreamWriter($stream, [System.Text.Encoding]::UTF8)
        $payload = @{ cmd = $cmd }
        foreach ($k in $params.Keys) {
            $payload[$k] = $params[$k]
        }
        $json = ($payload | ConvertTo-Json -Compress) + "`n"
        $writer.Write($json)
        $writer.Flush()
        $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
        $resp = $reader.ReadLine()
        $tcp.Close()
        return $true
    } catch {
        return $false
    }
}

# Periksa apakah ixsland sudah aktif
if (-not (Send-IpcCommand "collapse")) {
    Write-Host "[!] ixsland belum berjalan." -ForegroundColor Yellow
    Write-Host "    Mencoba menyalakan ixsland..." -ForegroundColor Gray
    
    $exe = "C:\ixsland\ixsland.exe"
    if (-not (Test-Path $exe)) {
        if (Test-Path "$PSScriptRoot\Setup.exe") {
            $exe = "$PSScriptRoot\Setup.exe"
        } elseif (Test-Path "$PSScriptRoot\..\Setup.exe") {
            $exe = "$PSScriptRoot\..\Setup.exe"
        }
    }
    if (Test-Path $exe) {
        Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe)
        Start-Sleep -Milliseconds 1800
    }
}

function Show-Step($num, $total, $title, [scriptblock]$action, $waitSec = 2.0) {
    Write-Host "[$("{0:D2}" -f $num)/$total] 🚀 $title ..." -ForegroundColor Yellow
    & $action
    Start-Sleep -Seconds $waitSec
    Send-IpcCommand "collapse" | Out-Null
    Start-Sleep -Milliseconds 500
}

$steps = @(
    @{ title = "Robot Mascot: OLED Gaze Tracking & Hover Smile (^  ^)"; action = { Send-IpcCommand "triggerMascotSmile" } },
    @{ title = "Skala Ukuran Dinamis: Diperbesar (125% Large)"; action = { Send-IpcCommand "setScale" @{ args = @(1.25) } } },
    @{ title = "Skala Ukuran Dinamis: Kembali Normal (100% Default)"; action = { Send-IpcCommand "setScale" @{ args = @(1.00) } } },
    @{ title = "Media Hub: Spotify Track (WinRT GSMTC Synchronized)"; action = { Send-IpcCommand "media" @{ title = "VOCE NA MIRA JUMPSTYLE"; artist = "Sxilwix" } } },
    @{ title = "CoreAudio OSD: Volume Slider (Level 45%)"; action = { Send-IpcCommand "volume" @{ val = 45 } } },
    @{ title = "CoreAudio OSD: Volume Slider (Level 85%)"; action = { Send-IpcCommand "volume" @{ val = 85 } } },
    @{ title = "CoreAudio OSD: Overboost Alert (Level 135% 🔥)"; action = { Send-IpcCommand "volume" @{ val = 135 } } },
    @{ title = "Caps Lock / Shift Lock OSD: ON (Persistent Amber Glow 🔠)"; action = { Send-IpcCommand "caps" @{ val = $true } } },
    @{ title = "Caps Lock / Shift Lock OSD: OFF (Elastic Gray Collapse 🔤)"; action = { Send-IpcCommand "caps" @{ val = $false } } },
    @{ title = "Alarm Waktu Sholat: Waktu Ashar Tiba (Astronomical Engine)"; action = { Send-IpcCommand "prayer" @{ prayer = "Ashar" } } },
    @{ title = "Desktop Chat Banner: WhatsApp Pesan Masuk"; action = { Send-IpcCommand "notif" @{ app = "WhatsApp"; summary = "Reza Rizki"; body = "ixsland Dynamic Island berjalan mulus di Windows 10/11 64-bit!" } } },
    @{ title = "Dynamic Island Settings: Dialog Pengaturan Fluent UI"; action = { Send-IpcCommand "settings" } }
)

$total = $steps.Count
for ($i = 0; $i -lt $total; $i++) {
    Show-Step ($i + 1) $total $steps[$i].title $steps[$i].action
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   ✅  DEMO SHOWCASE WINDOWS 10/11 SELESAI SEMPURNA!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
