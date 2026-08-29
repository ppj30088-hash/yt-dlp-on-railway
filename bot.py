import asyncio
import logging
import os
import re
import shutil
import tempfile
import subprocess

import yt_dlp
from telegram import Update
from telegram.error import BadRequest
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

# آیا aria2c روی سیستم نصبه؟ (دانلود چندریسمانی و خیلی سریع‌تر)
ARIA2C_AVAILABLE = shutil.which("aria2c") is not None

# کیفیت‌ها برای سایت‌های معمولی (از بهترین به بدترین)
QUALITY_LADDER = [
    "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "worst",
]

# کیفیت‌ها برای یوتیوب (Android client فقط فرمت ۱۸ - ۳۶۰p MP4 pre-merged برمی‌گرداند)
YOUTUBE_QUALITY_LADDER = [
    "18",   # فرمت ۱۸ - ۳۶۰p MP4 (video+audio merged, android client)
    "worst", # fallback
]

URL_REGEX = re.compile(r"https?://\S+")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# توابع کمکی
# ----------------------------------------------------------------------------

def is_youtube_url(url: str) -> bool:
    """بررسی آیا URL مربوط به یوتیوب است."""
    return "youtube.com" in url or "youtu.be" in url


def _base_ydl_opts(url: str, out_dir: str, fmt: str) -> dict:
    """تنظیمات مشترک yt-dlp با گزینه‌های سرعت بالا."""
    output_template = os.path.join(out_dir, "%(id)s.%(ext)s")
    opts = {
        "format": fmt,
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "postprocessor_args": {
            "ffmpeg": ["-movflags", "+faststart"]
        },
        # --- بهینه‌سازی‌های سرعت ---
        # دانلود چند فرگمنت به‌صورت هم‌زمان (برای HLS/DASH که فایل تکه‌تکه است)
        "concurrent_fragment_downloads": 8,
        # درخواست‌های شبکه رو سریع timeout بده و retry کن، به جای هنگ کردن
        "socket_timeout": 15,
        "retries": 3,
        "fragment_retries": 3,
        "extractor_retries": 1,
        # فایل‌های زیرنویس/thumbnail اضافه دانلود نکن - سرعت بیشتر
        "writesubtitles": False,
        "writethumbnail": False,
        "writeinfojson": False,
        # از cache دیسک برای extractor استفاده نکن (کمی سریع‌تر برای اجرای تک‌باره)
        "cachedir": False,
    }
    # اگر aria2c نصب باشه، به‌جای دانلودر داخلی ازش استفاده کن (چندریسمانی و بسیار سریع‌تر)
    if ARIA2C_AVAILABLE:
        opts["external_downloader"] = "aria2c"
        opts["external_downloader_args"] = {
            "aria2c": ["-x", "16", "-s", "16", "-k", "1M"]
        }
    # برای یوتیوب: از Android player client استفاده کن (بدون کوکی، بدون چالش JS)
    if is_youtube_url(url):
        opts["extractor_args"] = {
            "youtube": {
                "player_client": ["android"]
            }
        }
    return opts


def download_with_format(url: str, out_dir: str, fmt: str) -> str | None:
    """با یک فرمت مشخص دانلود می‌کند و مسیر فایل نهایی را برمی‌گرداند."""
    ydl_opts = _base_ydl_opts(url, out_dir, fmt)

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


def generate_thumbnail(video_path: str, out_dir: str) -> str | None:
    """استخراج فریم اول ویدیو به عنوان thumbnail با ffmpeg."""
    thumb_path = os.path.join(out_dir, "thumb.jpg")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                # گذاشتن -ss قبل از -i یعنی seek سریع بر اساس keyframe،
                # به‌جای decode کامل ویدیو تا اون لحظه (خیلی سریع‌تره)
                "-ss", "00:00:01", "-i", video_path,
                "-vframes", "1",
                "-vf", "scale=320:-1",  # حداکثر عرض ۳۲۰px برای تلگرام
                thumb_path
            ],
            capture_output=True, timeout=30, check=True
        )
        if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
            return thumb_path
    except Exception as e:
        logger.warning("Failed to generate thumbnail: %s", e)
    return None


def download_best_fitting(url: str, out_dir: str) -> tuple[str | None, str]:
    """
    از بهترین کیفیت شروع می‌کند؛ اگر حجم فایل از سقف تلگرام بیشتر بود،
    فایل را حذف کرده و با کیفیت پایین‌تر دوباره امتحان می‌کند.
    فقط یک بار extract+download انجام می‌شود (بدون pre-check جداگانه) تا سریع‌تر باشد.
    خروجی: (مسیر فایل یا None، پیام وضعیت)
    وضعیت‌های خاص: "unsupported" برای لینک‌های پشتیبانی‌نشده.
    """
    ladder = YOUTUBE_QUALITY_LADDER if is_youtube_url(url) else QUALITY_LADDER

    last_error = ""
    for fmt in ladder:
        try:
            filepath = download_with_format(url, out_dir, fmt)
        except yt_dlp.utils.UnsupportedError as e:
            # لینک اصلا پشتیبانی نمی‌شه، امتحان فرمت‌های دیگه فایده‌ای نداره
            return None, "unsupported"
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
# کمکی برای ارسال پیام حتی اگر پیام اصلی کاربر پاک شده باشد
# ----------------------------------------------------------------------------

