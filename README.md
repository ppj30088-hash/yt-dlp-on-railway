# Telegram yt-dlp Downloader Bot

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/deploy/RYOBU9)

A Telegram bot that downloads videos from any site supported by [yt-dlp](https://github.com/yt-dlp/yt-dlp) (YouTube, Instagram, Twitter/X, TikTok, and hundreds more) and sends them back to the user. If the file exceeds Telegram's 50 MB bot limit, the bot automatically tries lower quality until it fits.

## Deploy on Railway

### Option 1: One-Click Deploy (Template)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/deploy/RYOBU9)

Click the button above, enter your `TELEGRAM_BOT_TOKEN`, and Railway handles the rest.

### Option 2: Fork + Deploy
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

## Local Development

```bash
git clone <your-fork-url>
cd tg-ytdlp-bot
cp .env.example .env   # Add your TELEGRAM_BOT_TOKEN
pip install -r requirements.txt
python bot.py
```

### With Docker:
```bash
docker build -t tg-ytdlp-bot .
docker run -e TELEGRAM_BOT_TOKEN=your_token_here tg-ytdlp-bot
```

---

## Project Structure

```
tg-ytdlp-bot/
├── bot.py           # Main bot logic
├── requirements.txt # python-telegram-bot, yt-dlp
├── Dockerfile       # Includes ffmpeg for video/audio merging
├── railway.json     # Railway build config (Dockerfile)
├── .env.example     # Environment variables template
├── logo.svg         # Template icon
├── README.md        # This file (English)
├── README.fa.md     # Persian version
```

---

## How It Works

1. User sends a video URL (or text containing a URL)
2. Bot downloads with `yt-dlp` using best quality (1080p → 360p ladder)
3. If file > 50 MB, bot retries with lower quality automatically
4. Bot sends video with `supports_streaming=True` for instant playback
5. Temporary files cleaned up after each download

---

## Quality Ladder (Auto-adjust)

| Attempt | Format |
|---------|--------|
| 1 | `bestvideo[height<=1080]+bestaudio` |
| 2 | `bestvideo[height<=720]+bestaudio` |
| 3 | `bestvideo[height<=480]+bestaudio` |
| 4 | `bestvideo[height<=360]+bestaudio` |
| 5 | `worst` |

---

## Features

- ✅ **Thumbnail** — Video preview in Telegram
- ✅ **Faststart (moov atom first)** — Instant streaming playback
- ✅ **supports_streaming=True** — Telegram player starts immediately
- ✅ **Auto quality ladder** — 1080p → 360p → worst (under 50 MB)
- ✅ **Cleanup** — Temp files deleted after each send
- ✅ **Works in groups & private** — Group and private chats

---

## Requirements

- Python 3.11+
- `yt-dlp` (updated regularly)
- `python-telegram-bot` v21+
- `ffmpeg` (included in Dockerfile)

---

## License

MIT — Free to use, modify, and deploy.