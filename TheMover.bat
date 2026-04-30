@echo off
title TheMover Uploader
echo Uploading to TheMover... Please wait.

set "API_URL=https://themover-3r8d.onrender.com/api/upload"

for /f "usebackq delims=" %%i in (`curl.exe -s -X POST -F "file=@%~1" "%API_URL%" ^| powershell -command "$input | ConvertFrom-Json | Select-Object -ExpandProperty file | Select-Object -ExpandProperty url"`) do set "URL=%%i"

echo | set /p="%URL%" | clip

msg %username% "Upload Complete! TheMover link has been copied to your clipboard."
