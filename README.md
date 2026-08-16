# Telegram yt-dlp Downloader Bot

بات تلگرامی که لینک هر سایتی که [yt-dlp](https://github.com/yt-dlp/yt-dlp) پشتیبانی می‌کند (یوتیوب، اینستاگرام، توییتر/X، تیک‌تاک و ده‌ها سایت دیگر) را بگیرد و ویدیو را دانلود و برای کاربر ارسال کند. اگر حجم فایل از سقف تلگرام بیشتر باشد، خودکار کیفیت را پایین می‌آورد تا زیر ۵۰ مگابایت شود.

## دیپلوی روی Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/YOUR_TEMPLATE_ID)

> ⚠️ لینک بالا تا وقتی که خودت این ریپو را به یک **Railway Template** تبدیل نکنی کار نمی‌کند. مراحلش در پایین همین فایل توضیح داده شده (بخش «ساخت دکمه‌ی Deploy»).

بعد از کلیک روی دکمه، Railway از شما می‌خواهد:

| متغیر | توضیح |
|---|---|
| `TELEGRAM_BOT_TOKEN` | توکن باتی که از [@BotFather](https://t.me/BotFather) گرفته‌اید |
| `MAX_TELEGRAM_MB` | (اختیاری) سقف حجم فایل به مگابایت، پیش‌فرض ۵۰ |

بعد از وارد کردن توکن، Railway خودش پروژه را با `Dockerfile` می‌سازد و بات بالا می‌آید.

## اجرای محلی (تست قبل از دیپلوی)

```bash
git clone <آدرس ریپوی خودت>
cd tg-ytdlp-bot
cp .env.example .env   # و توکن رو داخلش بذار
pip install -r requirements.txt
python bot.py
```

برای اجرا با Docker:

```bash
docker build -t tg-ytdlp-bot .
docker run -e TELEGRAM_BOT_TOKEN=xxxx tg-ytdlp-bot
```

## ساختار پروژه

```
tg-ytdlp-bot/
├── bot.py           # منطق اصلی بات
├── requirements.txt
├── Dockerfile        # شامل ffmpeg برای مرج ویدیو/صدا
├── railway.json       # تنظیمات بیلد Railway
├── .env.example
└── README.md
```
