FROM python:3.12-slim

# System-Abhängigkeiten installieren (LibreOffice, Poppler für PDFs, Fonts für korrekte Darstellung)
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

# Verhindert pyc-Dateien und puffert Ausgaben
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/tmp

WORKDIR /app

# Python-Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY app.py .

EXPOSE 8080
ENV PORT=8080

# Gunicorn mit erhöhtem Timeout, da Office-Konvertierungen etwas dauern können
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120", "app:app"]
