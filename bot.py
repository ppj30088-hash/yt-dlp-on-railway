import logging
import os
import re
import tempfile
import shutil

import yt_dlp
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ----------------------------------------------------------------------------
# تنظیمات
# ----------------------------------------------------------------------------

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "متغیر محیطی TELEGRAM_BOT_TOKEN تنظیم نشده. "
        "توکن بات خودت رو از @BotFather بگیر و در Environment Variables ست کن."
    )

# سقف حجم فایل قابل ارسال توسط بات‌های عادی تلگرام (مگابایت)
MAX_TELEGRAM_MB = 50
MAX_TELEGRAM_BYTES = MAX_TELEGRAM_MB * 1024 * 1024

# کیفیت‌هایی که برای کوچک کردن فایل امتحان می‌کنیم (از بهترین به بدترین)
QUALITY_LADDER = [
    "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "worst",
]

URL_REGEX = re.compile(r"https?://\S+")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# منطق دانلود
# ----------------------------------------------------------------------------

def download_with_format(url: str, out_dir: str, fmt: str) -> str | None:
    """با یک فرمت مشخص دانلود می‌کند و مسیر فایل نهایی را برمی‌گرداند."""
    output_template = os.path.join(out_dir, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": fmt,
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # اگر مرج انجام شده ممکنه پسوند فرق کند
        base, _ = os.path.splitext(filename)
        for ext in (".mp4", ".mkv", ".webm"):
            candidate = base + ext
            if os.path.exists(candidate):
                return candidate
        return filename if os.path.exists(filename) else None


def download_best_fitting(url: str, out_dir: str) -> tuple[str | None, str]:
    """
    از بهترین کیفیت شروع می‌کند؛ اگر حجم فایل از سقف تلگرام بیشتر بود،
    فایل را حذف کرده و با کیفیت پایین‌تر دوباره امتحان می‌کند.
    خروجی: (مسیر فایل یا None، پیام وضعیت)
    """
    last_error = ""
    for fmt in QUALITY_LADDER:
        try:
            filepath = download_with_format(url, out_dir, fmt)
        except Exception as e:  # noqa: BLE001
            last_error = str(e)
            logger.warning("دانلود با فرمت %s شکست خورد: %s", fmt, e)
            continue

        if not filepath or not os.path.exists(filepath):
            continue

        size = os.path.getsize(filepath)
        if size <= MAX_TELEGRAM_BYTES:
            return filepath, "ok"

        # خیلی بزرگه، پاکش کن و کیفیت پایین‌تر رو امتحان کن
        os.remove(filepath)
        logger.info(
            "فایل با فرمت %s حجمش %.1f مگابایت بود، رفتن سراغ کیفیت پایین‌تر",
            fmt,
            size / (1024 * 1024),
        )

    if last_error:
        return None, f"خطا در دانلود: {last_error}"
    return None, "even_lowest_quality_too_big"


# ----------------------------------------------------------------------------
# هندلرهای بات
# ----------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "سلام! 👋\n"
        "لینک ویدیو از یوتیوب، اینستاگرام، توییتر/X، تیک‌تاک و هر سایتی که "
        "yt-dlp پشتیبانی کنه رو برام بفرست تا برات دانلودش کنم.\n\n"
        "اگه فایل بزرگ باشه، خودکار کیفیت رو کم می‌کنم تا زیر "
        f"{MAX_TELEGRAM_MB} مگابایت بشه (محدودیت تلگرام برای بات‌های عادی)."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.strip()
    chat_type = msg.chat.type if msg.chat else "private"
    is_group = chat_type in ("group", "supergroup")

    match = URL_REGEX.search(text)

    # در گروه‌ها: فقط روی لینک مستقیم یا "هرمس + لینک" واکنش نشان بده
    if is_group:
        if "هرمس" in text:
            if match:
                url = match.group(0).rstrip(".,)")
                await process_url(update, url)
            # اگر "هرمس" هست ولی لینک نیست -> سکوت (بدون پیام خطا)
        elif match:
            # لینک مستقیم بدون "هرمس"
            url = match.group(0).rstrip(".,)")
            await process_url(update, url)
        # بقیه پیام‌های گروه -> سکوت کامل
        return

    # در پیوی: رفتار کامل (روی همه متن‌ها واکنش نشان بده)
    if match:
        url = match.group(0)
        await process_url(update, url)
    else:
        await msg.reply_text(
            "یه لینک معتبر بفرست (باید با http:// یا https:// شروع بشه)."
        )


async def process_url(update: Update, url: str) -> None:
    msg = update.message
    status_msg = await msg.reply_text("⏳ در حال دانلود... ممکنه کمی طول بکشه.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        filepath, status = download_best_fitting(url, tmp_dir)

        if status == "even_lowest_quality_too_big":
            await status_msg.edit_text(
                f"⚠️ حتی با پایین‌ترین کیفیت هم فایل بزرگ‌تر از {MAX_TELEGRAM_MB} "
                "مگابایته و نمی‌تونم بفرستمش."
            )
            return

        if not filepath:
            await status_msg.edit_text(f"❌ نشد دانلودش کنم.\n{status}")
            return

        try:
            await status_msg.edit_text("📤 در حال آپلود به تلگرام...")
            with open(filepath, "rb") as f:
                await msg.reply_video(
                    video=f,
                    caption=os.path.basename(filepath),
                    supports_streaming=True,
                    read_timeout=120,
                    write_timeout=120,
                    connect_timeout=60,
                )
            await status_msg.delete()
        except Exception as e:  # noqa: BLE001
            logger.exception("ارسال فایل شکست خورد")
            await status_msg.edit_text(f"❌ آپلود فایل شکست خورد: {e}")


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("بات در حال اجراست...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()