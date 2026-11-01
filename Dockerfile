FROM python:3.12-slim

# ffmpeg (audio/video), nodejs (yt-dlp YouTube imzosi uchun zaxira), ca-certificates (HTTPS)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg nodejs ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]
