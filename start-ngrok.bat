@echo off
title Access Bank WhatsApp Tunnel (ngrok)
echo =========================================================
echo   Access Bank Ghana WhatsApp Bot - Webhook Tunnel (ngrok)
echo =========================================================
echo.
echo Starting ngrok tunnel on port 5000...
echo Keep this window open or minimized while testing!
echo.

ngrok http --domain=sandbag-remix-skyward.ngrok-free.dev 5000
if %ERRORLEVEL% neq 0 (
    echo Retrying with default ngrok command...
    ngrok http 5000
)

pause
