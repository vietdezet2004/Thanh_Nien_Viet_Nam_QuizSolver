@echo off
chcp 65001 > nul
title TRO LY THI THANH NIEN VIET NAM - REALTIME CTRL+F
color 0A
cd /d "%~dp0"
echo ========================================================
echo   DANG KHOI DONG TRO LY THI THANH NIEN VIET NAM...
echo ========================================================
python src/main.py
if errorlevel 1 (
    echo.
    echo [!] Xay ra loi khi chay tro ly. Nhan phim bat ky de thoat...
    pause > nul
)
