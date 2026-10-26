@echo off
chcp 65001 > nul
title CAI DAT MOI TRUONG - TRO LY THI TNVN
color 0B
cd /d "%~dp0"
echo ========================================================
echo   DANG CAI DAT CAC THU VIEN CAN THIET...
echo ========================================================
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo ========================================================
echo   CAI DAT HOAN TAT!
echo   Hay cam dien thoai, bat USB Debugging roi chay file:
echo   CHAY_TRO_LY.bat
echo ========================================================
pause
