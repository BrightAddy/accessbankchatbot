FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    USER_AGENT="AccessBankGhanaBot/1.0" \
    PORT=5000

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --timeout 120"]
