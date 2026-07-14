FROM python:3.12-slim

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    poppler-utils \
    fonts-liberation \
    fontconfig \
    gcc \
    python3-dev \
    musl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# WICHTIG: Erlaubt LibreOffice, ohne X11-Server stabil und minimaler zu laufen
ENV HOME=/tmp
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080
ENV PORT=8080

# Timeout auf 300 Sekunden erhöht und Threads verwendet, um Speicher besser zu teilen
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "300", "app:app"]
