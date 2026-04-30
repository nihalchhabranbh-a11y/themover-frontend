@echo off
title TheMover Installer
echo Installing TheMover Right-Click shortcut...

copy "%~dp0TheMover.bat" "%APPDATA%\Microsoft\Windows\SendTo\TheMover.bat" /Y

if %errorlevel% equ 0 (
    msg %username% "TheMover installed successfully! You can now right-click any file and select 'Send To -> TheMover'."
) else (
    echo Installation failed. Please ensure you extract the ZIP before running this installer.
    pause
)
