@echo off
setlocal
title Access Bank Ghana WhatsApp Bot (Docker)

echo =========================================================
echo    Access Bank Ghana WhatsApp Bot - Docker Launcher
echo =========================================================
echo.

cd /d "%~dp0"

REM Add Docker to PATH if this terminal session was opened before installation
set "PATH=%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin;%ProgramFiles%\Docker\Docker\resources\bin;%PATH%"

REM 1. Check if Docker CLI is installed
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not installed or not added to your PATH!
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    echo After installing, restart your terminal or computer and run this file again.
    echo.
    pause
    exit /b 1
)

REM 2. Check if Docker daemon is running
docker info >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker Desktop is installed but is NOT currently running!
    echo Please launch Docker Desktop from your Start menu and wait until it says 'Docker Engine is running'.
    echo.
    pause
    exit /b 1
)

REM 3. Check for .env file
if not exist .env (
    echo [WARNING] No .env file found!
    if exist .env.example (
        echo Creating .env from .env.example...
        copy .env.example .env
        echo.
        echo Please open .env and fill in your OPENAI_API_KEY and WHATSAPP credentials!
        pause
    ) else (
        echo Please create a .env file with your required API keys before continuing.
        pause
        exit /b 1
    )
)

echo.
echo Starting bot via Docker Compose...
echo Running command: docker compose up --build
echo (Press Ctrl+C in this window anytime to stop the bot)
echo.

docker compose up --build

echo.
pause

