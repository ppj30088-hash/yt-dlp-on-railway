# بات دانلودر یت‌دیال‌پ تلگرام

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/deploy/RYOBU9)

بات تلگرامی که ویدیو را از هر سایتی که [yt-dlp](https://github.com/yt-dlp/yt-dlp) پشتیبانی می‌کند (یوتیوب، اینستاگرام، توییتر/X، تیک‌تاک و صدها سایت دیگر) دانلود کرده و برای کاربر ارسال می‌کند. اگر حجم فایل از محدودیت ۵۰ مگابایتی تلگرام بیشتر باشد، بات خودکار کیفیت را پایین می‌آورد تا در حد مجاز شود.

## دیپلوی روی Railway

### روش ۱: یک کلیک (Template)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/deploy/RYOBU9)

روی دکمه بالا کلیک کنید، `TELEGRAM_BOT_TOKEN` خودتان را وارد کنید، بقیه را Railway انجام می‌دهد.

### روش ۲: Fork + Deploy
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

## اجرا محلی

```bash
git clone <your-fork-url>
cd tg-ytdlp-bot
cp .env.example .env   # توکن خودتان را اضافه کنید
pip install -r requirements.txt
python bot.py
```

### با Docker:
```bash
docker build -t tg-ytdlp-bot .
docker run -e TELEGRAM_BOT_TOKEN=your_token_here tg-ytdlp-bot
```

---

## ساختار پروژه

```
tg-ytdlp-bot/
├── bot.py           # منطق اصلی بات
├── requirements.txt # python-telegram-bot, yt-dlp
├── Dockerfile       # شامل ffmpeg برای مرج ویدیو/صدا
├── railway.json     # تنظیمات بیلد Railway
├── .env.example     # قالب متغیرهای محیطی
├── logo.svg         # آیکون تمپلیت
├── README.md        # English version
├── README.fa.md     # این فایل (فارسی)
```

---

## نحوه عملکرد

1. کاربر لینک ویدیو می‌فرستد (یا متنی شامل لینک)
2. بات با `yt-dlp` دانلود می‌کند (بهترین کیفیت: ۱۰۸۰p → ۳۶۰p)
3. اگر فایل > ۵۰ مگابایت باشد، خودکار کیفیت کمتر می‌شود
4. بات ویدیو را با `supports_streaming=True` برای پخش لحظه‌ای ارسال می‌کند
5. فایل‌های موقت پس از هر دانلود حذف می‌شوند

---

## پله کیفیت (خودکار)

| تلاش | فرمت |
|------|------|
| ۱ | `bestvideo[height<=1080]+bestaudio` |
| ۲ | `bestvideo[height<=720]+bestaudio` |
| ۳ | `bestvideo[height<=480]+bestaudio` |
| ۴ | `bestvideo[height<=360]+bestaudio` |
| ۵ | `worst` |

---

## ویژگی‌ها

- ✅ **Thumbnail** — پیش‌نمایش ویدیو در تلگرام
- ✅ **Faststart (moov atom اول)** — پخش لحظه‌ای / استریمینگ
- ✅ **supports_streaming=True** — پلیر تلگرام بلافاصله پخش می‌کند
- ✅ **پله کیفیت خودکار** — ۱۰۸۰p → ۳۶۰p → worst (زیر ۵۰ مگابایت)
- ✅ **Cleanup** — فایل‌های موقت پس از ارسال حذف می‌شوند
- ✅ **کار در گروه و پیوی** — گروه و پیام خصوصی

---

## پیش‌نیازها

- Python 3.11+
- `yt-dlp` (به‌روز به صورت منظم)
- `python-telegram-bot` v21+
- `ffmpeg` (در Dockerfile گنجانده شده)

---

## لایسنس

MIT — آزاد برای استفاده، تغییر و استقرار.