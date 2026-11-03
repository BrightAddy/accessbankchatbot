#!/bin/sh
set -e

echo "========================================================="
echo "   Access Bank Ghana WhatsApp Bot - Docker Launcher"
echo "========================================================="
echo ""

if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker is not installed or not in PATH."
    exit 1
fi

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "[WARNING] .env not found. Copying from .env.example..."
        cp .env.example .env
        echo "Please configure .env before continuing."
    fi
fi

echo "Starting bot via Docker Compose..."
docker compose up --build

