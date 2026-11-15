@echo off
title StreamVault Realtime Web Server
echo ==========================================================
echo   Starting StreamVault REALTIME Video Player Web Server
echo ==========================================================
echo.
echo Website akan mengambil video secara REALTIME langsung dari
echo tab Google Chrome yang sedang aktif di port 9222 (tanpa database).
echo.
echo Buka browser dan akses: http://127.0.0.1:5000
echo.
echo Tips: Jika port 9222 belum aktif, buka Chrome lewat: start_chrome.bat
echo Tekan CTRL+C untuk menghentikan server.
echo.
python server.py
pause
