@echo off
title Start Chrome Remote Debugging (Port 9222)
echo ==========================================================
echo   Membuka Google Chrome dengan Remote Debugging (Port 9222)
echo ==========================================================
echo.
echo Pastikan semua jendela Chrome ditutup terlebih dahulu sebelum
echo menjalankan script ini jika port 9222 belum aktif.
echo.
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\ScrapProfile"
echo Chrome berhasil dibuka!
echo Silakan login ke forum dan buka thread yang ingin Anda tonton di Chrome tersebut.
echo.
pause