def _is_reply_target_missing(exc: BadRequest) -> bool:
    text = str(exc).lower()
    return (
        "replied message not found" in text
        or "message to reply not found" in text
        or "message to be replied not found" in text
        or "reply message not found" in text
    )


async def safe_reply_text(msg, chat_id: int, context: ContextTypes.DEFAULT_TYPE, text: str):
    """reply_text امن: اگر پیام اصلی پاک شده باشه، به‌جاش پیام معمولی می‌فرسته."""
    try:
        return await msg.reply_text(text)
    except BadRequest as e:
        if _is_reply_target_missing(e):
            return await context.bot.send_message(chat_id=chat_id, text=text)
        raise


async def safe_reply_video(msg, chat_id: int, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    """reply_video امن: اگر پیام اصلی پاک شده باشه، ویدیو رو مستقیم به چت می‌فرسته."""
    try:
        return await msg.reply_video(**kwargs)
    except BadRequest as e:
        if _is_reply_target_missing(e):
            # فایل ارسال‌شده قبلاً خونده شده، باید از اول pointer رو برگردونیم
            if "video" in kwargs and hasattr(kwargs["video"], "seek"):
                kwargs["video"].seek(0)
            if "thumbnail" in kwargs and hasattr(kwargs["thumbnail"], "seek"):
                kwargs["thumbnail"].seek(0)
            return await context.bot.send_video(chat_id=chat_id, **kwargs)
        raise


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
    match = URL_REGEX.search(text)

    if not match:
        # در پیوی: اگر لینک نیست خطا بده
        # در گروه: سکوت کامل
        chat_type = msg.chat.type if msg.chat else "private"
        is_private = chat_type == "private"
        if is_private:
            await msg.reply_text(
                "یه لینک معتبر بفرست (باید با http:// یا https:// شروع بشه)."
            )
        return

    # لینک پیدا شده - در هر چتی (گروه یا پیوی) پردازش کن
    url = match.group(0).rstrip(".,)")
    await process_url(update, context, url)


async def process_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str) -> None:
    msg = update.message
    chat_id = msg.chat_id
    chat_type = msg.chat.type if msg.chat else "private"
    is_group = chat_type in ("group", "supergroup")

    # توجه: دیگه pre-check جداگانه (extract_info با download=False) نداریم.
    # همون یک بار extract+download داخل download_best_fitting انجام میشه،
    # که تقریبا نصف زمان استخراج اطلاعات لینک رو ذخیره می‌کنه.

    status_msg = await safe_reply_text(msg, chat_id, context, "⏳ در حال دانلود... ممکنه کمی طول بکشه.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        # دانلود توی thread جدا اجرا می‌شه تا event loop بات بلاک نشه
        # و بات بتونه هم‌زمان به پیام‌های دیگه هم جواب بده
        filepath, status = await asyncio.to_thread(download_best_fitting, url, tmp_dir)

        if status == "unsupported":
            if is_group:
                await status_msg.delete()
                return  # سکوت کامل در گروه برای لینک‌های پشتیبانی‌نشده
            await status_msg.edit_text("❌ این لینک پشتیبانی نمی‌شه.")
            return

        if status == "even_lowest_quality_too_big":
            await status_msg.edit_text(
                f"⚠️ حتی با پایین‌ترین کیفیت هم فایل بزرگ‌تر از {MAX_TELEGRAM_MB} "
                "مگابایته و نمی‌تونم بفرستمش."
            )
            return

        if not filepath:
            if is_group:
                await status_msg.delete()
                return  # سکوت کامل در گروه برای خطاهای دیگه (شبکه، geo-block و ...)
            await status_msg.edit_text(f"❌ نشد دانلودش کنم.\n{status}")
            return

        # Generate thumbnail (این هم توی thread جدا، تا event loop آزاد بمونه)
        thumb_path = await asyncio.to_thread(generate_thumbnail, filepath, tmp_dir)
        thumb_file = None

        try:
            await status_msg.edit_text("📤 در حال آپلود به تلگرام...")
            with open(filepath, "rb") as f:
                kwargs = {
                    "video": f,
                    "caption": os.path.basename(filepath),
                    "supports_streaming": True,
                    "read_timeout": 120,
                    "write_timeout": 120,
                    "connect_timeout": 60,
                }
                if thumb_path:
                    thumb_file = open(thumb_path, "rb")
                    kwargs["thumbnail"] = thumb_file
                # حتی اگر پیام اصلی کاربر (لینک) پاک شده باشه، ویدیو مستقیم به چت ارسال میشه
                await safe_reply_video(msg, chat_id, context, **kwargs)
            try:
                await status_msg.delete()
            except BadRequest:
                pass
        except Exception as e:  # noqa: BLE001
            logger.exception("ارسال فایل شکست خورد")
            try:
                await status_msg.edit_text(f"❌ آپلود فایل شکست خورد: {e}")
            except BadRequest:
                # حتی پیام وضعیت هم قابل ادیت نیست (مثلا پاک شده)، یه پیام جدید بفرست
                await context.bot.send_message(chat_id=chat_id, text=f"❌ آپلود فایل شکست خورد: {e}")
        finally:
            if thumb_file:
                try:
                    thumb_file.close()
                except Exception:
                    pass


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("بات در حال اجراست...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
        
