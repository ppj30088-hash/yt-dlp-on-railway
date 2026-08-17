# Telegram yt-dlp Downloader Bot / بات دانلودر یت‌دیال‌پ تلگرام

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/deploy/RYOBU9)

---

## 🇺🇸 English

A Telegram bot that downloads videos from any site supported by [yt-dlp](https://github.com/yt-dlp/yt-dlp) (YouTube, Instagram, Twitter/X, TikTok, and hundreds more) and sends them back to the user. If the file exceeds Telegram's 50 MB bot limit, the bot automatically tries lower quality until it fits.

### Deploy on Railway

#### Option 1: One-Click Deploy (Template)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/deploy/RYOBU9)

Click the button above, enter your `TELEGRAM_BOT_TOKEN`, and Railway handles the rest.

#### Option 2: Fork + Deploy
1. **Fork this repository** (top-right corner of this page)
2. Go to [Railway Dashboard](https://railway.app/dashboard)
3. **New Project** → **Deploy from GitHub repo**
4. Select **your forked repository**
5. Set **Environment Variables**:
   - `TELEGRAM_BOT_TOKEN` = Your bot token from [@BotFather](https://t.me/BotFather) **(Required)**
6. Click **Deploy**

### How to set your bot token after forking:
After Railway starts deploying your forked repo:
1. Click on your project in Railway Dashboard
2. Go to **Variables** tab
3. Click **New Variable**
4. Name: `TELEGRAM_BOT_TOKEN`
5. Value: Paste your token from @BotFather
6. Click **Add** → Railway will automatically redeploy with your token

---

## 🇮🇷 فارسی

بات تلگرامی که ویدیو را از هر سایتی که [yt-dlp](https://github.com/yt-dlp/yt-dlp) پشتیبانی می‌کند (یوتیوب، اینستاگرام، توییتر/X، تیک‌تاک و صدها سایت دیگر) دانلود کرده و برای کاربر ارسال می‌کند. اگر حجم فایل از محدودیت ۵۰ مگابایتی تلگرام بیشتر باشد، بات خودکار کیفیت را پایین می‌آورد تا در حد مجاز شود.

### دیپلوی روی Railway

#### روش ۱: یک کلیک (Template)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/deploy/RYOBU9)

روی دکمه بالا کلیک کنید، `TELEGRAM_BOT_TOKEN` خودتان را وارد کنید، بقیه را Railway انجام می‌دهد.

#### روش ۲: Fork + Deploy
1. این ریپو را **Fork** کنید (گوشه بالا راست صفحه)
2. به [Railway Dashboard](https://railway.app/dashboard) بروید
3. **New Project** → **Deploy from GitHub repo**
4. ریپو Fork شده خودتان را انتخاب کنید
5. **Environment Variables** ست کنید:
   - `TELEGRAM_BOT_TOKEN` = توکن بات از [@BotFather](https://t.me/BotFather) **(الزامی)**
6. **Deploy** بزنید

### ست کردن توکن بعد از Fork:
پس از اینکه Railway پروژه‌تان را Deploy کرد:
1. پروژه را در Railway Dashboard باز کنید
2. تب **Variables** → **New Variable**
3. نام: `TELEGRAM_BOT_TOKEN`
4. مقدار: توکن خودتان از @BotFather
6. **Add** بزنید → Railway خودکار مجدد Deploy می‌کند

---

## 💻 Local Development / اجرای محلی

```bash
git clone <your-fork-url>
cd tg-ytdlp-bot
cp .env.example .env   # Add your TELEGRAM_BOT_TOKEN / توکن خودتان را اضافه کنید
pip install -r requirements.txt
python bot.py
```

### With Docker:
```bash
docker build -t tg-ytdlp-bot .
docker run -e TELEGRAM_BOT_TOKEN=your_token_here tg-ytdlp-bot
```

---

## 📁 Project Structure / ساختار پروژه

```
tg-ytdlp-bot/
├── bot.py           # Main bot logic / منطق اصلی بات
├── requirements.txt # python-telegram-bot, yt-dlp
├── Dockerfile       # Includes ffmpeg for video/audio merging / شامل ffmpeg برای مرج ویدیو/صدا
├── railway.json     # Railway build config / تنظیمات بیلد Railway
├── .env.example     # Environment variables template / قالب متغیرهای محیطی
├── logo.svg         # Template icon / آیکون تمپلیت
└── README.md
```

---

## ⚙️ How It Works / نحوه عملکرد

1. User sends a video URL (or text containing a URL) / کاربر لینک ویدیو می‌فرستد
2. Bot downloads with `yt-dlp` using best quality (1080p → 360p ladder) / دانلود با بهترین کیفیت (مرحله‌ای ۱۰۸۰ تا ۳۶۰)
3. If file > 50 MB, bot retries with lower quality automatically / اگر > ۵۰ مگابایت باشد، خودکار کیفیت کمتر می‌شود
4. Bot sends video with `supports_streaming=True` for instant playback / ارسال با استریمینگ لحظه‌ای
5. Temporary files cleaned up after each download / فایل‌های موقت پس از هر دانلود حذف می‌شوند

---

## 🎬 Quality Ladder (Auto-adjust) / پله کیفیت (خودکار)

| Attempt / تلاش | Format / فرمت |
|---------|--------|
| 1 | `bestvideo[height<=1080]+bestaudio` |
| 2 | `bestvideo[height<=720]+bestaudio` |
| 3 | `bestvideo[height<=480]+bestaudio` |
| 4 | `bestvideo[height<=360]+bestaudio` |
| 5 | `worst` |

---

## ✨ Features / ویژگی‌ها

- ✅ **Thumbnail** — پیش‌نمایش ویدیو در تلگرام (Video preview)
- ✅ **Faststart (moov atom first)** — پخش لحظه‌ای / استریمینگ (Instant streaming)
- ✅ **supports_streaming=True** — پلیر تلگرام بلافاصله پخش می‌کند
- ✅ **Auto quality ladder** — 1080p → 360p → worst (برای زیر ۵۰ مگابایت)
- ✅ **Cleanup** — فایل‌های موقت پس از ارسال حذف می‌شوند
- ✅ **Works in groups & private** — در گروه و پیوی کار می‌کند

---

## 📋 Requirements / پیش‌نیازها

- Python 3.11+
- `yt-dlp` (updated regularly / به‌روز به صورت منظم)
- `python-telegram-bot` v21+
- `ffmpeg` (included in Dockerfile / در Dockerfile گنجانده شده)

---

## 📄 License / لایسنس

MIT — Free to use, modify, and deploy / آزاد برای استفاده، تغییر و استقرار.