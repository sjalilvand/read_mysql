# -*- coding: utf-8 -*-
# راه‌انداز PowerShell — سامانه گزارش‌گیری راه زندگی
# اجرا:  .\start.ps1
# یا کلیک راست → Run with PowerShell

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  سامانه گزارش‌گیری و تحلیل — راه زندگی" -ForegroundColor Magenta
Write-Host "  آدرس:            http://127.0.0.1:5000" -ForegroundColor White
Write-Host "  مسیر برنامه:     $Root" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Magenta

# ---------- پیدا کردن پایتون ----------
$py = $null
foreach ($cand in @('python', 'python3', "$Root\.venv\Scripts\python.exe")) {
    try {
        $v = & $cand --version 2>$null
        if ($LASTEXITCODE -eq 0 -and $v -match 'Python 3') { $py = $cand; break }
    } catch { }
}
if (-not $py) {
    Write-Host ""
    Write-Host "[!] پایتون پیدا نشد." -ForegroundColor Red
    Write-Host "    نصب خودکار با winget:" -ForegroundColor Yellow
    Write-Host "      winget install -e --id Python.Python.3.12" -ForegroundColor Cyan
    Write-Host "    بعد از نصب، یک بار این پنجره را ببندید و دوباره اجرا کنید."
    Read-Host "برای خروج Enter بزنید"
    exit 1
}
Write-Host "[✓] پایتون: $py" -ForegroundColor Green

# ---------- نصب وابستگی‌ها ----------
$needInstall = $false
& $py -c "import flask" 2>$null
if ($LASTEXITCODE -ne 0) { $needInstall = $true }
if ($needInstall) {
    Write-Host "[…] نصب وابستگی‌ها (flask, openpyxl)…" -ForegroundColor Yellow
    & $py -m pip install --disable-pip-version-check -q flask openpyxl
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] نصب ناموفق — اینترنت یا پروکسی را بررسی کنید." -ForegroundColor Red
        Read-Host "برای خروج Enter بزنید"
        exit 1
    }
    Write-Host "[✓] وابستگی‌ها نصب شد" -ForegroundColor Green
} else {
    Write-Host "[✓] وابستگی‌ها موجود است" -ForegroundColor Green
}

# ---------- باز کردن مرورگر ----------
Start-Process "http://127.0.0.1:5000"

# ---------- اجرای برنامه ----------
& $py "$Root\app.py"
Read-Host "برنامه متوقف شد. برای خروج Enter بزنید"
