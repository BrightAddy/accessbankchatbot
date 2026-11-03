@echo off
setlocal
title Stop Access Bank Ghana WhatsApp Bot

echo =========================================================
echo    Stopping Access Bank Ghana WhatsApp Bot Container
echo =========================================================
echo.

cd /d "%~dp0"

REM Add Docker to PATH if this terminal session was opened before installation
set "PATH=%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin;%ProgramFiles%\Docker\Docker\resources\bin;%PATH%"

docker compose down

echo.
echo Bot container has been stopped cleanly.
echo.
pause

