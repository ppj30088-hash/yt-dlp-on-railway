FROM python:3.11-slim

# ffmpeg برای مرج ویدیو و صدا و تبدیل فرمت لازم است
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg aria2 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# بات از polling استفاده می‌کند، پس نیازی به باز کردن پورت نیست
CMD ["python", "bot.py"]
