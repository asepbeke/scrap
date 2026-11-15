
@echo off
title Chrome Remote Debugging

set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
set "PROFILE_DIR=%LOCALAPPDATA%\ChromeDebugProfile"

if not exist "%CHROME_PATH%" (
    echo Chrome tidak ditemukan!
    pause
    exit /b 1
)

echo Starting Chrome Remote Debugging...
echo Port: 9222
echo Mode: Incognito
echo Profile: %PROFILE_DIR%

start "" "%CHROME_PATH%" ^
    --remote-debugging-port=9222 ^
    --incognito ^
    --user-data-dir="%PROFILE_DIR%"

exit /b 0
