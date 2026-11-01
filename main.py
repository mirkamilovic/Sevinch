"""Musiqa boti — BITTA FAYL (hamma modullar ichida). Faqat shu main.py kerak.

Ichida: config, core, premium, crypto, db, media, strings, cobalt, yt, deezer, assistants, player, song,
handlers_user, handlers_owner. Boshqa .py fayllarni (db.py, crypto.py, strings.py, handlers_*.py va h.k.)
o'chirib tashlasangiz bo'ladi — ular baribir ishlatilmaydi.

Yangiliklar:
* Fallen Music kabi buyruqlar menyusi (/ bosganda) + yangi buyruqlar: /loop /seek /seekback /shuffle /speed /verify.
  Admin buyruqlar (/panel /stats /reboot /ban /unban /cobaltest /dztest) menyuda faqat OWNER_ID dagilarga ko'rinadi.
* Yordamchi akkaunt /play paytida guruhga o'zi qo'shiladi: ochiq havola → bir martalik taklif havolasi,
  a'zolik so'rovini (zayafka) bot o'zi tasdiqlaydi, qo'shilgani haqidagi xizmat xabari o'chiriladi.
* YouTube'dan audio/video Cobalt API orqali olinadi (Railway Variables: COBALT_API_URL, ixtiyoriy COBALT_API_KEY).
  Cobalt ishlamasa avtomatik yt-dlp → Deezer → SoundCloud zaxiralariga o'tadi. Tekshirish: /cobaltest (owner).
* API ID/HASH Railway'siz ham kiritiladi: botga /panel → 🔑 API ID/HASH (bazada shifrlanadi).
* Qidiruv yt-dlp bloklansa YouTube qidiruv sahifasidan oddiy usulda olinadi.
Xato matnida satr raqami modul ichidagi satrga tegishli: <bundle:player.py> kabi.
"""
import sys
import types


def _load(name: str, src: str) -> None:
    mod = types.ModuleType(name)
    mod.__file__ = f"<bundle:{name}.py>"
    sys.modules[name] = mod  # boshqa fayllar `import name` qilganda shu modulni oladi
    try:
        exec(compile(src, f"<bundle:{name}.py>", "exec"), mod.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise

# ══════════ MODUL: config.py ══════════
_load('config', r'''import base64
import hashlib
import os
import re

from dotenv import load_dotenv

load_dotenv()


def _req(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"❌ {name} o'zgaruvchisi to'ldirilmagan (.env yoki Railway Variables).")
    return value


# Telegram API_ID/API_HASH (my.telegram.org). Railway'da berilmasa — /panel → 🔑 API ID/HASH orqali botning o'zida kiritiladi.
API_ID = int(os.getenv("API_ID", "0").strip() or 0)
API_HASH = os.getenv("API_HASH", "").strip()
BOT_TOKEN = _req("BOT_TOKEN")

# Bir nechta owner bo'lsa vergul bilan ajrating: 123,456
OWNER_LIST = [int(x) for x in re.split(r"[,\s]+", _req("OWNER_ID")) if x]
OWNER_IDS = set(OWNER_LIST)

# Ixtiyoriy: birinchi ishga tushirishda bitta yordamchini env orqali qo'shish (keyin panel orqali boshqariladi)
BOOT_SESSION = os.getenv("SESSION_STRING", "").strip()

LOG_CHAT = int(os.getenv("LOG_CHAT", "0") or 0)
SUPPORT_URL = os.getenv("SUPPORT_URL", "").strip()
UPDATES_URL = os.getenv("UPDATES_URL", "").strip()
START_IMG = os.getenv("START_IMG", "").strip()  # panel orqali media o'rnatilmagan bo'lsa ishlatiladi

# YouTube bloklasa qo'shiq shu bot orqali olinadi (yordamchi akkaunt inline qidiradi). O'chirish uchun bo'sh qoldiring.
DEEZER_BOT = os.getenv("DEEZER_BOT", "DeezerMusicBot").strip().lstrip("@")

# Cobalt API (Railway'dagi cobalt `api` servisi manzili). YouTube'dan audio/video shu orqali olinadi.
# Bo'sh qoldirilsa, bot oldingidek yt-dlp → Deezer → SoundCloud tartibida ishlaydi.
COBALT_API_URL = os.getenv("COBALT_API_URL", "").strip().rstrip("/")
if COBALT_API_URL and not COBALT_API_URL.lower().startswith(("http://", "https://")):
    COBALT_API_URL = "https://" + COBALT_API_URL
COBALT_API_KEY = os.getenv("COBALT_API_KEY", "").strip()  # faqat cobalt'da API_AUTH_REQUIRED yoqilgan bo'lsa
COBALT_TIMEOUT = int(os.getenv("COBALT_TIMEOUT", "40") or 40)  # havola olish uchun (soniya)
COBALT_DL_TIMEOUT = int(os.getenv("COBALT_DL_TIMEOUT", "180") or 180)  # audioni yuklab olish uchun (soniya)

DURATION_LIMIT_MIN = int(os.getenv("DURATION_LIMIT_MIN", "120"))
QUEUE_LIMIT = int(os.getenv("QUEUE_LIMIT", "50"))
DB_PATH = os.getenv("DB_PATH", "bot.db")  # Railway'da Volume ichidagi yo'l bering, masalan /data/bot.db

# Yordamchi sessiyalarni shifrlash kaliti. Berilmasa BOT_TOKEN'dan olinadi (token o'zgarsa sessiyalar o'qilmaydi).
_key = os.getenv("SECRET_KEY", "").strip()
SECRET_KEY = _key.encode() if _key else base64.urlsafe_b64encode(hashlib.sha256(BOT_TOKEN.encode()).digest())

# YouTube cookies. Asosiy manba — owner paneldan yuklangan fayl (bazada saqlanadi), zaxira — COOKIES_B64.
COOKIES_FILE = os.getenv("COOKIES_FILE", "cookies.txt")
_b64 = os.getenv("COOKIES_B64", "").strip()
if _b64:
    try:
        with open(COOKIES_FILE, "wb") as f:
            f.write(base64.b64decode(_b64))
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ COOKIES_B64 o'qilmadi: {exc}")
''')

# ══════════ MODUL: core.py ══════════
_load('core', r'''import time

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
)

# main.py ishga tushganda to'ldiriladi
BOT_USERNAME = ""
BOT_NAME = "Music Bot"
STARTED = time.time()  # bot ishga tushgan vaqt (/ping uptime uchun)
''')

# ══════════ MODUL: premium.py ══════════
_load('premium', r'''"""Premium emoji almashtirish va rangli tugmalar.

* Matnlarda oddiy emoji yoziladi — yuborish paytida (middleware) u egasi ulagan premium emojiga almashadi.
* Tugmalarda boshidagi emoji `icon_custom_emoji_id` ga aylanadi, `style` esa tugma rangini beradi
  (primary = ko'k, success = yashil, danger = qizil).
* Agar Telegram bunday so'rovni rad etsa, middleware premium/rang qismlarini olib tashlab qayta yuboradi.
"""
import logging
import re

from aiogram.client.default import Default
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton

log = logging.getLogger("premium")

VS = "️"

# Bot matnlarida ishlatiladigan oddiy emojilar (panelda ro'yxat sifatida ko'rsatiladi)
USED = (
    "👋", "🎵", "🎶", "🎧", "⚙️", "📢", "💬", "➕", "🔄", "😕", "⏳", "🔢", "👤", "▶️", "🕐",
    "⏸", "⏭", "⏹", "❌", "⚠️", "🔒", "ℹ️", "⏱", "🚫", "📭", "📜", "🌐", "👑", "✅", "🏓",
    "📊", "✖️", "⬅️", "👥", "📌", "🆔", "💎", "🖼", "🍪", "📣", "♻️",
)

EMOJI_MAP: dict[str, str] = {}
_RX: re.Pattern | None = None
_SPLIT = re.compile(r"(<tg-emoji.*?</tg-emoji>)", re.S)
_TG_TAG = re.compile(r"<tg-emoji[^>]*>(.*?)</tg-emoji>", re.S)

_TEXT_METHODS = {
    "SendMessage", "EditMessageText", "SendPhoto", "SendAnimation", "SendVideo",
    "SendDocument", "EditMessageCaption",
}


def norm(e: str) -> str:
    return e.replace(VS, "")


def load(mapping: dict[str, str]) -> None:
    global _RX
    EMOJI_MAP.clear()
    EMOJI_MAP.update({norm(k): v for k, v in mapping.items()})
    if EMOJI_MAP:
        keys = sorted(EMOJI_MAP, key=len, reverse=True)
        _RX = re.compile("|".join(re.escape(k) + VS + "?" for k in keys))
    else:
        _RX = None


def render(text: str) -> str:
    """Oddiy emojilarni <tg-emoji> bilan almashtiradi (tayyor teglarga tegmaydi)."""
    if not _RX or not text:
        return text
    parts = _SPLIT.split(text)
    for i in range(0, len(parts), 2):
        parts[i] = _RX.sub(
            lambda m: f'<tg-emoji emoji-id="{EMOJI_MAP[norm(m.group())]}">{m.group()}</tg-emoji>', parts[i]
        )
    return "".join(parts)


def strip_premium(text: str) -> str:
    return _TG_TAG.sub(r"\1", text) if text else text


def B(text: str, *, cb: str | None = None, url: str | None = None, style: str | None = None) -> InlineKeyboardButton:
    """Tugma yaratadi. Matn boshidagi emoji premium bo'lsa, ikonka sifatida qo'yiladi."""
    kw: dict = {}
    first, _, rest = text.partition(" ")
    if rest and norm(first) in EMOJI_MAP:
        kw["icon_custom_emoji_id"] = EMOJI_MAP[norm(first)]
        text = rest
    if style:
        kw["style"] = style
    return InlineKeyboardButton(text=text, callback_data=cb, url=url, **kw)


def _strip_markup(markup) -> None:
    rows = getattr(markup, "inline_keyboard", None)
    if not rows:
        return
    for row in rows:
        for btn in row:
            for field in ("icon_custom_emoji_id", "style"):
                try:
                    setattr(btn, field, None)
                except Exception:  # noqa: BLE001
                    pass


class EmojiMiddleware(BaseRequestMiddleware):
    async def __call__(self, make_request, bot, method):
        name = type(method).__name__
        if name in _TEXT_METHODS and not getattr(method, "entities", None):
            pm = getattr(method, "parse_mode", None)
            if isinstance(pm, Default) or str(pm).upper().endswith("HTML"):
                for attr in ("text", "caption"):
                    value = getattr(method, attr, None)
                    if isinstance(value, str) and value:
                        setattr(method, attr, render(value))
        try:
            return await make_request(bot, method)
        except TelegramBadRequest as exc:
            msg = str(exc).lower()
            if not any(k in msg for k in ("emoji", "button", "style", "entit")):
                raise
            log.warning("premium/style rad etildi, oddiy ko'rinishda qayta yuboriladi: %s", exc)
            for attr in ("text", "caption"):
                value = getattr(method, attr, None)
                if isinstance(value, str):
                    setattr(method, attr, strip_premium(value))
            _strip_markup(getattr(method, "reply_markup", None))
            return await make_request(bot, method)
''')

# ══════════ MODUL: crypto.py ══════════
_load('crypto', r'''from cryptography.fernet import Fernet

import config

try:
    _f = Fernet(config.SECRET_KEY)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(
        "❌ SECRET_KEY noto'g'ri. Bo'sh qoldiring yoki yangisini yarating:\n"
        "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    ) from exc


def enc(text: str) -> str:
    return _f.encrypt(text.encode()).decode()


def dec(token: str) -> str:
    return _f.decrypt(token.encode()).decode()
''')

# ══════════ MODUL: db.py ══════════
_load('db', r'''import time

import aiosqlite

import config

_db: aiosqlite.Connection | None = None


async def init() -> None:
    global _db
    _db = await aiosqlite.connect(config.DB_PATH)
    await _db.executescript(
        """
        CREATE TABLE IF NOT EXISTS chats(
            chat_id INTEGER PRIMARY KEY,
            lang TEXT NOT NULL DEFAULT 'uz',
            mode TEXT NOT NULL DEFAULT 'user',
            added_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS auth(
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            name TEXT,
            PRIMARY KEY(chat_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS banned(user_id INTEGER PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS plays(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER, title TEXT, ts INTEGER
        );
        CREATE TABLE IF NOT EXISTS assistants(
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT,
            session TEXT NOT NULL,
            added_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS chat_assistant(
            chat_id INTEGER PRIMARY KEY,
            assistant_id INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS emojis(key TEXT PRIMARY KEY, custom_id TEXT NOT NULL);
        """
    )
    await _db.commit()


# ───────────── guruhlar ─────────────
async def ensure_chat(chat_id: int) -> bool:
    """Yangi guruh bo'lsa True qaytaradi."""
    cur = await _db.execute("SELECT 1 FROM chats WHERE chat_id=?", (chat_id,))
    if await cur.fetchone():
        return False
    await _db.execute("INSERT INTO chats(chat_id, added_at) VALUES(?,?)", (chat_id, int(time.time())))
    await _db.commit()
    return True


async def get_chat(chat_id: int) -> tuple[str, str]:
    cur = await _db.execute("SELECT lang, mode FROM chats WHERE chat_id=?", (chat_id,))
    row = await cur.fetchone()
    if row:
        return row[0], row[1]
    await ensure_chat(chat_id)
    return "uz", "user"


async def set_lang(chat_id: int, lang: str) -> None:
    await ensure_chat(chat_id)
    await _db.execute("UPDATE chats SET lang=? WHERE chat_id=?", (lang, chat_id))
    await _db.commit()


async def set_mode(chat_id: int, mode: str) -> None:
    await ensure_chat(chat_id)
    await _db.execute("UPDATE chats SET mode=? WHERE chat_id=?", (mode, chat_id))
    await _db.commit()


async def remove_chat(chat_id: int) -> None:
    await _db.execute("DELETE FROM chats WHERE chat_id=?", (chat_id,))
    await _db.execute("DELETE FROM chat_assistant WHERE chat_id=?", (chat_id,))
    await _db.commit()


async def all_chat_ids() -> list[int]:
    cur = await _db.execute("SELECT chat_id FROM chats")
    return [r[0] for r in await cur.fetchall()]


# ───────────── ruxsat berilganlar ─────────────
async def add_auth(chat_id: int, user_id: int, name: str) -> None:
    await _db.execute(
        "INSERT OR REPLACE INTO auth(chat_id, user_id, name) VALUES(?,?,?)", (chat_id, user_id, name)
    )
    await _db.commit()


async def del_auth(chat_id: int, user_id: int) -> None:
    await _db.execute("DELETE FROM auth WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    await _db.commit()


async def is_auth(chat_id: int, user_id: int) -> bool:
    cur = await _db.execute("SELECT 1 FROM auth WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    return await cur.fetchone() is not None


async def list_auth(chat_id: int) -> list[tuple[int, str]]:
    cur = await _db.execute("SELECT user_id, name FROM auth WHERE chat_id=?", (chat_id,))
    return [(r[0], r[1] or str(r[0])) for r in await cur.fetchall()]


# ───────────── foydalanuvchilar ─────────────
async def add_user(user_id: int) -> None:
    await _db.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    await _db.commit()


async def remove_user(user_id: int) -> None:
    await _db.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    await _db.commit()


async def all_user_ids() -> list[int]:
    cur = await _db.execute("SELECT user_id FROM users")
    return [r[0] for r in await cur.fetchall()]


async def ban(user_id: int) -> None:
    await _db.execute("INSERT OR IGNORE INTO banned(user_id) VALUES(?)", (user_id,))
    await _db.commit()


async def unban(user_id: int) -> None:
    await _db.execute("DELETE FROM banned WHERE user_id=?", (user_id,))
    await _db.commit()


async def is_banned(user_id: int) -> bool:
    cur = await _db.execute("SELECT 1 FROM banned WHERE user_id=?", (user_id,))
    return await cur.fetchone() is not None


# ───────────── yordamchi akkauntlar ─────────────
async def add_assistant(user_id: int, name: str, phone: str, session_enc: str) -> None:
    await _db.execute(
        "INSERT OR REPLACE INTO assistants(user_id, name, phone, session, added_at) VALUES(?,?,?,?,?)",
        (user_id, name, phone, session_enc, int(time.time())),
    )
    await _db.commit()


async def del_assistant(user_id: int) -> None:
    await _db.execute("DELETE FROM assistants WHERE user_id=?", (user_id,))
    await _db.execute("DELETE FROM chat_assistant WHERE assistant_id=?", (user_id,))
    await _db.commit()


async def list_assistants() -> list[tuple[int, str, str, str]]:
    cur = await _db.execute("SELECT user_id, name, phone, session FROM assistants ORDER BY added_at")
    return [(r[0], r[1] or "", r[2] or "", r[3]) for r in await cur.fetchall()]


async def get_assignment(chat_id: int) -> int | None:
    cur = await _db.execute("SELECT assistant_id FROM chat_assistant WHERE chat_id=?", (chat_id,))
    row = await cur.fetchone()
    return row[0] if row else None


async def set_assignment(chat_id: int, assistant_id: int) -> None:
    await _db.execute(
        "INSERT OR REPLACE INTO chat_assistant(chat_id, assistant_id) VALUES(?,?)", (chat_id, assistant_id)
    )
    await _db.commit()


# ───────────── sozlamalar (media, cookies) ─────────────
async def get_setting(key: str) -> str | None:
    cur = await _db.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = await cur.fetchone()
    return row[0] if row else None


async def set_setting(key: str, value: str) -> None:
    await _db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (key, value))
    await _db.commit()


async def del_setting(key: str) -> None:
    await _db.execute("DELETE FROM settings WHERE key=?", (key,))
    await _db.commit()


# ───────────── premium emoji xaritasi ─────────────
async def emoji_all() -> dict[str, str]:
    cur = await _db.execute("SELECT key, custom_id FROM emojis")
    return {r[0]: r[1] for r in await cur.fetchall()}


async def emoji_set(key: str, custom_id: str) -> None:
    await _db.execute("INSERT OR REPLACE INTO emojis(key, custom_id) VALUES(?,?)", (key, custom_id))
    await _db.commit()


async def emoji_clear() -> None:
    await _db.execute("DELETE FROM emojis")
    await _db.commit()


# ───────────── statistika ─────────────
async def log_play(chat_id: int, title: str) -> None:
    await _db.execute(
        "INSERT INTO plays(chat_id, title, ts) VALUES(?,?,?)", (chat_id, (title or "")[:200], int(time.time()))
    )
    await _db.commit()


async def counts() -> tuple[int, int, int]:
    out = []
    for table in ("chats", "users", "plays"):
        cur = await _db.execute(f"SELECT COUNT(*) FROM {table}")
        out.append((await cur.fetchone())[0])
    return out[0], out[1], out[2]
''')

# ══════════ MODUL: media.py ══════════
_load('media', r'''"""Bot ichidan almashtiriladigan rasm/GIF (media slotlar)."""
import config
import db

SLOTS = {
    "start": "🖼 /start banneri",
    "welcome": "📌 Guruhga qo'shilgandagi rasm",
    "playing": "🎶 Ijro kartochkasi (thumbnail topilmasa)",
    "ping": "🏓 /ping rasmi",
}


def extract_media(msg) -> tuple[str, str] | None:
    """Xabardan (tur, file_id) ni oladi. GIF Telegramda 'animation' sifatida keladi."""
    if msg.animation:
        return "animation", msg.animation.file_id
    if msg.photo:
        return "photo", msg.photo[-1].file_id
    if msg.video:
        return "video", msg.video.file_id
    return None


async def get_slot(slot: str) -> tuple[str, str] | None:
    raw = await db.get_setting(f"media:{slot}")
    if not raw:
        return None
    kind, _, fid = raw.partition(":")
    return (kind, fid) if kind and fid else None


async def set_slot(slot: str, kind: str, file_id: str) -> None:
    await db.set_setting(f"media:{slot}", f"{kind}:{file_id}")


async def clear_slot(slot: str) -> None:
    await db.del_setting(f"media:{slot}")


async def send_with_media(bot, chat_id: int, slot: str, text: str, markup=None):
    """Slotdagi rasm/GIF bilan yuboradi; media bo'lmasa yoki xato bo'lsa oddiy matn yuboradi."""
    candidates: list[tuple[str, str]] = []
    cur = await get_slot(slot)
    if cur:
        candidates.append(cur)
    elif slot == "start" and config.START_IMG:
        candidates.append(("photo", config.START_IMG))

    for kind, fid in candidates:
        try:
            if kind == "photo":
                return await bot.send_photo(chat_id, fid, caption=text, reply_markup=markup)
            if kind == "animation":
                return await bot.send_animation(chat_id, fid, caption=text, reply_markup=markup)
            if kind == "video":
                return await bot.send_video(chat_id, fid, caption=text, reply_markup=markup)
        except Exception:  # noqa: BLE001
            continue
    return await bot.send_message(chat_id, text, reply_markup=markup)


async def reply_with_media(msg, slot: str, text: str, markup=None):
    """Buyruq xabariga javob sifatida slotdagi rasm/GIF bilan yuboradi (yo'q bo'lsa — oddiy matn bilan)."""
    candidates: list[tuple[str, str]] = []
    cur = await get_slot(slot)
    if cur:
        candidates.append(cur)
    elif slot in ("start", "ping") and config.START_IMG:
        candidates.append(("photo", config.START_IMG))
    for kind, fid in candidates:
        try:
            if kind == "photo":
                return await msg.reply_photo(fid, caption=text, reply_markup=markup)
            if kind == "animation":
                return await msg.reply_animation(fid, caption=text, reply_markup=markup)
            if kind == "video":
                return await msg.reply_video(fid, caption=text, reply_markup=markup)
        except Exception:  # noqa: BLE001
            continue
    return await msg.reply(text, reply_markup=markup)
''')

# ══════════ MODUL: strings.py ══════════
_load('strings', r'''LANGS = {"uz": "🇺🇿 O‘zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}

S = {
    "uz": {
        "start": "👋 Salom, {name}! 🎵\n\n<b>{bot}</b> guruhingizning ovozli chatida musiqa va video ijro etadi.\n\nBuyruqlar uchun /help, ijro uchun guruhda <code>/play qo‘shiq nomi</code> yozing.",
        "help": (
            "🎧 <b>Buyruqlar</b>\n\n"
            "/play <i>nom yoki havola</i> — musiqa ijro etish\n"
            "/vplay <i>nom yoki havola</i> — video ijro etish\n"
            "/pause · /resume · /skip · /end\n"
            "/loop · /seek · /seekback · /shuffle · /speed — ijroni boshqarish\n"
            "/queue — navbat\n"
            "/settings — sozlamalar\n"
            "/auth · /unauth · /authusers — ruxsat berilgan foydalanuvchilar\n"
            "/verify on|off — qo‘shilish so‘rovlarini tasdiqlash\n"
            "/ping — bot tezligi"
        ),
        "welcome": (
            "🎵 <b>{bot}</b> qo‘shilgani uchun rahmat!\n\n"
            "👤 Qo‘shgan: {by}\n📌 Guruh: <b>{title}</b>\n🆔 Chat ID: <code>{cid}</code>\n\n"
            "Menga <b>ovozli chatni boshqarish</b>, <b>xabarlarni o‘chirish</b> va <b>foydalanuvchilarni taklif qilish</b> ruxsatlarini bering, so‘ng <code>/play qo‘shiq nomi</code> yozing."
        ),
        "searching": "🔄 | So‘rovingiz bajarilmoqda...",
        "notfound": "😕 Hech narsa topilmadi.\nImloni tekshiring yoki ijrochi nomini boshqacha yozib ko‘ring (masalan lotin ↔️ kirill).",
        "downloading": "⏳ | Keyingi qo‘shiq yuklab olinmoqda...\n\n🎧 Nomi: <b>{title}</b>",
        "queued": "➕ <b>Navbatga qo‘shildi</b>\n\n🔢 O‘rin: <b>#{pos}</b>\n🎵 Nomi: <b>{title}</b>\n👤 Qo‘shgan: {by}",
        "playing": "<blockquote>➡️ <b>STREAMING STARTED | ENJOY MUSIC</b>\n▶️ <b>TRACK</b> : {title}\n⏱ <b>DURATION</b> : <code>{dur}</code>\n👤 <b>REQUESTER</b> : {by}</blockquote>",
        "paused": "⏸ | Ijro vaqtincha to‘xtatildi.\n\nTo‘xtatgan: {by}",
        "resumed": "▶️ | Ijro davom ettirildi.\n\nDavom ettirgan: {by}",
        "skipped": "⏭ O‘tkazib yuborgan: {by}",
        "ended": "⏹ | Ijro tugatildi.\n\nTugatgan: {by}",
        "nothing": "❌ Hozir hech narsa ijro etilmayapti.",
        "no_vc": "No active video chat found.\n\nPlease start one and try again.",
        "admin_only": "🔒 Bu amal faqat adminlar yoki ruxsat berilgan foydalanuvchilar uchun.",
        "usage": "ℹ️ Foydalanish: <code>/{cmd} qo‘shiq nomi yoki havola</code>",
        "too_long": "⏱ Bu trek juda uzun (limit: {limit} daqiqa).",
        "yt_blocked": "⚠️ YouTube hozir so‘rovni qabul qilmadi. Iltimos, birozdan so‘ng qayta urinib ko‘ring.",
        "error": "❌ Ijro qilib bo‘lmadi. Boshqa qo‘shiq bilan urinib ko‘ring.",
        "asst_banned": "🚫 Yordamchi akkaunt guruhdan bloklangan. Blokdan chiqaring.",
        "asst_fail": "⚠️ Yordamchi akkauntni guruhga qo‘sha olmadim. Menga «Foydalanuvchilarni taklif qilish» ruxsatini bering yoki yordamchini qo‘lda qo‘shing.",
        "queue_empty": "📭 Navbat bo‘sh.",
        "queue_title": "📜 <b>Navbat</b>",
        "queue_now": "▶️ Hozir: {title}",
        "settings": "⚙️ <b>Sozlamalar paneli — {title}</b>\n\n🌐 Til: <b>{lang}</b>\n👑 Faol rejim: <b>{mode}</b>\n\n<b>User Mode:</b> guruhning istalgan a’zosi qo‘shiq ijro etishi mumkin.\n<b>Admin Mode:</b> faqat adminlar yoki ruxsat berilgan foydalanuvchilar.\n\nQuyidagi variantlardan birini tanlang 👇",
        "lang_pick": "🌐 Tilni tanlang:",
        "lang_done": "✅ Til o‘zgartirildi: {lang}",
        "mode_done": "✅ Rejim: {mode}",
        "auth_added": "✅ {who} ruxsat berilganlar ro‘yxatiga qo‘shildi.",
        "auth_removed": "✅ {who} ro‘yxatdan o‘chirildi.",
        "auth_usage": "ℹ️ Foydalanuvchi xabariga javob bering yoki ID/@username yozing.",
        "auth_none": "📭 Ruxsat berilgan foydalanuvchilar yo‘q.",
        "auth_title": "👥 <b>Ruxsat berilgan foydalanuvchilar</b>",
        "ping": "🏓 Pong! <b>{ms} ms</b>",
        "stats": "📊 <b>Statistika</b>\n\n💬 Guruhlar: <b>{chats}</b>\n👤 Foydalanuvchilar: <b>{users}</b>\n🎧 Faol ovozli chatlar: <b>{active}</b>\n🎵 Jami ijrolar: <b>{plays}</b>",
        "private_only_group": "ℹ️ Bu buyruq faqat guruhlarda ishlaydi.",
        "b_add": "➕ Guruhga qo‘shish",
        "b_settings": "⚙️ Sozlamalar / Yordam",
        "b_updates": "📢 Yangiliklar",
        "b_support": "💬 Yordam guruhi",
        "b_lang": "🌐 Til",
        "b_auth": "👥 Ruxsatlar",
        "b_back": "⬅️ Orqaga",
        "b_close": "✖️ Yopish",
        "b_user": "User Mode",
        "b_admin": "Admin Mode",
    },
    "ru": {
        "start": "👋 Привет, {name}! 🎵\n\n<b>{bot}</b> проигрывает музыку и видео в голосовом чате вашей группы.\n\nКоманды — /help, воспроизведение — <code>/play название</code> в группе.",
        "help": (
            "🎧 <b>Команды</b>\n\n"
            "/play <i>название или ссылка</i> — музыка\n"
            "/vplay <i>название или ссылка</i> — видео\n"
            "/pause · /resume · /skip · /end\n"
            "/loop · /seek · /seekback · /shuffle · /speed — управление воспроизведением\n"
            "/queue — очередь\n"
            "/settings — настройки\n"
            "/auth · /unauth · /authusers — доверенные пользователи\n"
            "/verify on|off — проверка заявок на вступление\n"
            "/ping — скорость бота"
        ),
        "welcome": (
            "🎵 Спасибо, что добавили <b>{bot}</b>!\n\n"
            "👤 Добавил: {by}\n📌 Группа: <b>{title}</b>\n🆔 Chat ID: <code>{cid}</code>\n\n"
            "Выдайте мне права <b>управления голосовыми чатами</b>, <b>удаления сообщений</b> и <b>приглашения пользователей</b>, затем используйте <code>/play название</code>."
        ),
        "searching": "🔄 | Ваш запрос выполняется...",
        "notfound": "😕 Ничего не найдено.\nПроверьте написание или попробуйте другое имя исполнителя.",
        "downloading": "⏳ | Загружается следующий трек...\n\n🎧 Название: <b>{title}</b>",
        "queued": "➕ <b>Добавлено в очередь</b>\n\n🔢 Позиция: <b>#{pos}</b>\n🎵 Название: <b>{title}</b>\n👤 Добавил: {by}",
        "playing": "<blockquote>➡️ <b>STREAMING STARTED | ENJOY MUSIC</b>\n▶️ <b>TRACK</b> : {title}\n⏱ <b>DURATION</b> : <code>{dur}</code>\n👤 <b>REQUESTER</b> : {by}</blockquote>",
        "paused": "⏸ | Воспроизведение приостановлено.\n\nОстановил: {by}",
        "resumed": "▶️ | Воспроизведение продолжено.\n\nПродолжил: {by}",
        "skipped": "⏭ Пропустил: {by}",
        "ended": "⏹ | Воспроизведение завершено.\n\nЗавершил: {by}",
        "nothing": "❌ Сейчас ничего не играет.",
        "no_vc": "No active video chat found.\n\nPlease start one and try again.",
        "admin_only": "🔒 Только для админов и доверенных пользователей.",
        "usage": "ℹ️ Использование: <code>/{cmd} название или ссылка</code>",
        "too_long": "⏱ Трек слишком длинный (лимит: {limit} мин).",
        "yt_blocked": "⚠️ YouTube сейчас отклонил запрос. Попробуйте позже.",
        "error": "❌ Не удалось воспроизвести. Попробуйте другой трек.",
        "asst_banned": "🚫 Помощник заблокирован в группе. Разблокируйте его.",
        "asst_fail": "⚠️ Не удалось добавить помощника в группу. Дайте мне право приглашать пользователей или добавьте помощника вручную.",
        "queue_empty": "📭 Очередь пуста.",
        "queue_title": "📜 <b>Очередь</b>",
        "queue_now": "▶️ Сейчас: {title}",
        "settings": "⚙️ <b>Панель настроек — {title}</b>\n\n🌐 Язык: <b>{lang}</b>\n👑 Режим: <b>{mode}</b>\n\n<b>User Mode:</b> любой участник может включать музыку.\n<b>Admin Mode:</b> только админы и доверенные пользователи.\n\nВыберите вариант 👇",
        "lang_pick": "🌐 Выберите язык:",
        "lang_done": "✅ Язык изменён: {lang}",
        "mode_done": "✅ Режим: {mode}",
        "auth_added": "✅ {who} добавлен в список доверенных.",
        "auth_removed": "✅ {who} удалён из списка.",
        "auth_usage": "ℹ️ Ответьте на сообщение пользователя или укажите ID/@username.",
        "auth_none": "📭 Доверенных пользователей нет.",
        "auth_title": "👥 <b>Доверенные пользователи</b>",
        "ping": "🏓 Pong! <b>{ms} мс</b>",
        "stats": "📊 <b>Статистика</b>\n\n💬 Группы: <b>{chats}</b>\n👤 Пользователи: <b>{users}</b>\n🎧 Активные голосовые чаты: <b>{active}</b>\n🎵 Всего воспроизведений: <b>{plays}</b>",
        "private_only_group": "ℹ️ Эта команда работает только в группах.",
        "b_add": "➕ Добавить в группу",
        "b_settings": "⚙️ Настройки / Помощь",
        "b_updates": "📢 Новости",
        "b_support": "💬 Поддержка",
        "b_lang": "🌐 Язык",
        "b_auth": "👥 Доступ",
        "b_back": "⬅️ Назад",
        "b_close": "✖️ Закрыть",
        "b_user": "User Mode",
        "b_admin": "Admin Mode",
    },
    "en": {
        "start": "👋 Hello, {name}! 🎵\n\n<b>{bot}</b> streams music and video in your group's voice chat.\n\nUse /help for commands, or send <code>/play song name</code> in a group.",
        "help": (
            "🎧 <b>Commands</b>\n\n"
            "/play <i>name or link</i> — play music\n"
            "/vplay <i>name or link</i> — play video\n"
            "/pause · /resume · /skip · /end\n"
            "/loop · /seek · /seekback · /shuffle · /speed — playback control\n"
            "/queue — show queue\n"
            "/settings — settings\n"
            "/auth · /unauth · /authusers — authorized users\n"
            "/verify on|off — join request verification\n"
            "/ping — bot latency"
        ),
        "welcome": (
            "🎵 Thanks for adding <b>{bot}</b>!\n\n"
            "👤 Added by: {by}\n📌 Group: <b>{title}</b>\n🆔 Chat ID: <code>{cid}</code>\n\n"
            "Give me <b>Manage voice chats</b>, <b>Delete messages</b> and <b>Invite users</b> rights, then send <code>/play song name</code>."
        ),
        "searching": "🔄 | Processing your request...",
        "notfound": "😕 Nothing found.\nCheck the spelling or try a different artist name.",
        "downloading": "⏳ | Loading the next track...\n\n🎧 Title: <b>{title}</b>",
        "queued": "➕ <b>Added to queue</b>\n\n🔢 Position: <b>#{pos}</b>\n🎵 Title: <b>{title}</b>\n👤 Added by: {by}",
        "playing": "<blockquote>➡️ <b>STREAMING STARTED | ENJOY MUSIC</b>\n▶️ <b>TRACK</b> : {title}\n⏱ <b>DURATION</b> : <code>{dur}</code>\n👤 <b>REQUESTER</b> : {by}</blockquote>",
        "paused": "⏸ | Playback paused.\n\nPaused by: {by}",
        "resumed": "▶️ | Playback resumed.\n\nResumed by: {by}",
        "skipped": "⏭ Skipped by: {by}",
        "ended": "⏹ | Playback ended.\n\nEnded by: {by}",
        "nothing": "❌ Nothing is playing right now.",
        "no_vc": "No active video chat found.\n\nPlease start one and try again.",
        "admin_only": "🔒 Only admins or authorized users can do this.",
        "usage": "ℹ️ Usage: <code>/{cmd} song name or link</code>",
        "too_long": "⏱ This track is too long (limit: {limit} min).",
        "yt_blocked": "⚠️ YouTube rejected the request. Please try again shortly.",
        "error": "❌ Couldn't play it. Try another track.",
        "asst_banned": "🚫 The assistant account is banned in this group. Unban it first.",
        "asst_fail": "⚠️ I couldn't add the assistant to the group. Give me the Invite users right or add the assistant manually.",
        "queue_empty": "📭 The queue is empty.",
        "queue_title": "📜 <b>Queue</b>",
        "queue_now": "▶️ Now: {title}",
        "settings": "⚙️ <b>Settings panel — {title}</b>\n\n🌐 Language: <b>{lang}</b>\n👑 Mode: <b>{mode}</b>\n\n<b>User Mode:</b> any member can play songs.\n<b>Admin Mode:</b> only admins or authorized users.\n\nChoose an option below 👇",
        "lang_pick": "🌐 Choose a language:",
        "lang_done": "✅ Language updated: {lang}",
        "mode_done": "✅ Mode: {mode}",
        "auth_added": "✅ {who} added to the authorized list.",
        "auth_removed": "✅ {who} removed from the list.",
        "auth_usage": "ℹ️ Reply to a user's message or send an ID/@username.",
        "auth_none": "📭 No authorized users.",
        "auth_title": "👥 <b>Authorized users</b>",
        "ping": "🏓 Pong! <b>{ms} ms</b>",
        "stats": "📊 <b>Statistics</b>\n\n💬 Groups: <b>{chats}</b>\n👤 Users: <b>{users}</b>\n🎧 Active voice chats: <b>{active}</b>\n🎵 Total plays: <b>{plays}</b>",
        "private_only_group": "ℹ️ This command only works in groups.",
        "b_add": "➕ Add me to a group",
        "b_settings": "⚙️ Settings / Help",
        "b_updates": "📢 Updates",
        "b_support": "💬 Support",
        "b_lang": "🌐 Language",
        "b_auth": "👥 Auth users",
        "b_back": "⬅️ Back",
        "b_close": "✖️ Close",
        "b_user": "User Mode",
        "b_admin": "Admin Mode",
    },
}


def t(lang: str, key: str, **kw) -> str:
    text = S.get(lang, S["uz"]).get(key) or S["en"].get(key, key)
    return text.format(**kw) if kw else text


_EXTRA = {
    "uz": {
        "no_asst": "⚠️ Hozircha yordamchi akkaunt ulanmagan. Bot egasiga xabar berildi.",
        "banned_user": "🚫 Siz botdan foydalanishdan chetlatilgansiz.",
        "queue_full": "📭 Navbat to‘lgan (limit: {limit}).",
        "loop_on": "🔁 | Joriy qo‘shiq takrorlanadi (cheksiz).\n\nYoqqan: {by}",
        "loop_off": "➡️ | Takrorlash o‘chirildi.\n\nO‘chirgan: {by}",
        "loop_n": "🔁 | Joriy qo‘shiq yana <b>{n}</b> marta takrorlanadi.\n\nYoqqan: {by}",
        "loop_usage": "ℹ️ Foydalanish: <code>/loop on</code> · <code>/loop off</code> · <code>/loop 1-10</code>",
        "seek_usage": "ℹ️ Foydalanish: <code>/{cmd} 30</code> (soniya) yoki <code>/{cmd} 1:30</code>",
        "seeked": "⏩ | Ijro <b>{pos}</b> ga o‘tkazildi.\n\nO‘tkazgan: {by}",
        "seek_range": "⚠️ Bu qiymat trek davomiyligidan oshadi ({dur}).",
        "shuffled": "🔀 | Navbat aralashtirildi ({n} ta trek).\n\nAralashtirgan: {by}",
        "shuffle_few": "ℹ️ Aralashtirish uchun navbatda kamida 2 ta trek bo‘lishi kerak.",
        "speed_set": "⚡ | Tezlik: <b>{speed}x</b>\n\nO‘zgartirgan: {by}",
        "speed_usage": "ℹ️ Foydalanish: <code>/speed 0.5-2.0</code> yoki <code>/speed 1</code> (oddiy). Hozir: <b>{cur}x</b>",
        "speed_video": "⚠️ Video ijroda tezlikni o‘zgartirib bo‘lmaydi (faqat audio).",
        "busy": "⏳ Trek yuklanmoqda, biroz kuting va qayta urinib ko‘ring.",
        "verify_msg": "<u><b>Click on the button below to verify yourself.</b></u>\n\n<i>Your request to join the group will be approved shortly.</i>",
        "verify_ok": "✅ Tasdiqlandi! So‘rovingiz qabul qilindi.",
        "verify_fail": "⚠️ Tasdiqlab bo‘lmadi. So‘rov eskirgan bo‘lishi mumkin.",
        "verify_on": "✅ Qo‘shilish so‘rovlarini tasdiqlash yoqildi. Botda «Foydalanuvchilarni taklif qilish» ruxsati bo‘lishi shart.",
        "verify_off": "✅ Qo‘shilish so‘rovlarini tasdiqlash o‘chirildi.",
        "verify_status": "ℹ️ Tasdiqlash hozir: <b>{state}</b>. O‘zgartirish: <code>/verify on</code> yoki <code>/verify off</code>",
        "b_verify": "Verify",
    },
    "ru": {
        "no_asst": "⚠️ Помощник пока не подключён. Владелец бота уведомлён.",
        "banned_user": "🚫 Вам запрещено пользоваться ботом.",
        "queue_full": "📭 Очередь заполнена (лимит: {limit}).",
        "loop_on": "🔁 | Текущий трек будет повторяться (бесконечно).\n\nВключил: {by}",
        "loop_off": "➡️ | Повтор выключен.\n\nВыключил: {by}",
        "loop_n": "🔁 | Текущий трек повторится ещё <b>{n}</b> раз.\n\nВключил: {by}",
        "loop_usage": "ℹ️ Использование: <code>/loop on</code> · <code>/loop off</code> · <code>/loop 1-10</code>",
        "seek_usage": "ℹ️ Использование: <code>/{cmd} 30</code> (секунды) или <code>/{cmd} 1:30</code>",
        "seeked": "⏩ | Воспроизведение перемотано на <b>{pos}</b>.\n\nПеремотал: {by}",
        "seek_range": "⚠️ Это значение больше длительности трека ({dur}).",
        "shuffled": "🔀 | Очередь перемешана ({n} треков).\n\nПеремешал: {by}",
        "shuffle_few": "ℹ️ Для перемешивания в очереди должно быть минимум 2 трека.",
        "speed_set": "⚡ | Скорость: <b>{speed}x</b>\n\nИзменил: {by}",
        "speed_usage": "ℹ️ Использование: <code>/speed 0.5-2.0</code> или <code>/speed 1</code> (обычная). Сейчас: <b>{cur}x</b>",
        "speed_video": "⚠️ Для видео изменить скорость нельзя (только аудио).",
        "busy": "⏳ Трек загружается, подождите немного и повторите.",
        "verify_msg": "<u><b>Click on the button below to verify yourself.</b></u>\n\n<i>Your request to join the group will be approved shortly.</i>",
        "verify_ok": "✅ Подтверждено! Ваша заявка принята.",
        "verify_fail": "⚠️ Не удалось подтвердить. Возможно, заявка устарела.",
        "verify_on": "✅ Проверка заявок на вступление включена. У бота должно быть право «Приглашать пользователей».",
        "verify_off": "✅ Проверка заявок на вступление выключена.",
        "verify_status": "ℹ️ Проверка сейчас: <b>{state}</b>. Изменить: <code>/verify on</code> или <code>/verify off</code>",
        "b_verify": "Verify",
    },
    "en": {
        "no_asst": "⚠️ No assistant account is connected yet. The bot owner was notified.",
        "banned_user": "🚫 You are banned from using this bot.",
        "queue_full": "📭 The queue is full (limit: {limit}).",
        "loop_on": "🔁 | The current track will repeat (endless).\n\nEnabled by: {by}",
        "loop_off": "➡️ | Loop disabled.\n\nDisabled by: {by}",
        "loop_n": "🔁 | The current track will repeat <b>{n}</b> more time(s).\n\nEnabled by: {by}",
        "loop_usage": "ℹ️ Usage: <code>/loop on</code> · <code>/loop off</code> · <code>/loop 1-10</code>",
        "seek_usage": "ℹ️ Usage: <code>/{cmd} 30</code> (seconds) or <code>/{cmd} 1:30</code>",
        "seeked": "⏩ | Playback moved to <b>{pos}</b>.\n\nMoved by: {by}",
        "seek_range": "⚠️ That is beyond the track length ({dur}).",
        "shuffled": "🔀 | Queue shuffled ({n} tracks).\n\nShuffled by: {by}",
        "shuffle_few": "ℹ️ You need at least 2 queued tracks to shuffle.",
        "speed_set": "⚡ | Speed: <b>{speed}x</b>\n\nChanged by: {by}",
        "speed_usage": "ℹ️ Usage: <code>/speed 0.5-2.0</code> or <code>/speed 1</code> (normal). Now: <b>{cur}x</b>",
        "speed_video": "⚠️ Speed can't be changed for video playback (audio only).",
        "busy": "⏳ A track is loading, wait a moment and try again.",
        "verify_msg": "<u><b>Click on the button below to verify yourself.</b></u>\n\n<i>Your request to join the group will be approved shortly.</i>",
        "verify_ok": "✅ Verified! Your join request was approved.",
        "verify_fail": "⚠️ Couldn't verify. The request may have expired.",
        "verify_on": "✅ Join request verification is on. The bot needs the «Invite users» right.",
        "verify_off": "✅ Join request verification is off.",
        "verify_status": "ℹ️ Verification is currently: <b>{state}</b>. Change: <code>/verify on</code> or <code>/verify off</code>",
        "b_verify": "Verify",
    },
}
for _l, _d in _EXTRA.items():
    S[_l].update(_d)
''')

# ══════════ MODUL: cobalt.py ══════════
_load('cobalt', r'''"""Cobalt API orqali YouTube'dan audio/video olish (o'zingizning Railway'dagi cobalt `api` servisi).

Railway Variables (botda):
  COBALT_API_URL = https://api-production-xxxx.up.railway.app   (cobalt'ning `api` servisi, `web` EMAS)
  COBALT_API_KEY = (ixtiyoriy) cobalt'da API_AUTH_REQUIRED yoqilgan bo'lsa

Tartib: bot Cobalt'dan havola oladi → audioni vaqtinchalik faylga yuklaydi → yordamchi akkaunt shu fayldan ijro qiladi.
Cobalt ishlamasa, bot avtomatik yt-dlp → Deezer → SoundCloud zaxiralariga o'tadi.
"""
import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
import time
import urllib.error
import urllib.request

import config

log = logging.getLogger("cobalt")

MAX_BYTES = 120 * 1024 * 1024
_UA = "Mozilla/5.0 (compatible; MusicBot/1.0)"
_sem = asyncio.Semaphore(3)  # bir vaqtda 3 tadan ortiq yuklash cobalt'ni bo'g'masligi uchun


class CobaltError(Exception):
    def __init__(self, kind: str, detail: str = ""):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind  # notfound | blocked | other
        self.detail = detail


def enabled() -> bool:
    return bool(config.COBALT_API_URL)


def _auth() -> dict:
    key = config.COBALT_API_KEY
    if not key:
        return {}
    if key.lower().startswith(("api-key ", "bearer ")):
        return {"Authorization": key}
    return {"Authorization": f"Api-Key {key}"}


def _classify(code: str) -> CobaltError:
    c = (code or "").lower()
    if any(s in c for s in (
        "youtube.login", "youtube.decipher", "token_expired", "fetch.rate", "rate_exceeded",
        "fetch.fail", "fetch.critical", "error.api.auth", "capacity",
    )):
        return CobaltError("blocked", code)
    if any(s in c for s in (
        "unavailable", ".private", ".age", ".region", "fetch.empty", "content.video.live",
        "no_matching_format", "link.invalid", "link.unsupported",
    )):
        return CobaltError("notfound", code)
    return CobaltError("other", code)


def _post_sync(payload: dict) -> dict:
    headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": _UA, **_auth()}
    req = urllib.request.Request(
        config.COBALT_API_URL + "/", data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=config.COBALT_TIMEOUT) as resp:
            code, raw = resp.status, resp.read(2_000_000)
    except urllib.error.HTTPError as exc:  # cobalt xatolarni 4xx + JSON tanasi bilan qaytaradi
        code, raw = exc.code, exc.read(2_000_000)
    except (urllib.error.URLError, OSError) as exc:  # TimeoutError ham shu yerga tushadi
        raise CobaltError("other", f"ulanib bo'lmadi: {exc}") from exc
    try:
        data = json.loads(raw.decode("utf-8", "ignore"))
    except ValueError:
        raise CobaltError("other", f"HTTP {code}: JSON emas (COBALT_API_URL `api` servisiga qaratilganmi?)") from None
    if not isinstance(data, dict):
        raise CobaltError("other", f"HTTP {code}: kutilmagan javob")
    return data


def _unpack(data: dict, audio: bool) -> dict:
    status = data.get("status")
    if status in ("tunnel", "redirect") and data.get("url"):
        return {"url": data["url"], "filename": data.get("filename") or ""}
    if status == "picker":
        if audio and data.get("audio"):
            return {"url": data["audio"], "filename": data.get("audioFilename") or ""}
        for item in data.get("picker") or []:
            if isinstance(item, dict) and item.get("url"):
                return {"url": item["url"], "filename": ""}
        raise CobaltError("notfound", "picker bo'sh")
    if status == "error":
        raise _classify(str((data.get("error") or {}).get("code") or "unknown"))
    raise CobaltError("other", f"kutilmagan javob: {str(data)[:150]}")


def _request_sync(page_url: str, audio: bool, fmt: str, quality: str) -> dict:
    payload: dict = {"url": page_url}
    if audio:
        payload.update(downloadMode="audio", audioFormat=fmt)
    else:
        payload.update(videoQuality=quality, youtubeVideoCodec="h264")
    data = _post_sync(payload)
    if data.get("status") == "error" and "invalid_body" in str((data.get("error") or {}).get("code") or ""):
        # cobalt versiyasi qo'shimcha maydonlarni qabul qilmasa — eng sodda so'rov bilan qayta urinamiz
        data = _post_sync({"url": page_url, "downloadMode": "audio" if audio else "auto"})
    return _unpack(data, audio)


def _download_sync(url: str, filename: str) -> str:
    folder = tempfile.mkdtemp(prefix="cb_")
    try:
        ext = os.path.splitext(filename or "")[1].lower().lstrip(".")
        if not re.fullmatch(r"[a-z0-9]{2,5}", ext):
            ext = "audio"
        path = os.path.join(folder, f"track.{ext}")
        size = 0
        deadline = time.monotonic() + config.COBALT_DL_TIMEOUT
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp, open(path, "wb") as f:
                while True:
                    chunk = resp.read(1 << 16)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise CobaltError("other", "fayl juda katta")
                    if time.monotonic() > deadline:
                        raise CobaltError("other", "yuklash vaqti tugadi")
                    f.write(chunk)
        except urllib.error.HTTPError as exc:
            raise CobaltError("other", f"yuklash HTTP {exc.code}") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise CobaltError("other", f"yuklab bo'lmadi: {exc}") from exc
        if size < 10_000:
            raise CobaltError("other", f"fayl juda kichik ({size} bayt)")
        return path
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)
        raise


def _info_sync() -> str:
    req = urllib.request.Request(config.COBALT_API_URL + "/", headers={"Accept": "application/json", "User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read(500_000)
    except (urllib.error.URLError, OSError) as exc:
        raise CobaltError("other", f"ulanib bo'lmadi: {exc}") from exc
    try:
        ver = (json.loads(raw.decode("utf-8", "ignore")).get("cobalt") or {}).get("version")
    except (ValueError, AttributeError):
        ver = None
    if not ver:
        raise CobaltError("other", "bu cobalt API emas (COBALT_API_URL `api` servisiga qaratilganmi, `web`ga emas?)")
    return str(ver)


async def fetch_audio(page_url: str, fmt: str = "best") -> str:
    """Audioni vaqtinchalik fayl qilib yuklaydi. Fayl yo'lini qaytaradi; papkasini (os.path.dirname) chaqiruvchi o'chiradi."""
    async with _sem:
        res = await asyncio.to_thread(_request_sync, page_url, True, fmt, "720")
        return await asyncio.to_thread(_download_sync, res["url"], res["filename"])


async def stream_url(page_url: str, video: bool = False) -> str:
    """Faylga yuklamasdan, to'g'ridan-to'g'ri oqim havolasini qaytaradi (video uchun)."""
    res = await asyncio.to_thread(_request_sync, page_url, not video, "best", "720")
    return res["url"]


async def info() -> str:
    """Cobalt versiyasi (ulanishni tekshirish uchun)."""
    return await asyncio.to_thread(_info_sync)
''')

# ══════════ MODUL: yt.py ══════════
_load('yt', r'''"""Qidiruv va oqim havolasi: YouTube (cookies bilan), bloklansa SoundCloud zaxirasi.

Qo'shimcha: Spotify/Apple Music/Resso trek havolalari (nom bo'yicha YouTube'dan topiladi) va mp3 yuklab olish.
"""
import asyncio
import html as _html
import os
import re
import shutil
import json
import logging
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

import yt_dlp

import cobalt
import config

log = logging.getLogger("yt")

URL_RE = re.compile(r"^https?://", re.I)
# audio to'g'ridan-to'g'ri olinmaydigan servislar: faqat nomini olib YouTube'dan qidiramiz
META_RE = re.compile(r"(open\.spotify\.com|music\.apple\.com|resso\.(?:com|app)|m\.resso\.com)", re.I)
SPOTIFY_TRACK_RE = re.compile(r"open\.spotify\.com/(?:intl-[a-z-]+/)?track/", re.I)

_NOISE_RE = re.compile(
    r"[\(\[\{][^\)\]\}]*(official|video|lyrics?|audio|clip|klip|rasmiy|hd|4k|mv)[^\)\]\}]*[\)\]\}]", re.I
)


@dataclass
class Track:
    vid: str
    title: str
    url: str  # sahifa havolasi (stream havolasi tez eskiradi, shuning uchun ijro oldidan olinadi)
    duration: int
    thumb: str
    by: str
    by_id: int
    video: bool = False
    src: str = "youtube"  # youtube | soundcloud | deezer (deezer = hali topilmagan, nom bo'yicha qidiriladi)
    status: Any = field(default=None, repr=False)  # "qidirilmoqda" xabari
    tmp: str = ""  # vaqtinchalik audio fayl yo'li (Deezer zaxirasi); ijro tugagach o'chiriladi


class YTError(Exception):
    def __init__(self, kind: str, detail: str = ""):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind  # notfound | blocked | other
        self.detail = detail


def _classify(exc: Exception) -> YTError:
    msg = str(exc).lower()
    if any(s in msg for s in ("sign in to confirm", "not a bot", "cookies", "confirm your age", "429", "too many requests")):
        return YTError("blocked", str(exc))
    if any(s in msg for s in ("video unavailable", "private video", "no video results", "not found")):
        return YTError("notfound", str(exc))
    return YTError("other", str(exc))


def _opts(**extra) -> dict:
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "socket_timeout": 20,
        "retries": 3,
        # yangi yt-dlp YouTube imzosini yechish uchun JS runtime talab qiladi (Dockerfile'da nodejs bor)
        "js_runtimes": {"node": {}},
    }
    if os.path.exists(config.COOKIES_FILE):
        opts["cookiefile"] = config.COOKIES_FILE
    opts.update(extra)
    return opts


def _thumb(vid: str) -> str:
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"


def clean_title(title: str) -> str:
    """'(Official Video)', '[Lyrics]' kabi shovqinni olib tashlaydi — SoundCloud'da yaxshiroq topiladi."""
    out = _NOISE_RE.sub("", title or "")
    out = re.sub(r"\s{2,}", " ", out).strip(" -|·")
    return out or (title or "")


# ───────────── Spotify / Apple Music / Resso: faqat nomni olish ─────────────
def _og(page: str, prop: str) -> str:
    m = re.search(r'<meta[^>]+property=["\']og:%s["\'][^>]+content=["\']([^"\']*)["\']' % prop, page, re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:%s["\']' % prop, page, re.I)
    return _html.unescape(m.group(1)).strip() if m else ""


def _meta_to_query(url: str) -> str:
    """Spotify/Apple/Resso sahifasidan 'ijrochi - nom' qidiruv so'rovini yasaydi."""
    if "open.spotify.com" in url and not SPOTIFY_TRACK_RE.search(url):
        raise YTError("notfound", "faqat trek havolalari qo'llanadi")
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
                     "Accept-Language": "en-US,en;q=0.8"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            page = resp.read(300_000).decode("utf-8", "ignore")
    except Exception as exc:  # noqa: BLE001
        raise YTError("notfound", f"havola ochilmadi: {exc}") from exc

    title = _og(page, "title")
    desc = _og(page, "description")
    if not title:
        raise YTError("notfound", "nom topilmadi")
    title = re.sub(r"\s+(?:on|by)\s+Apple Music.*$", "", title, flags=re.I)
    title = re.sub(r"\s*-\s*(?:Single|EP|Album)\b.*$", "", title, flags=re.I)
    title = re.sub(r"\s*\|\s*Spotify$", "", title, flags=re.I)
    artist = ""
    if "spotify" in url.lower() and "·" in desc:  # "Ijrochi · Nom · 2020"
        artist = desc.split("·")[0].strip()
    query = f"{artist} {title}".strip() if artist and artist.lower() not in title.lower() else title
    return query


def _pick(entries: list[dict]) -> dict:
    """Qidiruv natijasidan eng mosini tanlaydi: jonli efir, Shorts va juda uzun videolarni chetlab o'tadi."""
    limit = config.DURATION_LIMIT_MIN * 60

    def ok(e: dict) -> bool:
        if e.get("live_status") in ("is_live", "is_upcoming"):
            return False
        d = e.get("duration")
        return True if d is None else 30 <= d <= limit

    for e in entries:
        if ok(e):
            return e
    return entries[0]


_WEB_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _yt_id(url: str) -> str:
    if "youtu" not in url.lower():
        return ""
    m = re.search(r"(?:youtu\.be/|[?&]v=|/shorts/|/embed/|/live/)([\w-]{11})", url)
    return m.group(1) if m else ""


def _oembed_track(url: str, by: str, by_id: int, video: bool) -> "Track | None":
    """yt-dlp havola ma'lumotini ololmasa (IP bloklangan): YouTube oEmbed'dan nomni olamiz, ijroni cobalt qiladi."""
    vid = _yt_id(url)
    if not vid:
        return None
    try:
        api = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(
            f"https://www.youtube.com/watch?v={vid}", safe=""
        )
        req = urllib.request.Request(api, headers={"User-Agent": _WEB_UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read(200_000).decode("utf-8", "ignore"))
    except Exception:  # noqa: BLE001
        return None
    return Track(
        vid=vid,
        title=data.get("title") or "YouTube",
        url=f"https://www.youtube.com/watch?v={vid}",
        duration=0,
        thumb=_thumb(vid),
        by=by, by_id=by_id, video=video,
    )


def _walk(node):
    if isinstance(node, dict):
        vr = node.get("videoRenderer")
        if isinstance(vr, dict):
            yield vr
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _clock_to_sec(text: str) -> int | None:
    parts = (text or "").strip().split(":")
    if not text or len(parts) > 3 or not all(p.isdigit() for p in parts):
        return None
    sec = 0
    for p in parts:
        sec = sec * 60 + int(p)
    return sec


def _parse_results(page: str) -> list[dict]:
    m = re.search(r"var ytInitialData\s*=\s*(\{.*?\});\s*</script>", page, re.S)
    if not m:
        return []
    data = json.loads(m.group(1))
    out: list[dict] = []
    seen: set[str] = set()
    for vr in _walk(data):
        vid = vr.get("videoId")
        if not vid or vid in seen:
            continue
        seen.add(vid)
        title_obj = vr.get("title") or {}
        title = "".join(r.get("text", "") for r in title_obj.get("runs", [])) or title_obj.get("simpleText") or ""
        dur = _clock_to_sec((vr.get("lengthText") or {}).get("simpleText") or "")
        entry: dict = {"id": vid, "title": title or "Unknown", "duration": dur}
        if dur is None:  # davomiyligi yo'q = jonli efir yoki premyera
            entry["live_status"] = "is_live"
        out.append(entry)
    return out


def _web_search(query: str) -> list[dict]:
    """yt-dlp qidiruvi ishlamasa zaxira: YouTube qidiruv sahifasidan to'g'ridan-to'g'ri natijalarni o'qiydi."""
    url = (
        "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query) + "&sp=EgIQAQ%3D%3D"
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": _WEB_UA, "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1; SOCS=CAI"},
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        page = resp.read(3_000_000).decode("utf-8", "ignore")
    return _parse_results(page)[:6]


def _yt_search(query: str, by: str, by_id: int, video: bool) -> Track:
    if URL_RE.match(query):
        try:
            with yt_dlp.YoutubeDL(_opts(extract_flat=False)) as ydl:
                info = ydl.extract_info(query, download=False, process=False)
        except Exception:  # noqa: BLE001
            fb = _oembed_track(query, by, by_id, video) if cobalt.enabled() else None
            if fb is None:
                raise
            return fb  # yt-dlp bloklangan: nomni oEmbed'dan oldik, ijroni cobalt qiladi
        if info and info.get("entries"):
            info = next(iter(info["entries"]), None)
        if not info:
            raise YTError("notfound")
        vid = info.get("id") or ""
        is_sc = "soundcloud" in (info.get("extractor_key") or "").lower() or "soundcloud.com" in query
        return Track(
            vid=vid,
            title=info.get("title") or "Unknown",
            url=info.get("webpage_url") or info.get("url") or query,
            duration=int(info.get("duration") or 0),
            thumb="" if is_sc else (_thumb(vid) if vid else ""),
            by=by, by_id=by_id, video=video,
            src="soundcloud" if is_sc else "youtube",
        )

    entries: list[dict] = []
    first_exc: Exception | None = None
    try:
        with yt_dlp.YoutubeDL(_opts(extract_flat=True)) as ydl:
            res = ydl.extract_info(f"ytsearch6:{query}", download=False)
        entries = [e for e in (res or {}).get("entries", []) if e and e.get("id")]
    except Exception as exc:  # noqa: BLE001
        first_exc = exc
    if not entries:
        # yt-dlp qidiruvi ishlamadi (IP bloklangan bo'lishi mumkin) — qidiruv sahifasidan oddiy usulda olamiz
        try:
            entries = _web_search(query)
        except Exception as exc:  # noqa: BLE001
            log.info("web qidiruv ishlamadi: %s", exc)
    if not entries:
        if first_exc is not None:
            raise first_exc
        raise YTError("notfound")
    e = _pick(entries)
    vid = e["id"]
    return Track(
        vid=vid,
        title=e.get("title") or "Unknown",
        url=f"https://www.youtube.com/watch?v={vid}",
        duration=int(e.get("duration") or 0),
        thumb=_thumb(vid),
        by=by, by_id=by_id, video=video,
    )


def _sc_search(query: str, by: str, by_id: int) -> Track:
    with yt_dlp.YoutubeDL(_opts(extract_flat=True)) as ydl:
        res = ydl.extract_info(f"scsearch3:{query}", download=False)
    entries = [e for e in (res or {}).get("entries", []) if e and (e.get("url") or e.get("webpage_url"))]
    if not entries:
        raise YTError("notfound")
    e = entries[0]
    return Track(
        vid=str(e.get("id") or ""),
        title=e.get("title") or query,
        url=e.get("webpage_url") or e.get("url"),
        duration=int(e.get("duration") or 0),
        thumb="",
        by=by, by_id=by_id, video=False, src="soundcloud",
    )


def _search_sync(query: str, by: str, by_id: int, video: bool) -> Track:
    query = query.strip()
    if URL_RE.match(query) and META_RE.search(query):
        query = _meta_to_query(query)  # endi oddiy matnli qidiruv

    try:
        return _yt_search(query, by, by_id, video)
    except Exception as exc:  # noqa: BLE001
        err = exc if isinstance(exc, YTError) else _classify(exc)
        # YouTube bloklasa yoki topilmasa — SoundCloud'dan qidiramiz (havola bo'lsa emas)
        if err.kind in ("blocked", "other", "notfound") and not URL_RE.match(query) and not video:
            if getattr(config, "DEEZER_BOT", ""):
                # YouTube qidiruvi ishlamadi: ijro paytida avval Deezer bot, keyin SoundCloud sinaladi
                return Track(vid="", title=query, url="", duration=0, thumb="", by=by, by_id=by_id, src="deezer")
            try:
                return _sc_search(query, by, by_id)
            except Exception:  # noqa: BLE001
                pass
        raise err from exc


# yt-dlp YouTube mijozlari tez-tez o'zgaradi: 1-urinish standart, 2-urinish muqobil mijozlar bilan
_CLIENT_FALLBACK = {"youtube": {"player_client": ["tv", "web_safari", "mweb"]}}


def _extract_stream(url: str, fmt: str, alt_client: bool = False) -> tuple[str, dict | None]:
    extra: dict[str, Any] = {"format": fmt}
    if alt_client:
        extra["extractor_args"] = _CLIENT_FALLBACK
    with yt_dlp.YoutubeDL(_opts(**extra)) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise YTError("other", "ma'lumot olinmadi")
    stream = info.get("url")
    if not stream and info.get("requested_formats"):
        stream = info["requested_formats"][0].get("url")
    if not stream:
        raise YTError("other", "stream url topilmadi")
    return stream, info.get("http_headers")


def _resolve_sync(track: Track, mode: str = "auto") -> tuple[str, dict | None]:
    """mode: auto = YouTube, bloklansa SoundCloud | youtube = faqat YouTube | soundcloud = to'g'ridan-to'g'ri SoundCloud."""
    audio_fmt = "bestaudio[ext=m4a]/bestaudio/best"
    video_fmt = "best[height<=720][vcodec!=none][acodec!=none]/best[height<=720]/best"
    fmt = video_fmt if (track.video and track.src == "youtube") else audio_fmt

    if mode == "soundcloud":
        try:
            alt = _sc_search(clean_title(track.title), track.by, track.by_id)
            stream, headers = _extract_stream(alt.url, audio_fmt)
        except YTError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise _classify(exc) from exc
        track.src, track.url = "soundcloud", alt.url
        if not track.duration:
            track.duration = alt.duration
        return stream, headers

    last: YTError | None = None
    for attempt in range(2):
        try:
            return _extract_stream(track.url, fmt, alt_client=(attempt == 1 and track.src == "youtube"))
        except YTError as exc:
            last = exc
        except Exception as exc:  # noqa: BLE001
            last = _classify(exc)

    # YouTube bloklasa: SoundCloud'dan shu nom bilan topib ko'ramiz
    if mode == "auto" and track.src == "youtube" and last and last.kind in ("blocked", "other") and not track.video:
        try:
            alt = _sc_search(clean_title(track.title), track.by, track.by_id)
            stream, headers = _extract_stream(alt.url, audio_fmt)
            track.src, track.url = "soundcloud", alt.url
            return stream, headers
        except Exception:  # noqa: BLE001
            pass
    raise last or YTError("other", "unknown")


async def search(query: str, by: str, by_id: int, video: bool = False) -> Track:
    return await asyncio.to_thread(_search_sync, query, by, by_id, video)


async def resolve(track: Track, mode: str = "auto") -> tuple[str, dict | None]:
    return await asyncio.to_thread(_resolve_sync, track, mode)


# ───────────── mp3 yuklab olish (/song) ─────────────
def _download_one(url: str, outdir: str, alt_client: bool = False) -> tuple[str, dict]:
    extra: dict[str, Any] = dict(
        skip_download=False,
        format="bestaudio[ext=m4a]/bestaudio/best",
        outtmpl=os.path.join(outdir, "%(id)s.%(ext)s"),
        postprocessors=[{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        noprogress=True,
    )
    if alt_client:
        extra["extractor_args"] = _CLIENT_FALLBACK
    with yt_dlp.YoutubeDL(_opts(**extra)) as ydl:
        info = ydl.extract_info(url, download=True)
    mp3 = [f for f in os.listdir(outdir) if f.lower().endswith(".mp3")]
    if not mp3:
        raise YTError("other", "mp3 fayl hosil bo'lmadi (ffmpeg bormi?)")
    return os.path.join(outdir, mp3[0]), (info or {})


def _download_sync(track: Track) -> tuple[str, dict]:
    outdir = tempfile.mkdtemp(prefix="song_")
    try:
        if track.src == "deezer" or not track.url:  # YouTube qidiruvi ishlamagan: SoundCloud'dan olamiz
            alt = _sc_search(clean_title(track.title), track.by, track.by_id)
            path, info = _download_one(alt.url, outdir)
            track.src, track.url = "soundcloud", alt.url
            return path, info
        last: YTError | None = None
        for attempt in range(2):
            try:
                return _download_one(track.url, outdir, alt_client=(attempt == 1 and track.src == "youtube"))
            except YTError as exc:
                last = exc
            except Exception as exc:  # noqa: BLE001
                last = _classify(exc)
        if track.src == "youtube" and last and last.kind in ("blocked", "other"):
            try:
                alt = _sc_search(clean_title(track.title), track.by, track.by_id)
                path, info = _download_one(alt.url, outdir)
                track.src, track.url = "soundcloud", alt.url
                return path, info
            except Exception:  # noqa: BLE001
                pass
        raise last or YTError("other", "unknown")
    except BaseException:
        shutil.rmtree(outdir, ignore_errors=True)
        raise


async def download_audio(track: Track) -> tuple[str, dict]:
    """(mp3 yo'li, info) qaytaradi. Chaqiruvchi tugagach `shutil.rmtree(os.path.dirname(path))` qilishi kerak."""
    if cobalt.enabled() and track.src == "youtube" and track.url:
        try:
            return await cobalt.fetch_audio(track.url, fmt="mp3"), {}
        except Exception as exc:  # noqa: BLE001
            log.warning("cobalt yuklay olmadi, yt-dlp'ga o'tilmoqda: %s", exc)
    return await asyncio.to_thread(_download_sync, track)


def fmt_duration(sec: int) -> str:
    if not sec:
        return "LIVE"
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
''')

# ══════════ MODUL: deezer.py ══════════
_load('deezer', r'''"""Zaxira manba: @DeezerMusicBot (YouTube bloklaganda).

Bot boshqa botga yoza olmaydi, shuning uchun yordamchi akkaunt (oddiy foydalanuvchi sifatida):
1) botga inline qidiruv yuboradi, 2) birinchi audio natijani o'zining «Saqlangan xabarlar»iga yuboradi,
3) audio faylni yuklab oladi, 4) xabarni o'chiradi. Fayl yo'li ovozli chatga uzatiladi.
"""
import asyncio
import logging
import os
import shutil
import tempfile
import time

import config

log = logging.getLogger("deezer")

GAP = 6.0  # bir akkaunt uchun so'rovlar orasidagi minimal pauza (FloodWait'dan saqlanish)
MAX_BYTES = 60 * 1024 * 1024

_sem = asyncio.Semaphore(1)  # bir vaqtda faqat bitta so'rov
_last: dict[int, float] = {}
_started: set[int] = set()  # botga /start yuborgan yordamchilar


class DeezerError(Exception):
    pass


def enabled() -> bool:
    return bool(getattr(config, "DEEZER_BOT", ""))


async def _last_id(client) -> int:
    async for m in client.get_chat_history("me", limit=1):
        return m.id
    return 0


def _is_audio(m) -> bool:
    if m.audio or m.voice:
        return True
    doc = m.document
    return bool(doc and (doc.mime_type or "").startswith("audio"))


async def _wait_audio(client, base_id: int, timeout: float = 35.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        await asyncio.sleep(1.5)
        async for m in client.get_chat_history("me", limit=6):
            if m.id <= base_id:
                break
            if _is_audio(m):
                return m
    raise DeezerError("audio kelmadi (vaqt tugadi)")


async def fetch(asst, query: str) -> tuple[str, dict]:
    """(mp3/audio fayl yo'li, {'title','performer','duration'}) qaytaradi. Chaqiruvchi tugagach papkani o'chiradi."""
    bot = getattr(config, "DEEZER_BOT", "")
    if not bot:
        raise DeezerError("o'chirilgan (DEEZER_BOT bo'sh)")
    client = asst.client

    async with _sem:
        wait = GAP - (time.monotonic() - _last.get(asst.uid, 0.0))
        if wait > 0:
            await asyncio.sleep(wait)
        _last[asst.uid] = time.monotonic()

        tmpdir = tempfile.mkdtemp(prefix="dz_")
        msg = None
        try:
            if asst.uid not in _started:  # ba'zi botlar avval /start bosilishini talab qiladi
                try:
                    await client.send_message(bot, "/start")
                    await asyncio.sleep(2)
                except Exception as exc:  # noqa: BLE001
                    log.info("deezer /start yuborilmadi: %s", exc)
                _started.add(asst.uid)

            try:
                res = await asyncio.wait_for(client.get_inline_bot_results(bot, query), 20)
            except asyncio.TimeoutError as exc:
                raise DeezerError("bot javob bermadi") from exc
            except Exception as exc:  # noqa: BLE001
                raise DeezerError(f"qidiruv xatosi: {type(exc).__name__}") from exc

            results = list(getattr(res, "results", None) or [])
            if not results:
                raise DeezerError("natija topilmadi")
            pick = next((r for r in results if getattr(r, "type", "") in ("audio", "document")), results[0])

            base = await _last_id(client)
            try:
                await client.send_inline_bot_result("me", res.query_id, pick.id)
            except Exception as exc:  # noqa: BLE001
                raise DeezerError(f"natija yuborilmadi: {type(exc).__name__}") from exc

            msg = await _wait_audio(client, base)
            media = msg.audio or msg.document or msg.voice
            if getattr(media, "file_size", 0) and media.file_size > MAX_BYTES:
                raise DeezerError("fayl juda katta")

            path = await asyncio.wait_for(
                client.download_media(msg, file_name=os.path.join(tmpdir, "track.mp3")), 90
            )
            if not path or not os.path.exists(path):
                raise DeezerError("fayl yuklanmadi")

            audio = msg.audio
            meta = {
                "title": (getattr(audio, "title", None) or getattr(media, "file_name", None) or "").strip(),
                "performer": (getattr(audio, "performer", None) or "").strip(),
                "duration": int(getattr(audio, "duration", 0) or getattr(media, "duration", 0) or 0),
            }
            return path, meta
        except BaseException:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise
        finally:
            if msg is not None:
                try:
                    await client.delete_messages("me", msg.id)
                except Exception:  # noqa: BLE001
                    pass
''')

# ══════════ MODUL: assistants.py ══════════
_load('assistants', r'''"""Yordamchi akkauntlar puli: bir nechta Telegram akkaunt, har biri o'z PyTgCalls klienti bilan.

Owner panel orqali telefon raqam (kod + 2FA) yoki session string bilan qo'shiladi.
Sessiyalar bazada Fernet bilan shifrlangan holda saqlanadi.
"""
import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Awaitable, Callable

from pyrogram import Client
from pyrogram.errors import (
    PasswordHashInvalid,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    SessionPasswordNeeded,
)
from pytgcalls import PyTgCalls
from pytgcalls.types import ChatUpdate, StreamEnded

import config
import crypto
import db

log = logging.getLogger("assistants")


@dataclass
class Assistant:
    uid: int
    name: str
    client: Client
    call: PyTgCalls


items: dict[int, Assistant] = {}
failed: dict[int, str] = {}  # uid -> xato matni (ishga tushmaganlar)
_cooldown: dict[int, float] = {}  # uid -> shu vaqtgacha (monotonic) dam oladi (FloodWait)

_on_end: Callable[[int], Awaitable[None]] | None = None
_on_closed: Callable[[int], Awaitable[None]] | None = None


def set_callbacks(on_end, on_closed) -> None:
    global _on_end, _on_closed
    _on_end, _on_closed = on_end, on_closed


def cool(uid: int, seconds: int) -> None:
    """Akkauntni vaqtincha 'dam olishga' qo'yadi (FloodWait va h.k.)."""
    _cooldown[uid] = time.monotonic() + max(5, min(int(seconds), 3600))


def is_cooling(uid: int) -> bool:
    return _cooldown.get(uid, 0) > time.monotonic()


def _new_client(session: str, tag: str) -> Client:
    return Client(
        f"asst-{tag}",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=session,
        in_memory=True,
        sleep_threshold=30,  # 30 soniyagacha FloodWait'ni Pyrogram o'zi kutadi
    )


async def _safe(cb, chat_id: int) -> None:
    """Callback xatosi PyTgCalls hodisa tsiklini buzmasligi uchun."""
    if not cb:
        return
    try:
        await cb(chat_id)
    except Exception:  # noqa: BLE001
        log.exception("callback xatosi (chat %s)", chat_id)


def _is_audio_end(update) -> bool:
    """Video oqimda audio va video uchun ikkita StreamEnded keladi — faqat audionikini olamiz."""
    kind = getattr(update, "stream_type", None)
    type_cls = getattr(StreamEnded, "Type", None)
    if kind is None or type_cls is None:
        return True
    return kind == type_cls.AUDIO


async def _start(session: str) -> Assistant:
    client = _new_client(session, "x")
    await client.start()
    try:
        me = await client.get_me()
        if me.is_bot:
            raise ValueError("Bu bot sessiyasi. Yordamchi uchun oddiy Telegram akkaunt kerak.")
        call = PyTgCalls(client)

        @call.on_update()
        async def _updates(_, update):
            chat_id = getattr(update, "chat_id", None)
            if chat_id is None:
                return
            if isinstance(update, StreamEnded):
                if _is_audio_end(update):
                    await _safe(_on_end, chat_id)
            elif isinstance(update, ChatUpdate):
                closed = (
                    ChatUpdate.Status.CLOSED_VOICE_CHAT
                    | ChatUpdate.Status.KICKED
                    | ChatUpdate.Status.LEFT_GROUP
                )
                if update.status & closed:
                    await _safe(_on_closed, chat_id)

        await call.start()
    except BaseException:
        try:
            await client.stop()
        except Exception:  # noqa: BLE001
            pass
        raise

    name = " ".join(x for x in (me.first_name, me.last_name) if x) or str(me.id)
    asst = Assistant(uid=me.id, name=name, client=client, call=call)
    old = items.get(me.id)
    items[me.id] = asst
    failed.pop(me.id, None)
    if old is not None:  # xuddi shu akkaunt qayta ulangan bo'lsa, eskisini to'xtatamiz
        try:
            await old.client.stop()
        except Exception:  # noqa: BLE001
            pass
    return asst


async def load_all() -> None:
    for uid, name, _phone, enc_session in await db.list_assistants():
        try:
            await _start(crypto.dec(enc_session))
        except Exception as exc:  # noqa: BLE001
            failed[uid] = str(exc)[:200]
            log.error("assistant %s (%s) ishga tushmadi: %s", uid, name, exc)


async def load_missing() -> int:
    """Bazadagi, lekin hali ishga tushmagan yordamchilarni ishga tushiradi (API ID/HASH keyin kiritilganda). Soni qaytadi."""
    n = 0
    for uid, name, _phone, enc_session in await db.list_assistants():
        if uid in items:
            continue
        try:
            await _start(crypto.dec(enc_session))
            n += 1
        except Exception as exc:  # noqa: BLE001
            failed[uid] = str(exc)[:200]
            log.error("assistant %s (%s) ishga tushmadi: %s", uid, name, exc)
    return n


async def retry_failed() -> list[int]:
    """Ishga tushmay qolgan yordamchilarni qayta urinib ko'radi. Muvaffaqiyatlilar uid ro'yxatini qaytaradi."""
    ok: list[int] = []
    if not failed:
        return ok
    for uid, name, _phone, enc_session in await db.list_assistants():
        if uid in items or uid not in failed:
            continue
        try:
            await _start(crypto.dec(enc_session))
            ok.append(uid)
            log.info("assistant %s (%s) qayta ulandi", uid, name)
        except Exception as exc:  # noqa: BLE001
            failed[uid] = str(exc)[:200]
    return ok


async def watchdog(interval: int = 300) -> None:
    """Har 5 daqiqada ishga tushmay qolgan yordamchilarni qayta ulashga urinadi."""
    while True:
        await asyncio.sleep(interval)
        try:
            await retry_failed()
        except Exception:  # noqa: BLE001
            log.exception("watchdog xatosi")


async def add_session(session: str, phone: str = "") -> Assistant:
    asst = await _start(session)
    await db.add_assistant(asst.uid, asst.name, phone, crypto.enc(session))
    return asst


async def remove(uid: int) -> None:
    asst = items.pop(uid, None)
    failed.pop(uid, None)
    _cooldown.pop(uid, None)
    if asst:
        try:
            await asst.client.stop()
        except Exception:  # noqa: BLE001
            pass
    await db.del_assistant(uid)


async def stop_all() -> None:
    for asst in list(items.values()):
        try:
            await asst.client.stop()
        except Exception:  # noqa: BLE001
            pass
    items.clear()


async def for_chat(chat_id: int, loads: dict[int, int], exclude: tuple[int, ...] = ()) -> Assistant | None:
    """Guruhga biriktirilgan yordamchini qaytaradi; yo'q (yoki exclude'da) bo'lsa eng bo'shini biriktiradi."""
    aid = await db.get_assignment(chat_id)
    if aid in items and aid not in exclude:
        return items[aid]
    pool = [a for a in items.values() if a.uid not in exclude]
    if not pool:
        return None
    best = min(pool, key=lambda a: (is_cooling(a.uid), loads.get(a.uid, 0)))
    await db.set_assignment(chat_id, best.uid)
    return best


# ───────────── telefon orqali kirish (owner panel) ─────────────
@dataclass
class _Login:
    client: Client
    phone: str
    code_hash: str


_pending: dict[int, _Login] = {}


async def login_begin(owner_id: int, phone: str) -> None:
    await login_cancel(owner_id)
    client = Client("asst-login", api_id=config.API_ID, api_hash=config.API_HASH, in_memory=True)
    await client.connect()
    try:
        sent = await client.send_code(phone)
    except Exception:
        await client.disconnect()
        raise
    _pending[owner_id] = _Login(client, phone, sent.phone_code_hash)


async def login_code(owner_id: int, code: str) -> str:
    """'done' yoki '2fa' qaytaradi."""
    lg = _pending[owner_id]
    code = "".join(ch for ch in code if ch.isdigit())  # "1 2 3 4 5" ham ishlaydi
    try:
        await lg.client.sign_in(lg.phone, lg.code_hash, code)
    except SessionPasswordNeeded:
        return "2fa"
    except (PhoneCodeInvalid, PhoneCodeExpired):
        raise
    return await _finish(owner_id)


async def login_password(owner_id: int, password: str) -> str:
    lg = _pending[owner_id]
    try:
        await lg.client.check_password(password)
    except PasswordHashInvalid:
        raise
    return await _finish(owner_id)


async def _finish(owner_id: int) -> str:
    lg = _pending.pop(owner_id)
    try:
        session = await lg.client.export_session_string()
    finally:
        try:
            await lg.client.disconnect()
        except Exception:  # noqa: BLE001
            pass
    await add_session(session, lg.phone)
    return "done"


async def login_cancel(owner_id: int) -> None:
    lg = _pending.pop(owner_id, None)
    if lg:
        try:
            await lg.client.disconnect()
        except Exception:  # noqa: BLE001
            pass
''')

# ══════════ MODUL: player.py ══════════
_load('player', r'''"""Navbat va ijro mexanizmi (aiogram bot + yordamchi akkaunt orqali ovozli chat)."""
import asyncio
import html
import logging
import os
import random
import shutil
import tempfile
import time
from datetime import datetime, timedelta, timezone

import pyrogram.errors as perr
from aiogram.enums import ChatMemberStatus
from aiogram.types import InlineKeyboardMarkup as Markup
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import AudioQuality, MediaStream, VideoQuality

import assistants
import config
import core
import db
import cobalt
import deezer
import media
import yt
from premium import B
from strings import t

log = logging.getLogger("player")


def _exc(name: str) -> type:
    """Pyrogram versiyasida bo'lmagan xato nomi import xatosini bermasligi uchun."""
    return getattr(perr, name, type(name, (Exception,), {}))


FloodWait = _exc("FloodWait")
UserAlreadyParticipant = _exc("UserAlreadyParticipant")
InviteRequestSent = _exc("InviteRequestSent")
UserChannelsTooMuch = _exc("UserChannelsTooMuch")
ChannelsTooMuch = _exc("ChannelsTooMuch")
UserBannedInChannel = _exc("UserBannedInChannel")


class AssistantError(Exception):
    """kind: none | banned | fail (eski kodlar bilan mos). reason: aniq sabab (hint() uchun)."""

    def __init__(self, kind: str, reason: str = "", wait: int = 0):
        super().__init__(f"{kind}:{reason}")
        self.kind = kind
        self.reason = reason or kind
        self.wait = wait


HINTS = {
    "none": "⚠️ Yordamchi akkaunt ulanmagan. Bot egasi /panel orqali yordamchi qo'shishi kerak.",
    "no_rights": (
        "⚠️ Yordamchi akkauntni guruhga qo'sha olmadim.\n"
        "Botni guruhda <b>admin</b> qiling va <b>«Foydalanuvchilarni taklif qilish»</b> huquqini bering."
    ),
    "banned": (
        "🚫 Yordamchi akkaunt guruhdan bloklangan.\n"
        "Uni blokdan chiqaring yoki botga <b>«Foydalanuvchilarni bloklash»</b> huquqini bering."
    ),
    "flood": "⏳ Yordamchi akkaunt vaqtincha cheklangan. Birozdan keyin urinib ko'ring.",
    "too_many": "⚠️ Yordamchi akkaunt juda ko'p guruhga a'zo. Bot egasi yangi yordamchi qo'shishi kerak.",
    "join_request": "⚠️ Guruhda a'zolik tasdiqlanadi. Yordamchi akkauntning so'rovini qabul qiling.",
}
HINT_DEFAULT = "⚠️ Yordamchi akkauntni guruhga qo'sha olmadim. Botni admin qiling va qayta urinib ko'ring."


def hint(exc: AssistantError) -> str:
    """Foydalanuvchiga tushunarli, texnik so'zsiz yo'riqnoma."""
    return HINTS.get(exc.reason, HINT_DEFAULT)


class State:
    def __init__(self) -> None:
        self.queue: list[yt.Track] = []
        self.current: yt.Track | None = None
        self.card = None
        self.asst: assistants.Assistant | None = None
        self.lock = asyncio.Lock()
        self.started: float = 0.0  # joriy trek boshlangan vaqt (monotonic)
        self.src: tuple | None = None  # (url, headers): loop/seek/speed uchun joriy manba
        self.loop: int = 0  # 0 = o'chiq, -1 = cheksiz, N > 0 = yana N marta
        self.speed: float = 1.0
        self.offset: float = 0.0  # manbadagi boshlang'ich pozitsiya (soniya)
        self.paused_at: float = 0.0  # pauza boshlangan vaqt (monotonic), 0 = pauzada emas
        self.paused_total: float = 0.0
        self.spd_dir: str = ""  # tezlik uchun vaqtinchalik fayl papkasi


_states: dict[int, State] = {}


def state(chat_id: int) -> State:
    return _states.setdefault(chat_id, State())


def active_count() -> int:
    return sum(1 for s in _states.values() if s.current)


def loads() -> dict[int, int]:
    out: dict[int, int] = {}
    for s in _states.values():
        if s.current and s.asst:
            out[s.asst.uid] = out.get(s.asst.uid, 0) + 1
    return out


def chats_of(assistant_uid: int) -> list[int]:
    return [cid for cid, s in _states.items() if s.asst and s.asst.uid == assistant_uid]


def position(chat_id: int) -> float:
    """Joriy trekning hozirgi pozitsiyasi (soniya): pauza va tezlik hisobga olinadi."""
    st = state(chat_id)
    if not st.current:
        return 0.0
    now = time.monotonic()
    paused = st.paused_total + ((now - st.paused_at) if st.paused_at else 0.0)
    played = max(0.0, now - st.started - paused)
    return st.offset + played * st.speed


def controls(lang: str) -> Markup:
    return Markup(
        inline_keyboard=[
            [
                B("PAUSE", cb="ctl:pause", style="primary"),
                B("RESUME", cb="ctl:resume", style="primary"),
                B("SKIP", cb="ctl:skip", style="primary"),
            ],
            [
                B(
                    "ADD ME",
                    url=f"https://t.me/{core.BOT_USERNAME}?startgroup=true&admin=manage_video_chats+delete_messages+invite_users",
                    style="success",
                ),
                B("CLOSE", cb="close", style="danger"),
            ],
        ]
    )


async def log_owner(text: str) -> None:
    target = config.LOG_CHAT or config.OWNER_LIST[0]
    try:
        await core.bot.send_message(target, text)
    except Exception:  # noqa: BLE001
        pass


async def notice(chat_id: int, text: str, ttl: int = 10) -> None:
    """Qisqa xabar yuboradi va ttl soniyadan keyin o'chiradi."""
    try:
        msg = await core.bot.send_message(chat_id, text)
    except Exception:  # noqa: BLE001
        return

    async def _later() -> None:
        await asyncio.sleep(ttl)
        try:
            await msg.delete()
        except Exception:  # noqa: BLE001
            pass

    asyncio.create_task(_later())


# ───────────── yordamchini guruhga qo'shish ─────────────
async def _member_status(chat_id: int, asst: assistants.Assistant) -> str:
    """member | banned | absent | unknown"""
    try:  # bot admin bo'lsa, a'zolikni ko'ra oladi
        m = await core.bot.get_chat_member(chat_id, asst.uid)
        if m.status == ChatMemberStatus.KICKED:
            return "banned"
        if m.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
            return "member"
        if m.status == ChatMemberStatus.RESTRICTED and getattr(m, "is_member", True):
            return "member"
        return "absent"
    except Exception:  # noqa: BLE001
        pass
    try:  # bot ko'ra olmasa, yordamchining o'zidan so'raymiz
        m = await asst.client.get_chat_member(chat_id, "me")
        name = str(getattr(m.status, "name", m.status)).upper()
        if "BANNED" in name:
            return "banned"
        if any(s in name for s in ("MEMBER", "ADMIN", "OWNER", "RESTRICTED")):
            return "member"
    except Exception:  # noqa: BLE001
        pass
    return "unknown"


async def _try_unban(chat_id: int, asst: assistants.Assistant) -> bool:
    try:
        await core.bot.unban_chat_member(chat_id, asst.uid, only_if_banned=True)
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("unban bo'lmadi %s: %s", chat_id, exc)
        return False


async def _targets(chat_id: int, chat):
    """Qo'shilish uchun nishonlar: ochiq username → yangi bir martalik havola → asosiy havola."""
    username = getattr(chat, "username", None)
    if username:
        yield username
    try:
        # export_chat_invite_link ESKI havolani bekor qiladi — shuning uchun alohida bir martalik havola yaratamiz
        link = await core.bot.create_chat_invite_link(
            chat_id,
            name="Assistant",
            expire_date=datetime.now(timezone.utc) + timedelta(minutes=15),
            member_limit=1,
        )
        yield link.invite_link
    except Exception as exc:  # noqa: BLE001
        log.warning("taklif havolasi yaratilmadi (%s): %s", chat_id, exc)
    primary = getattr(chat, "invite_link", None)
    if primary:
        yield primary


async def _try_join(asst: assistants.Assistant, target: str) -> str:
    """ok | request | bad. Qayta urinib bo'lmaydigan holatlarda AssistantError ko'taradi."""
    try:
        await asst.client.join_chat(target)
        return "ok"
    except UserAlreadyParticipant:
        return "ok"
    except InviteRequestSent:
        return "request"
    except FloodWait as exc:
        raise AssistantError("fail", "flood", wait=int(getattr(exc, "value", 60) or 60)) from exc
    except (UserChannelsTooMuch, ChannelsTooMuch) as exc:
        raise AssistantError("fail", "too_many") from exc
    except UserBannedInChannel as exc:
        raise AssistantError("banned", "banned") from exc
    except Exception as exc:  # noqa: BLE001
        log.warning("join_chat(%s) bo'lmadi: %s", target, exc)
        return "bad"


async def _approve_request(chat_id: int, asst: assistants.Assistant) -> bool:
    """Yordamchining a'zolik so'rovini (guruhda 'so'rov bilan qo'shilish' yoqilgan bo'lsa) bot o'zi tasdiqlaydi.

    So'rov Telegram serveriga yetib borguncha biroz kutiladi; handlers_user'dagi hodisa ushlagichi avval
    tasdiqlab qo'ygan bo'lsa ham (xato qaytadi) a'zolik tekshirilib, muvaffaqiyat deb hisoblanadi.
    """
    for delay in (0.5, 1.5, 3.0):
        await asyncio.sleep(delay)
        try:
            await core.bot.approve_chat_join_request(chat_id, asst.uid)
            return True
        except Exception as exc:  # noqa: BLE001
            log.info("join request tasdiqlash %s: %s", chat_id, exc)
            if await _member_status(chat_id, asst) == "member":
                return True
    return False


async def _join(chat_id: int, asst: assistants.Assistant) -> None:
    chat = None
    try:
        chat = await core.bot.get_chat(chat_id)
    except Exception:  # noqa: BLE001
        pass

    produced = 0
    async for target in _targets(chat_id, chat):
        produced += 1
        res = await _try_join(asst, target)
        if res == "ok":
            return
        if res == "request":
            if await _approve_request(chat_id, asst):
                return
            log.warning("join request tasdiqlanmadi %s", chat_id)
            raise AssistantError("fail", "join_request")
    raise AssistantError("fail", "no_rights" if produced == 0 else "join_failed")


async def _ensure_member(chat_id: int, asst: assistants.Assistant) -> None:
    status = await _member_status(chat_id, asst)
    if status == "member":
        return
    if status == "banned" and not await _try_unban(chat_id, asst):
        raise AssistantError("banned", "banned")
    await _join(chat_id, asst)
    await asyncio.sleep(0.7)


async def ensure_assistant(chat_id: int) -> assistants.Assistant:
    """Guruhga yordamchini qo'shadi. Biri ishlamasa (FloodWait, ban, juda ko'p guruh) boshqasiga o'tadi."""
    st = state(chat_id)
    tried: list[int] = []
    last: AssistantError | None = None
    while True:
        asst = await assistants.for_chat(chat_id, loads(), exclude=tuple(tried))
        if asst is None:
            raise last or AssistantError("none")
        try:
            await _ensure_member(chat_id, asst)
            st.asst = asst
            return asst
        except AssistantError as exc:
            last = exc
            tried.append(asst.uid)
            log.warning("assistant %s chat %s: %s", asst.uid, chat_id, exc.reason)
            if exc.reason == "flood":
                assistants.cool(asst.uid, exc.wait or 60)
            if exc.reason in ("no_rights", "join_request"):
                raise  # bot huquqi/guruh sozlamasi muammosi: boshqa yordamchi yordam bermaydi
            if exc.reason == "too_many":
                await log_owner(f"⚠️ Yordamchi <code>{asst.uid}</code> juda ko'p guruhga a'zo. Yangi yordamchi qo'shing.")


async def add(chat_id: int, track: yt.Track, status_msg=None) -> int:
    """0 qaytarsa darhol ijro boshlanadi, aks holda navbatdagi o'rin."""
    st = state(chat_id)
    track.status = status_msg
    # navbat bo'sh bo'lishi shart: aks holda ketma-ket ikki /play ikkinchisi birinchisini bosib ketardi
    waiting = st.current is None and not st.lock.locked()  # ijro boshlanishi kutilmoqda
    idle = waiting and not st.queue
    pending_head = waiting and bool(st.queue)  # navbat boshidagi trek hozir ijro boshlaydi
    st.queue.append(track)
    if idle:
        asyncio.create_task(play_next(chat_id))
        return 0
    return len(st.queue) - (1 if pending_head else 0)


async def _delete(msg) -> None:
    if msg is None:
        return
    try:
        await msg.delete()
    except Exception:  # noqa: BLE001
        pass


async def _leave(chat_id: int) -> None:
    st = state(chat_id)
    if not st.asst:
        return
    try:
        await st.asst.call.leave_call(chat_id)
    except Exception:  # noqa: BLE001
        pass


def _is_video_stream(track: yt.Track) -> bool:
    return bool(track.video and track.src == "youtube")


async def _start_stream(chat_id: int, track: yt.Track, url: str, headers, start: float = 0.0) -> None:
    if _is_video_stream(track):
        kwargs = dict(audio_parameters=AudioQuality.HIGH, video_parameters=VideoQuality.HD_720p)
    else:
        kwargs = dict(audio_parameters=AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE)
    extra = {"ffmpeg_parameters": f"-ss {int(start)}"} if start >= 1 else {}
    try:
        stream = MediaStream(url, headers=headers, **kwargs, **extra)
    except TypeError:  # eski versiyalarda headers yoki ffmpeg_parameters yo'q
        try:
            stream = MediaStream(url, **kwargs, **extra)
        except TypeError:
            if extra:
                raise RuntimeError("PyTgCalls versiyasi seek'ni qo'llamaydi (ffmpeg_parameters yo'q)")
            stream = MediaStream(url, **kwargs)
    await state(chat_id).asst.call.play(chat_id, stream)


async def _try_create_vc(chat_id: int) -> bool:
    """Ovozli chat yo'q bo'lsa, yordamchi (huquqi bo'lsa) o'zi ochib ko'radi."""
    asst = state(chat_id).asst
    if not asst:
        return False
    try:
        from pyrogram.raw import functions

        peer = await asst.client.resolve_peer(chat_id)
        await asst.client.invoke(functions.phone.CreateGroupCall(peer=peer, random_id=random.randint(1, 2**31 - 1)))
        await asyncio.sleep(1.5)
        return True
    except Exception as exc:  # noqa: BLE001
        log.info("ovozli chat ochilmadi (%s): %s", chat_id, exc)
        return False


async def _play(chat_id: int, track: yt.Track, url: str, headers, start: float = 0.0) -> None:
    """Ijroni boshlaydi: vaqtinchalik xatolarda 3 martagacha qayta urinadi."""
    last: Exception | None = None
    tried_create = False
    for attempt in range(3):
        try:
            await _start_stream(chat_id, track, url, headers, start)
            return
        except NoActiveGroupCall:
            if not tried_create:
                tried_create = True
                if await _try_create_vc(chat_id):
                    continue
            raise
        except FloodWait as exc:
            wait = int(getattr(exc, "value", 5) or 5)
            last = exc
            if wait > 20:
                asst = state(chat_id).asst
                if asst:
                    assistants.cool(asst.uid, wait)
                raise
            await asyncio.sleep(wait + 1)
        except Exception as exc:  # noqa: BLE001
            last = exc
            log.warning("ijro urinishi %d/3 (chat %s): %s", attempt + 1, chat_id, exc)
            await asyncio.sleep(1.5)
    raise last if last else RuntimeError("ijro boshlanmadi")


def _card_title(track: yt.Track) -> str:
    """Kartochkadagi trek nomi: uzun bo'lsa qisqartiriladi, havolasi bo'lsa bosiladigan qilinadi."""
    title = track.title or ""
    if len(title) > 34:
        title = title[:33].rstrip() + "..."
    safe = html.escape(title)
    url = str(track.url or "")
    if url.startswith("http"):
        return f'<a href="{html.escape(url, quote=True)}">{safe}</a>'
    return safe


async def _card(chat_id: int, track: yt.Track, lang: str) -> None:
    st = state(chat_id)
    text = t(
        lang, "playing",
        title=_card_title(track), dur=_dur(track), by=html.escape(track.by),
    )
    markup = controls(lang)
    old = st.card
    msg = None
    if track.thumb:
        try:
            msg = await core.bot.send_photo(chat_id, track.thumb, caption=text, reply_markup=markup)
        except Exception:  # noqa: BLE001
            msg = None
    if msg is None:
        try:
            msg = await media.send_with_media(core.bot, chat_id, "playing", text, markup)
        except Exception:  # noqa: BLE001
            msg = None
    st.card = msg
    await _delete(old)
    await _delete(track.status)
    track.status = None


def _dur(track: yt.Track) -> str:
    return yt.fmt_duration(track.duration) if track.duration else "—"


def _drop_tmp(track: yt.Track | None) -> None:
    """Deezer'dan yuklangan vaqtinchalik faylni o'chiradi."""
    if track is not None and track.tmp:
        shutil.rmtree(os.path.dirname(track.tmp), ignore_errors=True)
        track.tmp = ""


_dz_warned_at = float("-inf")


async def _dz_warn(reason: str) -> None:
    """Deezer zaxirasi ishlamasa, egasiga 10 daqiqada bir marta sababini yozadi."""
    global _dz_warned_at
    if time.monotonic() - _dz_warned_at < 600:
        return
    _dz_warned_at = time.monotonic()
    await log_owner(f"⚠️ Deezer zaxirasi ishlamadi: <code>{html.escape(reason[:200])}</code>\nTekshirish: /dztest nom")


_cb_warned_at = float("-inf")


async def _cb_warn(detail: str) -> None:
    """Cobalt YouTube'dan olib bera olmasa, egasiga 10 daqiqada bir marta sababini yozadi."""
    global _cb_warned_at
    if time.monotonic() - _cb_warned_at < 600:
        return
    _cb_warned_at = time.monotonic()
    await log_owner(
        "⚠️ Cobalt API YouTube'dan olib bera olmadi (zaxira manbalar ishlatiladi).\n"
        f"<code>{html.escape(detail[:300])}</code>\n"
        "Cobalt servisida YouTube cookies yoki YOUTUBE_SESSION_SERVER sozlang. Tekshirish: /cobaltest"
    )


async def _resolve_source(chat_id: int, track: yt.Track) -> tuple[str, dict | None]:
    """Manba tartibi: Cobalt API → YouTube (yt-dlp) → Deezer bot → SoundCloud."""
    use_dz = deezer.enabled() and not track.video
    first_err: yt.YTError | None = None

    if cobalt.enabled() and track.src == "youtube" and track.url:
        try:
            if track.video:  # video: fayl qilmasdan oqim havolasi beriladi
                return await cobalt.stream_url(track.url, video=True), None
            path = await cobalt.fetch_audio(track.url)  # audio: fayl qilib yuklanadi (to'xtab qolmaydi)
            track.tmp = path
            return path, None
        except cobalt.CobaltError as exc:
            log.warning("cobalt (%s): %s", exc.kind, exc.detail[:200])
            if exc.kind == "blocked":
                await _cb_warn(exc.detail)
        except Exception as exc:  # noqa: BLE001
            log.warning("cobalt kutilmagan xato: %s", exc)

    if track.src != "deezer":
        try:
            return await yt.resolve(track, mode="youtube" if (use_dz and track.src == "youtube") else "auto")
        except yt.YTError as exc:
            if not (use_dz and track.src == "youtube" and exc.kind in ("blocked", "other")):
                raise
            first_err = exc  # YouTube rad etdi: darhol Deezer botga o'tamiz

    asst = state(chat_id).asst
    if use_dz and asst is not None:
        try:
            path, meta = await deezer.fetch(asst, yt.clean_title(track.title))
            track.tmp = path
            was_placeholder = track.src == "deezer"
            track.src = "deezer"
            if meta.get("duration") and not track.duration:
                track.duration = meta["duration"]
            if was_placeholder and meta.get("title"):
                track.title = f"{meta['performer']} - {meta['title']}" if meta.get("performer") else meta["title"]
            return path, None
        except Exception as exc:  # noqa: BLE001
            log.warning("deezer zaxirasi ishlamadi: %s", exc)
            await _dz_warn(str(exc))

    try:  # oxirgi zaxira: SoundCloud
        return await yt.resolve(track, mode="soundcloud")
    except yt.YTError:
        if first_err is not None:
            raise first_err
        raise


async def play_next(chat_id: int) -> None:
    st = state(chat_id)
    async with st.lock:
        lang, _ = await db.get_chat(chat_id)
        while st.queue:
            track = st.queue.pop(0)
            try:
                # bot qayta ishga tushgan yoki yordamchi o'chirilgan bo'lsa, qaytadan biriktiramiz
                if st.asst is None or st.asst.uid not in assistants.items:
                    await ensure_assistant(chat_id)
                url, headers = await _resolve_source(chat_id, track)
                await _play(chat_id, track, url, headers)
            except AssistantError as exc:
                log.warning("yordamchi muammosi (chat %s): %s", chat_id, exc.reason)
                _drop_tmp(track)
                st.queue.clear()
                st.current = None
                await _delete(track.status)
                await notice(chat_id, hint(exc), ttl=20)
                return
            except yt.YTError as exc:
                log.warning("resolve failed (%s): %s", exc.kind, exc.detail[:200])
                _drop_tmp(track)
                await notice(chat_id, t(lang, "yt_blocked" if exc.kind == "blocked" else "error"))
                if exc.kind == "blocked":
                    await log_owner(
                        "⚠️ YouTube bloklayapti. Owner panel → 🍪 Cookies orqali yangi cookies.txt yuklang.\n"
                        f"<code>{html.escape(exc.detail[:300])}</code>"
                    )
                await _delete(track.status)
                continue
            except NoActiveGroupCall:
                _drop_tmp(track)
                st.queue.clear()
                st.current = None
                await _delete(track.status)
                await notice(chat_id, t(lang, "no_vc"))
                return
            except Exception as exc:  # noqa: BLE001
                log.exception("play failed: %s", exc)
                _drop_tmp(track)
                await notice(chat_id, t(lang, "error"))
                await _delete(track.status)
                continue

            prev, st.current = st.current, track
            _drop_tmp(prev)  # oldingi trekning vaqtinchalik fayli (yangi oqim boshlangach)
            st.started = time.monotonic()
            st.src = (url, headers)
            st.offset, st.speed, st.loop = 0.0, 1.0, 0
            st.paused_at = st.paused_total = 0.0
            _drop_spd(st)  # oldingi trekning tezlik fayli (yangi oqim boshlangach)
            await db.log_play(chat_id, track.title)
            await _card(chat_id, track, lang)
            return

        # navbat tugadi
        _drop_tmp(st.current)
        _drop_spd(st)
        st.current = None
        st.src = None
        st.loop = 0
        await _leave(chat_id)
        await _delete(st.card)
        st.card = None


async def on_stream_end(chat_id: int) -> None:
    """Trek tugaganda PyTgCalls chaqiradi. Eski oqimdan kechikib kelgan signalni (2 soniya ichida) e'tiborsiz qoldiradi."""
    st = _states.get(chat_id)
    if not st or st.current is None:
        return
    if time.monotonic() - st.started < 2:
        return
    if st.loop != 0 and st.src is not None and not st.lock.locked():
        if st.loop > 0:
            st.loop -= 1
        try:
            await _restart(chat_id, 0.0, st.speed)
            return
        except Exception as exc:  # noqa: BLE001
            log.warning("loop ishlamadi (chat %s): %s", chat_id, exc)
            st.loop = 0
    await play_next(chat_id)


async def skip(chat_id: int) -> bool:
    if not state(chat_id).current:
        return False
    state(chat_id).loop = 0
    await play_next(chat_id)
    return True


async def pause(chat_id: int) -> bool:
    st = state(chat_id)
    if not st.current or not st.asst:
        return False
    try:
        await st.asst.call.pause(chat_id)
        if not st.paused_at:
            st.paused_at = time.monotonic()
        return True
    except Exception:  # noqa: BLE001
        return False


async def resume(chat_id: int) -> bool:
    st = state(chat_id)
    if not st.current or not st.asst:
        return False
    try:
        await st.asst.call.resume(chat_id)
        if st.paused_at:
            st.paused_total += time.monotonic() - st.paused_at
            st.paused_at = 0.0
        return True
    except Exception:  # noqa: BLE001
        return False


async def end(chat_id: int) -> bool:
    st = state(chat_id)
    had = st.current is not None or bool(st.queue)
    st.queue.clear()
    _drop_tmp(st.current)
    _drop_spd(st)
    st.current = None
    st.src = None
    st.loop = 0
    st.speed = 1.0
    await _leave(chat_id)
    await _delete(st.card)
    st.card = None
    return had


# ───────────── loop · seek · shuffle · speed ─────────────
def _drop_spd(st: State) -> None:
    """Tezlik uchun vaqtinchalik fayl papkasini o'chiradi."""
    if st.spd_dir:
        shutil.rmtree(st.spd_dir, ignore_errors=True)
        st.spd_dir = ""


async def _speed_file(url: str, headers, start: float, speed: float) -> str:
    """Audioni kerakli tezlik (atempo) va pozitsiyadan boshlab vaqtinchalik mp3 faylga o'giradi."""
    folder = tempfile.mkdtemp(prefix="spd-")
    out = os.path.join(folder, "a.mp3")
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y"]
    if start >= 1:
        cmd += ["-ss", str(int(start))]
    if headers and str(url).startswith("http"):
        cmd += ["-headers", "".join(f"{k}: {v}\r\n" for k, v in dict(headers).items())]
    cmd += ["-i", url, "-vn", "-filter:a", f"atempo={speed:.2f}", "-c:a", "libmp3lame", "-q:a", "4", out]
    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
        )
        _, err = await asyncio.wait_for(proc.communicate(), timeout=240)
        if proc.returncode != 0 or not os.path.exists(out):
            raise RuntimeError(f"ffmpeg: {err.decode(errors='ignore')[-200:]}")
    except BaseException:
        if proc is not None and proc.returncode is None:
            try:
                proc.kill()
            except Exception:  # noqa: BLE001
                pass
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return out


async def _launch(chat_id: int, track: yt.Track, url: str, headers, start: float, speed: float) -> None:
    """Oqimni start soniyadan, speed tezligida (qayta) boshlaydi."""
    st = state(chat_id)
    old_dir = st.spd_dir
    if speed != 1.0 and not _is_video_stream(track):
        path = await _speed_file(url, headers, start, speed)
        try:
            await _play(chat_id, track, path, None, 0.0)
        except BaseException:
            shutil.rmtree(os.path.dirname(path), ignore_errors=True)
            raise
        st.spd_dir = os.path.dirname(path)
    else:
        await _play(chat_id, track, url, headers, start)
        st.spd_dir = ""
    if old_dir and old_dir != st.spd_dir:
        shutil.rmtree(old_dir, ignore_errors=True)


async def _restart(chat_id: int, start: float, speed: float) -> None:
    """Joriy trekni boshqa pozitsiya/tezlik bilan qaytadan boshlaydi (manba eskirgan bo'lsa qayta oladi)."""
    st = state(chat_id)
    async with st.lock:
        track = st.current
        if track is None or st.src is None:
            raise RuntimeError("nothing")
        url, headers = st.src
        st.started = time.monotonic()  # eski oqimning kechikkan 'tugadi' signalini o'tkazib yuborish uchun
        try:
            await _launch(chat_id, track, url, headers, start, speed)
        except (NoActiveGroupCall, AssistantError):
            raise
        except Exception as exc:  # noqa: BLE001
            log.info("manba eskirgan, qayta olinmoqda (chat %s): %s", chat_id, exc)
            _drop_tmp(track)
            url, headers = await _resolve_source(chat_id, track)
            st.src = (url, headers)
            await _launch(chat_id, track, url, headers, start, speed)
        st.started = time.monotonic()
        st.offset = start
        st.speed = speed
        st.paused_at = 0.0
        st.paused_total = 0.0


def set_loop(chat_id: int, value: int) -> bool:
    """value: 0 = o'chiq, -1 = cheksiz, N = yana N marta."""
    st = state(chat_id)
    if not st.current:
        return False
    st.loop = value
    return True


async def seek(chat_id: int, delta: float) -> tuple[str, float]:
    """delta > 0 oldinga, < 0 orqaga (soniya). Qaytadi: (nothing|busy|range|fail|ok, pozitsiya yoki davomiylik)."""
    st = state(chat_id)
    if not st.current or st.src is None:
        return "nothing", 0.0
    if st.lock.locked():
        return "busy", 0.0
    dur = st.current.duration or 0
    target = max(0.0, position(chat_id) + delta)
    if dur and target >= dur - 2:
        return "range", float(dur)
    try:
        await _restart(chat_id, target, st.speed)
    except Exception as exc:  # noqa: BLE001
        log.warning("seek ishlamadi (chat %s): %s", chat_id, exc)
        return "fail", 0.0
    return "ok", target


def shuffle(chat_id: int) -> int:
    """Navbatni aralashtiradi. Aralashtirilgan treklar soni (2 tadan kam bo'lsa 0)."""
    st = state(chat_id)
    if len(st.queue) < 2:
        return 0
    random.shuffle(st.queue)
    return len(st.queue)


async def set_speed(chat_id: int, speed: float) -> str:
    """nothing | video | busy | fail | ok"""
    st = state(chat_id)
    if not st.current or st.src is None:
        return "nothing"
    if speed != 1.0 and _is_video_stream(st.current):
        return "video"
    if st.lock.locked():
        return "busy"
    try:
        await _restart(chat_id, position(chat_id), speed)
    except Exception as exc:  # noqa: BLE001
        log.warning("speed ishlamadi (chat %s): %s", chat_id, exc)
        return "fail"
    return "ok"
''')

# ══════════ MODUL: song.py ══════════
_load('song', r'''"""/song — qo'shiqni mp3 qilib yuklab beradi (nom yoki havola bo'yicha). Guruhda ham, shaxsiy chatda ham ishlaydi."""
import asyncio
import html
import logging
import os
import shutil
import time

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile, Message

import assistants
import cobalt
import config
import core
import deezer
import yt

log = logging.getLogger("song")
router = Router(name="song")

MAX_MIN = 20  # shundan uzun treklar yuklanmaydi (Telegram bot yuklash limiti 50 MB)
MAX_BYTES = 49 * 1024 * 1024
_sem = asyncio.Semaphore(2)  # bir vaqtda 2 tadan ortiq yuklash serverni bo'g'masligi uchun
_cache: dict[str, str] = {}  # trek havolasi -> Telegram file_id (qayta yuklamaslik uchun)


def _remember(url: str, file_id: str) -> None:
    if len(_cache) >= 500:
        _cache.pop(next(iter(_cache)))
    _cache[url] = file_id


@router.message(Command("song", "yukla", "mp3"))
async def cmd_song(m: Message, command: CommandObject) -> None:
    query = (command.args or "").strip()
    if not query and m.reply_to_message:
        query = (m.reply_to_message.text or m.reply_to_message.caption or "").strip()
    if not query:
        await m.reply("🎵 Qo'shiq nomini yoki havolasini yozing.\nMasalan: <code>/song Konsta Lola</code>")
        return

    who = m.from_user
    status = await m.reply("⏳ Qidirilmoqda…")
    folder: str | None = None
    try:
        track = await yt.search(query, who.first_name if who else "User", who.id if who else 0)
        if track.duration and track.duration > MAX_MIN * 60:
            await status.edit_text(f"⚠️ Bu trek {MAX_MIN} daqiqadan uzun, yuklab bo'lmaydi.")
            return

        title = html.escape(track.title)
        cached = _cache.get(track.url)
        if cached:
            try:
                await m.reply_audio(cached, caption=f"🎵 {title}\n@{core.BOT_USERNAME}")
                await status.delete()
                return
            except Exception:  # noqa: BLE001
                _cache.pop(track.url, None)  # file_id eskirgan bo'lsa, qaytadan yuklaymiz

        await status.edit_text(f"⏳ Yuklanmoqda: <b>{title}</b>")
        async with _sem:
            path, info = await yt.download_audio(track)
        folder = os.path.dirname(path)

        if os.path.getsize(path) > MAX_BYTES:
            await status.edit_text("⚠️ Fayl juda katta, yuborib bo'lmaydi.")
            return

        performer = info.get("artist") or info.get("uploader") or info.get("channel") or None
        sent = await m.reply_audio(
            FSInputFile(path, filename=f"{yt.clean_title(track.title)[:60]}.mp3"),
            title=yt.clean_title(track.title)[:64],
            performer=performer,
            duration=track.duration or None,
            caption=f"🎵 {title}\n@{core.BOT_USERNAME}",
        )
        if sent.audio:
            _remember(track.url, sent.audio.file_id)
        await status.delete()
    except yt.YTError as exc:
        log.warning("song xatosi (%s): %s", exc.kind, exc.detail[:200])
        if exc.kind == "notfound":
            text = "📭 Hech narsa topilmadi. Nomini boshqacha yozib ko'ring."
        elif exc.kind == "blocked":
            text = "😕 Hozir yuklab bo'lmadi. Birozdan keyin urinib ko'ring."
        else:
            text = "⚠️ Yuklashda muammo bo'ldi. Qayta urinib ko'ring."
        try:
            await status.edit_text(text)
        except Exception:  # noqa: BLE001
            pass
    except Exception:  # noqa: BLE001
        log.exception("song kutilmagan xato")
        try:
            await status.edit_text("⚠️ Yuklashda muammo bo'ldi. Qayta urinib ko'ring.")
        except Exception:  # noqa: BLE001
            pass
    finally:
        if folder:
            shutil.rmtree(folder, ignore_errors=True)


@router.message(Command("dztest"))
async def cmd_dztest(m: Message, command: CommandObject) -> None:
    """Faqat owner: Deezer bot zaxirasi ishlayotganini tekshiradi. Masalan: /dztest Konsta Lola"""
    if not m.from_user or m.from_user.id not in config.OWNER_IDS:
        return
    if not deezer.enabled():
        await m.reply("⚠️ Deezer zaxirasi o'chirilgan (DEEZER_BOT bo'sh).")
        return
    if not assistants.items:
        await m.reply("⚠️ Yordamchi akkaunt ulanmagan.")
        return
    asst = next(iter(assistants.items.values()))
    query = (command.args or "").strip() or "Believer"
    status = await m.reply(f"⏳ @{config.DEEZER_BOT} tekshirilmoqda: <b>{html.escape(query)}</b>")
    try:
        path, meta = await deezer.fetch(asst, query)
        size = os.path.getsize(path) // 1024
        shutil.rmtree(os.path.dirname(path), ignore_errors=True)
        await status.edit_text(
            f"✅ Ishladi: <b>{html.escape(meta.get('performer') or '')} {html.escape(meta.get('title') or '')}</b>\n"
            f"Hajmi: {size} KB, davomiyligi: {meta.get('duration') or '?'} soniya"
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("dztest: %s", exc)
        await status.edit_text(f"⚠️ Ishlamadi: <code>{html.escape(str(exc)[:300])}</code>")


@router.message(Command("cobaltest"))
async def cmd_cobaltest(m: Message, command: CommandObject) -> None:
    """Faqat owner: Cobalt API YouTube'dan audio olayotganini tekshiradi. Masalan: /cobaltest Konsta Lola"""
    if not m.from_user or m.from_user.id not in config.OWNER_IDS:
        return
    if not cobalt.enabled():
        await m.reply("⚠️ Cobalt o'chirilgan (COBALT_API_URL bo'sh).")
        return
    query = (command.args or "").strip() or "Believer"
    status = await m.reply(f"⏳ Cobalt tekshirilmoqda: <b>{html.escape(query)}</b>")
    t0 = time.monotonic()
    folder: str | None = None
    try:
        ver = await cobalt.info()
        track = await yt.search(query, "Owner", m.from_user.id)
        if track.src != "youtube" or not track.url:
            raise cobalt.CobaltError("other", "YouTube qidiruvi natija bermadi (zaxira manba tanlandi)")
        path = await cobalt.fetch_audio(track.url)
        folder = os.path.dirname(path)
        size = os.path.getsize(path) // 1024
        await status.edit_text(
            f"✅ Cobalt v{ver} ishladi: <b>{html.escape(track.title)}</b>\n"
            f"Hajmi: {size} KB · {time.monotonic() - t0:.1f} s"
        )
    except cobalt.CobaltError as exc:
        log.warning("cobaltest: %s", exc)
        await status.edit_text(f"⚠️ Cobalt xatosi [{exc.kind}]: <code>{html.escape(exc.detail[:300])}</code>")
    except Exception as exc:  # noqa: BLE001
        log.warning("cobaltest: %s", exc)
        await status.edit_text(f"⚠️ Ishlamadi: <code>{html.escape(str(exc)[:300])}</code>")
    finally:
        if folder:
            shutil.rmtree(folder, ignore_errors=True)
''')

# ══════════ MODUL: menu.py ══════════
_load('menu', r'''"""Telegram buyruqlar menyusi: hamma uchun umumiy ro'yxat + faqat egalarga ko'rinadigan admin buyruqlar.

Hamma ko'radigan menyu Fallen Music bilan bir xil tartibda (birinchi 10 ta buyruq), keyin qo'shimchalar.
Owner buyruqlari BotCommandScopeChat orqali faqat OWNER_ID dagi akkauntlarning shaxsiy chatida ko'rinadi.
"""
import logging

from aiogram.types import (
    BotCommand,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    BotCommandScopeDefault,
)

import config
import core
import db

log = logging.getLogger("menu")

PUBLIC_COMMANDS = [
    ("start", "Starts the bot"),
    ("ping", "Check that bot is alive or dead"),
    ("play", "Starts playing the requested song"),
    ("vplay", "Starts playing the requested song as video"),
    ("skip", "Moves to the next track"),
    ("pause", "Pause the current playing song"),
    ("resume", "Resume the paused song"),
    ("end", "Clear the queue and leave voice chat"),
    ("loop", "Loops the current playing song on voicechat"),
    ("seek", "Seek the stream to given duration (in seconds)"),
    ("seekback", "Seek the stream backward (in seconds)"),
    ("shuffle", "Shuffle the queued songs"),
    ("speed", "Change the playback speed (0.5x - 2x)"),
    ("queue", "Show the current queue"),
    ("song", "Download a song as mp3"),
    ("settings", "Open the group settings (language, mode)"),
    ("auth", "Allow a user to control the player"),
    ("unauth", "Remove a user's control permission"),
    ("authusers", "Show the authorized users"),
    ("verify", "Turn join request verification on or off"),
    ("help", "Show all commands"),
]

# Faqat egalar ko'radi (handlerlari ham faqat OWNER_ID uchun ishlaydi)
OWNER_COMMANDS = [
    ("panel", "Open the owner panel"),
    ("stats", "Bot statistics"),
    ("reboot", "Restart the bot"),
    ("ban", "Ban a user from the bot (ID)"),
    ("unban", "Unban a user (ID)"),
    ("cobaltest", "Test the Cobalt API"),
    ("dztest", "Test the Deezer fallback"),
]


def public_list() -> list[BotCommand]:
    return [BotCommand(command=c, description=d) for c, d in PUBLIC_COMMANDS]


def owner_list() -> list[BotCommand]:
    return [BotCommand(command=c, description=d) for c, d in OWNER_COMMANDS] + public_list()


async def set_owner(uid: int) -> bool:
    """Eganing shaxsiy chatiga to'liq menyuni qo'yadi (ega botni /start qilmagan bo'lsa Telegram rad etadi)."""
    try:
        await core.bot.set_my_commands(owner_list(), scope=BotCommandScopeChat(chat_id=uid))
        return True
    except Exception as exc:  # noqa: BLE001
        log.info("owner %s menyusi o'rnatilmadi (hali /start qilmagan bo'lishi mumkin): %s", uid, exc)
        return False


async def setup() -> None:
    bot = core.bot
    try:
        # BotFather yoki eski versiyadan qolgan toifali ro'yxatlar umumiy ro'yxatni bosib qolmasligi uchun tozalaymiz
        for scope in (
            BotCommandScopeAllPrivateChats(),
            BotCommandScopeAllGroupChats(),
            BotCommandScopeAllChatAdministrators(),
        ):
            await bot.delete_my_commands(scope=scope)
        await bot.set_my_commands(public_list(), scope=BotCommandScopeDefault())

        # OWNER_ID dan olib tashlangan akkauntlardagi admin menyusini o'chiramiz
        old = await db.get_setting("menu_owners") or ""
        old_ids = {int(x) for x in old.split(",") if x.strip().lstrip("-").isdigit()}
        for uid in old_ids - set(config.OWNER_IDS):
            try:
                await bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=uid))
            except Exception:  # noqa: BLE001
                pass
        for uid in config.OWNER_IDS:
            await set_owner(uid)
        await db.set_setting("menu_owners", ",".join(str(i) for i in sorted(config.OWNER_IDS)))
        log.info("buyruqlar menyusi o'rnatildi: %d ommaviy, %d owner", len(PUBLIC_COMMANDS), len(OWNER_COMMANDS))
    except Exception:  # noqa: BLE001
        log.exception("buyruqlar menyusini o'rnatib bo'lmadi")
''')

# ══════════ MODUL: handlers_user.py ══════════
_load('handlers_user', r'''import asyncio
import html
import logging
import shutil
import time

from aiogram import F, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import ChatMemberUpdatedFilter, Command, CommandObject, CommandStart, JOIN_TRANSITION
from aiogram.types import CallbackQuery, ChatJoinRequest, ChatMemberUpdated
from aiogram.types import InlineKeyboardMarkup as Markup
from aiogram.types import Message, User

import assistants
import config
import core
import db
import media
import menu
import player
import yt
from premium import B
from strings import LANGS, t

log = logging.getLogger("handlers_user")
router = Router()

GROUPS = {ChatType.GROUP, ChatType.SUPERGROUP}
IN_GROUP = F.chat.type.in_(GROUPS)
IN_PRIVATE = F.chat.type == ChatType.PRIVATE
ANON_ID = 1087968824  # "GroupAnonymousBot" — anonim adminlar xabari shu nomdan keladi


# ───────────────────────── yordamchi funksiyalar ─────────────────────────
def mention(user: User | None) -> str:
    return user.mention_html() if user else "Admin"


async def is_admin(chat_id: int, user_id: int) -> bool:
    if user_id in config.OWNER_IDS or user_id == ANON_ID:
        return True
    try:
        m = await core.bot.get_chat_member(chat_id, user_id)
        return m.status in (ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR)
    except Exception:  # noqa: BLE001
        return False


async def can_control(chat_id: int, user_id: int) -> bool:
    _lang, mode = await db.get_chat(chat_id)
    if mode == "user" or user_id in config.OWNER_IDS:
        return True
    return await is_admin(chat_id, user_id) or await db.is_auth(chat_id, user_id)


async def lang_of(chat_id: int) -> str:
    return (await db.get_chat(chat_id))[0]


async def lang_for(chat) -> str:
    return "uz" if chat.type == ChatType.PRIVATE else await lang_of(chat.id)


async def safe_edit(msg: Message, text: str, markup=None) -> None:
    try:
        await msg.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as exc:
        if "not modified" not in str(exc).lower():
            raise


def start_markup(lang: str) -> Markup:
    rows = [
        [B(t(lang, "b_add"), url=f"https://t.me/{core.BOT_USERNAME}?startgroup=true&admin=manage_video_chats+delete_messages+invite_users", style="primary")],
        [B(t(lang, "b_settings"), cb="help", style="primary")],
    ]
    extra = []
    if config.UPDATES_URL:
        extra.append(B(t(lang, "b_updates"), url=config.UPDATES_URL, style="primary"))
    if config.SUPPORT_URL:
        extra.append(B(t(lang, "b_support"), url=config.SUPPORT_URL, style="primary"))
    if extra:
        rows.append(extra)
    return Markup(inline_keyboard=rows)


def settings_markup(lang: str, mode: str) -> Markup:
    user_label = t(lang, "b_user") + (" ✅" if mode == "user" else "")
    admin_label = t(lang, "b_admin") + (" ✅" if mode == "admin" else "")
    return Markup(
        inline_keyboard=[
            [B(t(lang, "b_lang"), cb="set:lang", style="primary")],
            [
                B(user_label, cb="mode:user", style="success" if mode == "user" else "primary"),
                B(admin_label, cb="mode:admin", style="success" if mode == "admin" else "primary"),
            ],
            [B(t(lang, "b_auth"), cb="set:auth", style="primary")],
            [B(t(lang, "b_close"), cb="close", style="danger")],
        ]
    )


def settings_text(chat, lang: str, mode: str) -> str:
    return t(
        lang, "settings",
        title=html.escape(chat.title or ""), lang=LANGS.get(lang, lang),
        mode="Admin Mode" if mode == "admin" else "User Mode",
    )


# ───────────────────────────── /start, /help ─────────────────────────────
@router.message(CommandStart(), IN_PRIVATE)
async def start_private(m: Message):
    await db.add_user(m.from_user.id)
    if m.from_user.id in config.OWNER_IDS:
        await menu.set_owner(m.from_user.id)  # admin buyruqlar faqat egaga ko'rinadi
    lang = "uz"
    text = t(lang, "start", name=html.escape(m.from_user.first_name or ""), bot=html.escape(core.BOT_NAME))
    await media.send_with_media(core.bot, m.chat.id, "start", text, start_markup(lang))


@router.message(CommandStart(), IN_GROUP)
async def start_group(m: Message):
    await db.ensure_chat(m.chat.id)
    await m.reply(t(await lang_of(m.chat.id), "help"))


@router.message(Command("help"))
async def help_cmd(m: Message):
    await m.reply(t(await lang_for(m.chat), "help"))


@router.callback_query(F.data == "help")
async def help_cb(q: CallbackQuery):
    await q.message.answer(t(await lang_for(q.message.chat), "help"))
    await q.answer()


# ───────────────────────── guruhga qo'shilganda ─────────────────────────
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION), F.chat.type.in_(GROUPS))
async def on_added(ev: ChatMemberUpdated):
    chat = ev.chat
    is_new = await db.ensure_chat(chat.id)
    lang = await lang_of(chat.id)
    rows = [[B(t(lang, "b_lang"), cb="set:lang", style="primary")]]
    if config.UPDATES_URL:
        rows[0].append(B(t(lang, "b_updates"), url=config.UPDATES_URL, style="primary"))
    text = t(
        lang, "welcome",
        bot=html.escape(core.BOT_NAME), by=mention(ev.from_user),
        title=html.escape(chat.title or ""), cid=chat.id,
    )
    try:
        await media.send_with_media(core.bot, chat.id, "welcome", text, Markup(inline_keyboard=rows))
    except Exception:  # noqa: BLE001
        pass
    if is_new:
        await player.log_owner(f"➕ Yangi guruh: <b>{html.escape(chat.title or '')}</b> (<code>{chat.id}</code>)")


# ─────────────────────────────── ijro ───────────────────────────────
@router.message(Command("play", "vplay", "p"), IN_GROUP)
async def play_cmd(m: Message, command: CommandObject):
    if not m.from_user or m.from_user.id == ANON_ID:
        return
    chat_id = m.chat.id
    uid = m.from_user.id
    video = command.command.lower() == "vplay"
    await db.ensure_chat(chat_id)
    await db.add_user(uid)
    lang = await lang_of(chat_id)

    if await db.is_banned(uid):
        return await m.reply(t(lang, "banned_user"))
    if not await can_control(chat_id, uid):
        return await m.reply(t(lang, "admin_only"))

    query = (command.args or "").strip()
    if not query and m.reply_to_message:
        query = (m.reply_to_message.text or m.reply_to_message.caption or "").strip()
    if not query:
        return await m.reply(t(lang, "usage", cmd=command.command.lower()))

    if len(player.state(chat_id).queue) >= config.QUEUE_LIMIT:
        return await m.reply(t(lang, "queue_full", limit=config.QUEUE_LIMIT))

    status = await m.reply(t(lang, "searching"))

    try:
        track = await yt.search(query, m.from_user.first_name or "User", uid, video)
    except yt.YTError as exc:
        if exc.kind == "blocked":
            await player.log_owner(
                "⚠️ YouTube bloklayapti. Owner panel → 🍪 Cookies orqali yangi cookies.txt yuklang.\n"
                f"<code>{html.escape(exc.detail[:300])}</code>"
            )
        key = {"notfound": "notfound", "blocked": "yt_blocked"}.get(exc.kind, "error")
        return await status.edit_text(t(lang, key))

    if track.duration and track.duration > config.DURATION_LIMIT_MIN * 60:
        return await status.edit_text(t(lang, "too_long", limit=config.DURATION_LIMIT_MIN))

    try:
        await player.ensure_assistant(chat_id)
    except player.AssistantError as exc:
        if exc.kind == "none":
            await player.log_owner("⚠️ Yordamchi akkaunt yo'q. Owner panel → 👤 Yordamchilar orqali qo'shing.")
        return await status.edit_text(t(lang, "no_asst") if exc.kind == "none" else player.hint(exc))

    pos = await player.add(chat_id, track, status)
    if pos > 0:
        track.status = None  # navbat xabari chatda qoladi
        await safe_edit(
            status,
            t(lang, "queued", pos=pos, title=html.escape(track.title), by=mention(m.from_user)),
            Markup(inline_keyboard=[[
                B(t(lang, "b_add"), url=f"https://t.me/{core.BOT_USERNAME}?startgroup=true", style="success"),
                B(t(lang, "b_close"), cb="close", style="danger"),
            ]]),
        )
    else:
        try:
            await status.edit_text(t(lang, "downloading", title=html.escape(track.title)))
        except Exception:  # noqa: BLE001  (ijro tez boshlansa xabar allaqachon o'chirilgan bo'lishi mumkin)
            pass

    try:
        await m.delete()
    except Exception:  # noqa: BLE001
        pass


async def _control(chat_id: int, user: User | None, action: str) -> str:
    lang = await lang_of(chat_id)
    ok = False
    if action == "pause":
        ok = await player.pause(chat_id)
    elif action == "resume":
        ok = await player.resume(chat_id)
    elif action == "skip":
        ok = await player.skip(chat_id)
    elif action == "end":
        ok = await player.end(chat_id)
    if not ok:
        return t(lang, "nothing")
    key = {"pause": "paused", "resume": "resumed", "skip": "skipped", "end": "ended"}[action]
    return t(lang, key, by=mention(user))


def _make_cmd(name: str) -> None:
    @router.message(Command(name), IN_GROUP)
    async def _h(m: Message):
        chat_id = m.chat.id
        uid = m.from_user.id if m.from_user else 0
        if not await can_control(chat_id, uid):
            return await m.reply(t(await lang_of(chat_id), "admin_only"))
        text = await _control(chat_id, m.from_user if uid != ANON_ID else None, name)
        await player.notice(chat_id, text)
        try:
            await m.delete()
        except Exception:  # noqa: BLE001
            pass

    _h.__name__ = f"cmd_{name}"


for _name in ("pause", "resume", "skip", "end"):
    _make_cmd(_name)


@router.callback_query(F.data.in_({"ctl:pause", "ctl:resume", "ctl:skip"}))
async def ctl_cb(q: CallbackQuery):
    chat_id = q.message.chat.id
    if not await can_control(chat_id, q.from_user.id):
        return await q.answer(t(await lang_of(chat_id), "admin_only"), show_alert=True)
    text = await _control(chat_id, q.from_user, q.data.split(":")[1])
    await q.answer()
    await player.notice(chat_id, text)


@router.callback_query(F.data == "close")
async def close_cb(q: CallbackQuery):
    chat = q.message.chat
    if chat.type != ChatType.PRIVATE and not await can_control(chat.id, q.from_user.id):
        return await q.answer(t(await lang_of(chat.id), "admin_only"), show_alert=True)
    try:
        await q.message.delete()
    except Exception:  # noqa: BLE001
        await q.answer()


# ───────────── loop · seek · shuffle · speed · verify ─────────────
async def _gate(m: Message) -> tuple[int, str] | None:
    """Ijro buyruqlari uchun umumiy tekshiruv. Ruxsat bo'lmasa javob berib None qaytaradi."""
    chat_id = m.chat.id
    uid = m.from_user.id if m.from_user else 0
    await db.ensure_chat(chat_id)
    lang = await lang_of(chat_id)
    if uid and uid != ANON_ID and await db.is_banned(uid):
        await m.reply(t(lang, "banned_user"))
        return None
    if not await can_control(chat_id, uid):
        await m.reply(t(lang, "admin_only"))
        return None
    return chat_id, lang


async def _done(m: Message, text: str) -> None:
    """Qisqa xabar yuboradi (10 soniyadan keyin o'chadi) va buyruq xabarini o'chiradi."""
    await player.notice(m.chat.id, text)
    try:
        await m.delete()
    except Exception:  # noqa: BLE001
        pass


def _by(m: Message) -> str:
    return mention(m.from_user if m.from_user and m.from_user.id != ANON_ID else None)


def parse_loop(arg: str, current: int) -> int | None:
    """'' → almashtirish, on/off, 1-10. Noto'g'ri bo'lsa None."""
    a = (arg or "").strip().lower()
    if a in ("", "toggle"):
        return 0 if current else -1
    if a in ("on", "enable", "enabled", "yes"):
        return -1
    if a in ("off", "disable", "disabled", "no", "0"):
        return 0
    if a.isdigit() and 1 <= int(a) <= 10:
        return int(a)
    return None


def parse_secs(arg: str) -> int | None:
    """'30', '90s', '1:30', '1:02:03' → soniya. Noto'g'ri yoki 0 bo'lsa None."""
    a = (arg or "").strip().lower().rstrip("s")
    if not a:
        return None
    try:
        if ":" in a:
            parts = [int(x) for x in a.split(":")]
            if len(parts) > 3 or any(p < 0 for p in parts):
                return None
            total = 0
            for p in parts:
                total = total * 60 + p
        else:
            total = int(a)
    except ValueError:
        return None
    return total if 0 < total <= 36000 else None


def parse_speed(arg: str) -> float | None:
    a = (arg or "").strip().lower().replace(",", ".").rstrip("x")
    if a in ("reset", "normal"):
        return 1.0
    try:
        v = float(a)
    except ValueError:
        return None
    return round(v, 2) if 0.5 <= v <= 2.0 else None


@router.message(Command("loop"), IN_GROUP)
async def loop_cmd(m: Message, command: CommandObject):
    g = await _gate(m)
    if not g:
        return
    chat_id, lang = g
    st = player.state(chat_id)
    if not st.current:
        return await _done(m, t(lang, "nothing"))
    value = parse_loop(command.args or "", st.loop)
    if value is None:
        return await _done(m, t(lang, "loop_usage"))
    player.set_loop(chat_id, value)
    if value == 0:
        text = t(lang, "loop_off", by=_by(m))
    elif value < 0:
        text = t(lang, "loop_on", by=_by(m))
    else:
        text = t(lang, "loop_n", n=value, by=_by(m))
    await _done(m, text)


async def _seek(m: Message, command: CommandObject, sign: int) -> None:
    g = await _gate(m)
    if not g:
        return
    chat_id, lang = g
    secs = parse_secs(command.args or "")
    if secs is None:
        return await _done(m, t(lang, "seek_usage", cmd=command.command.lower()))
    status, val = await player.seek(chat_id, sign * secs)
    if status == "ok":
        text = t(lang, "seeked", pos=yt.fmt_duration(int(val)), by=_by(m))
    elif status == "range":
        text = t(lang, "seek_range", dur=yt.fmt_duration(int(val)))
    elif status == "busy":
        text = t(lang, "busy")
    elif status == "nothing":
        text = t(lang, "nothing")
    else:
        text = t(lang, "error")
    await _done(m, text)


@router.message(Command("seek"), IN_GROUP)
async def seek_cmd(m: Message, command: CommandObject):
    await _seek(m, command, 1)


@router.message(Command("seekback"), IN_GROUP)
async def seekback_cmd(m: Message, command: CommandObject):
    await _seek(m, command, -1)


@router.message(Command("shuffle"), IN_GROUP)
async def shuffle_cmd(m: Message):
    g = await _gate(m)
    if not g:
        return
    chat_id, lang = g
    n = player.shuffle(chat_id)
    await _done(m, t(lang, "shuffled", n=n, by=_by(m)) if n else t(lang, "shuffle_few"))


@router.message(Command("speed"), IN_GROUP)
async def speed_cmd(m: Message, command: CommandObject):
    g = await _gate(m)
    if not g:
        return
    chat_id, lang = g
    st = player.state(chat_id)
    if not st.current:
        return await _done(m, t(lang, "nothing"))
    speed = parse_speed(command.args or "")
    if speed is None:
        return await _done(m, t(lang, "speed_usage", cur=f"{st.speed:g}"))
    res = await player.set_speed(chat_id, speed)
    text = {
        "ok": t(lang, "speed_set", speed=f"{speed:g}", by=_by(m)),
        "video": t(lang, "speed_video"),
        "busy": t(lang, "busy"),
        "nothing": t(lang, "nothing"),
    }.get(res, t(lang, "error"))
    await _done(m, text)


def _verify_key(chat_id: int) -> str:
    return f"verify:{chat_id}"


@router.message(Command("verify"), IN_GROUP)
async def verify_cmd(m: Message, command: CommandObject):
    chat_id = m.chat.id
    await db.ensure_chat(chat_id)
    lang = await lang_of(chat_id)
    if not await is_admin(chat_id, m.from_user.id if m.from_user else 0):
        return await m.reply(t(lang, "admin_only"))
    arg = (command.args or "").strip().lower()
    if arg in ("on", "enable", "1"):
        await db.set_setting(_verify_key(chat_id), "1")
        return await m.reply(t(lang, "verify_on"))
    if arg in ("off", "disable", "0"):
        await db.set_setting(_verify_key(chat_id), "0")
        return await m.reply(t(lang, "verify_off"))
    on = await db.get_setting(_verify_key(chat_id)) == "1"
    await m.reply(t(lang, "verify_status", state="ON" if on else "OFF"))


@router.callback_query(F.data.startswith("verify:"))
async def verify_cb(q: CallbackQuery):
    try:
        chat_id = int(q.data.split(":", 1)[1])
    except ValueError:
        return await q.answer()
    lang = await lang_of(chat_id)
    if await db.get_setting(_verify_key(chat_id)) != "1":
        return await q.answer(t(lang, "verify_fail"), show_alert=True)
    try:
        await core.bot.approve_chat_join_request(chat_id, q.from_user.id)
    except TelegramBadRequest as exc:
        log.info("verify: %s (chat %s, user %s)", exc, chat_id, q.from_user.id)
        return await q.answer(t(lang, "verify_fail"), show_alert=True)
    await q.answer(t(lang, "verify_ok"))
    try:
        await q.message.edit_text(t(lang, "verify_ok"))
    except Exception:  # noqa: BLE001
        pass


@router.message(Command("queue"), IN_GROUP)
async def queue_cmd(m: Message):
    chat_id = m.chat.id
    lang = await lang_of(chat_id)
    st = player.state(chat_id)
    if not st.current and not st.queue:
        return await m.reply(t(lang, "queue_empty"))
    lines = [t(lang, "queue_title")]
    if st.current:
        lines.append(t(lang, "queue_now", title=html.escape(st.current.title)))
    for i, tr in enumerate(st.queue[:15], 1):
        lines.append(f"{i}. {html.escape(tr.title)} · {yt.fmt_duration(tr.duration)}")
    if len(st.queue) > 15:
        lines.append(f"… +{len(st.queue) - 15}")
    await m.reply("\n".join(lines))


def readable_time(sec: float) -> str:
    """6days, 13h:40m:28s ko'rinishida (Fallen Music kabi)."""
    days, rem = divmod(max(0, int(sec)), 86400)
    h, rem = divmod(rem, 3600)
    mnt, s = divmod(rem, 60)
    return (f"{days}days, " if days else "") + f"{h}h:{mnt}m:{s}s"


def _sys_stats_sync() -> tuple[float, float, float]:
    """(CPU %, RAM %, Disk %). psutil bo'lsa u ishlatiladi, bo'lmasa Linux /proc orqali."""
    try:
        import psutil

        return psutil.cpu_percent(interval=0.3), psutil.virtual_memory().percent, psutil.disk_usage("/").percent
    except Exception:  # noqa: BLE001
        pass
    cpu = ram = disk = 0.0
    try:
        def _cpu() -> tuple[int, int]:
            with open("/proc/stat") as f:
                p = [int(x) for x in f.readline().split()[1:]]
            return sum(p), p[3] + (p[4] if len(p) > 4 else 0)

        t1, i1 = _cpu()
        time.sleep(0.3)
        t2, i2 = _cpu()
        cpu = 100.0 * (1 - (i2 - i1) / max(1, t2 - t1))
    except Exception:  # noqa: BLE001
        pass
    try:
        info: dict[str, int] = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, _, v = line.partition(":")
                info[k] = int(v.split()[0])
        ram = 100.0 * (1 - info["MemAvailable"] / info["MemTotal"])
    except Exception:  # noqa: BLE001
        pass
    try:
        du = shutil.disk_usage("/")
        disk = 100.0 * du.used / du.total
    except Exception:  # noqa: BLE001
        pass
    return cpu, ram, disk


def _pytg_latency() -> float:
    vals: list[float] = []
    for a in assistants.items.values():
        try:
            vals.append(float(a.call.ping))
        except Exception:  # noqa: BLE001
            pass
    return sum(vals) / len(vals) if vals else 0.0


def ping_text(latency: float, cpu: float, ram: float, disk: float, pytg: float) -> str:
    return (
        "<u>Pong!</u>\n\n"
        f"<b>Latency:</b> <code>{latency:.2f}ms</code>\n\n"
        f"<b>Uptime:</b> {readable_time(time.time() - core.STARTED)}\n"
        f"<b>CPU:</b> <code>{cpu:.1f}%</code>\n"
        f"<b>RAM:</b> <code>{ram:.1f}%</code>\n"
        f"<b>Disk:</b> <code>{disk:.1f}%</code>\n"
        f"<b>PyTgCalls Latency:</b> <code>{pytg:.1f}ms</code>"
    )


@router.message(Command("ping"))
async def ping_cmd(m: Message):
    t0 = time.perf_counter()
    try:
        await core.bot.get_me()  # Bot API'ga haqiqiy so'rov-javob vaqti
    except Exception:  # noqa: BLE001
        pass
    latency = (time.perf_counter() - t0) * 1000
    cpu, ram, disk = await asyncio.to_thread(_sys_stats_sync)
    text = ping_text(latency, cpu, ram, disk, _pytg_latency())
    kb = None
    if config.SUPPORT_URL:
        kb = Markup(inline_keyboard=[[B("Support", url=config.SUPPORT_URL, style="primary")]])
    await media.reply_with_media(m, "ping", text, kb)


# ───────────────────────────── sozlamalar ─────────────────────────────
@router.message(Command("settings", "lang"), IN_GROUP)
async def settings_cmd(m: Message):
    chat_id = m.chat.id
    lang, mode = await db.get_chat(chat_id)
    uid = m.from_user.id if m.from_user else 0
    if not await is_admin(chat_id, uid):
        return await m.reply(t(lang, "admin_only"))
    await m.reply(settings_text(m.chat, lang, mode), reply_markup=settings_markup(lang, mode))


async def _admin_gate(q: CallbackQuery, lang: str) -> bool:
    if await is_admin(q.message.chat.id, q.from_user.id):
        return True
    await q.answer(t(lang, "admin_only"), show_alert=True)
    return False


async def _render_settings(q: CallbackQuery) -> None:
    lang, mode = await db.get_chat(q.message.chat.id)
    await safe_edit(q.message, settings_text(q.message.chat, lang, mode), settings_markup(lang, mode))


@router.callback_query(F.data.in_({"set:lang", "set:auth", "set:back"}))
async def settings_cb(q: CallbackQuery):
    chat_id = q.message.chat.id
    lang, _mode = await db.get_chat(chat_id)
    if not await _admin_gate(q, lang):
        return
    action = q.data.split(":")[1]
    back = [B(t(lang, "b_back"), cb="set:back", style="primary")]
    if action == "back":
        await _render_settings(q)
    elif action == "lang":
        rows = [
            [B(label + (" ✅" if code == lang else ""), cb=f"setlang:{code}", style="success" if code == lang else "primary")]
            for code, label in LANGS.items()
        ]
        rows.append(back)
        await safe_edit(q.message, t(lang, "lang_pick"), Markup(inline_keyboard=rows))
    else:
        users = await db.list_auth(chat_id)
        body = "\n".join(f"• {html.escape(n)} (<code>{uid}</code>)" for uid, n in users) if users else t(lang, "auth_none")
        await safe_edit(q.message, f"{t(lang, 'auth_title')}\n\n{body}", Markup(inline_keyboard=[back]))
    await q.answer()


@router.callback_query(F.data.startswith("setlang:"))
async def setlang_cb(q: CallbackQuery):
    chat_id = q.message.chat.id
    old, _mode = await db.get_chat(chat_id)
    if not await _admin_gate(q, old):
        return
    code = q.data.split(":")[1]
    if code not in LANGS:
        return await q.answer()
    await db.set_lang(chat_id, code)
    await q.answer(t(code, "lang_done", lang=LANGS[code]))
    await _render_settings(q)


@router.callback_query(F.data.in_({"mode:user", "mode:admin"}))
async def mode_cb(q: CallbackQuery):
    chat_id = q.message.chat.id
    lang, current = await db.get_chat(chat_id)
    if not await _admin_gate(q, lang):
        return
    mode = q.data.split(":")[1]
    if mode != current:
        await db.set_mode(chat_id, mode)
        await _render_settings(q)
    await q.answer(t(lang, "mode_done", mode="Admin Mode" if mode == "admin" else "User Mode"))


# ───────────────────────── ruxsat berilganlar ─────────────────────────
async def _target_user(m: Message, command: CommandObject) -> tuple[int, str] | None:
    if m.reply_to_message and m.reply_to_message.from_user:
        u = m.reply_to_message.from_user
        return u.id, u.first_name or str(u.id)
    arg = (command.args or "").split(" ")[0].strip()
    if not arg:
        return None
    if arg.lstrip("-").isdigit():
        return int(arg), arg
    try:
        chat = await core.bot.get_chat(arg if arg.startswith("@") else f"@{arg}")
        return chat.id, chat.first_name or chat.title or arg
    except Exception:  # noqa: BLE001
        return None


@router.message(Command("auth", "unauth"), IN_GROUP)
async def auth_cmd(m: Message, command: CommandObject):
    chat_id = m.chat.id
    lang = await lang_of(chat_id)
    if not await is_admin(chat_id, m.from_user.id if m.from_user else 0):
        return await m.reply(t(lang, "admin_only"))
    target = await _target_user(m, command)
    if not target:
        return await m.reply(t(lang, "auth_usage"))
    uid, name = target
    who = f'<a href="tg://user?id={uid}">{html.escape(name)}</a>'
    if command.command.lower() == "auth":
        await db.add_auth(chat_id, uid, name)
        await m.reply(t(lang, "auth_added", who=who))
    else:
        await db.del_auth(chat_id, uid)
        await m.reply(t(lang, "auth_removed", who=who))


@router.message(Command("authusers"), IN_GROUP)
async def authusers_cmd(m: Message):
    chat_id = m.chat.id
    lang = await lang_of(chat_id)
    users = await db.list_auth(chat_id)
    if not users:
        return await m.reply(t(lang, "auth_none"))
    body = "\n".join(f"• {html.escape(n)} (<code>{uid}</code>)" for uid, n in users)
    await m.reply(f"{t(lang, 'auth_title')}\n\n{body}")


@router.message(Command("play", "vplay", "p", "pause", "resume", "skip", "end", "queue", "settings", "lang", "auth", "unauth", "authusers", "loop", "seek", "seekback", "shuffle", "speed", "verify"), IN_PRIVATE)
async def private_notice(m: Message):
    await m.reply(t("uz", "private_only_group"))


# ───────────────── yordamchi akkaunt: guruhga avtomatik qo'shilish ─────────────────
@router.chat_join_request()
async def on_join_request(req: ChatJoinRequest):
    """Yordamchi akkaunt a'zolik so'rovi yuborsa (guruhda «so'rov bilan qo'shilish» yoqilgan), bot o'zi tasdiqlaydi."""
    if req.from_user.id not in assistants.items:
        # oddiy foydalanuvchi: guruhda /verify yoqilgan bo'lsa, DM'da tasdiqlash tugmasi yuboriladi
        if await db.get_setting(_verify_key(req.chat.id)) != "1":
            return
        lang = await lang_of(req.chat.id)
        kb = Markup(inline_keyboard=[[B(t(lang, "b_verify"), cb=f"verify:{req.chat.id}", style="success")]])
        try:
            await core.bot.send_message(
                req.user_chat_id, t(lang, "verify_msg", title=html.escape(req.chat.title or "")), reply_markup=kb
            )
        except Exception as exc:  # noqa: BLE001
            log.info("verify xabari yuborilmadi (%s → %s): %s", req.chat.id, req.from_user.id, exc)
        return
    try:
        await req.approve()
    except Exception as exc:  # noqa: BLE001
        log.info("yordamchi so'rovi tasdiqlanmadi (%s): %s", req.chat.id, exc)


@router.message(IN_GROUP, F.new_chat_members | F.left_chat_member)
async def hide_assistant_service(m: Message):
    """Yordamchi qo'shilgani/chiqqani haqidagi xizmat xabarini o'chiradi: guruh a'zolari buni sezmaydi."""
    ids = {u.id for u in (m.new_chat_members or [])}
    if m.left_chat_member:
        ids.add(m.left_chat_member.id)
    if ids & set(assistants.items):
        try:
            await m.delete()
        except Exception:  # noqa: BLE001
            pass
''')

# ══════════ MODUL: handlers_owner.py ══════════
_load('handlers_owner', r'''"""Owner panel (faqat OWNER_ID ro'yxatidagi foydalanuvchilar, faqat shaxsiy chatda)."""
import asyncio
import html
import io
import os
import re
import sys

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as Markup
from aiogram.types import Message
from pyrogram.errors import (
    FloodWait,
    PasswordHashInvalid,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    PhoneNumberInvalid,
)

import assistants
import config
import core
import crypto
import db
import premium
import media
import menu
import player
from premium import B

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE, F.from_user.id.in_(config.OWNER_IDS))
router.callback_query.filter(F.from_user.id.in_(config.OWNER_IDS))


class Own(StatesGroup):
    phone = State()
    code = State()
    password = State()
    session = State()
    api = State()
    media = State()
    emoji = State()
    cookies = State()
    bc_content = State()
    bc_buttons = State()


BACK = B("⬅️ Orqaga", cb="own:main", style="primary")
CANCEL = Markup(inline_keyboard=[[B("✖️ Bekor qilish", cb="own:cancel", style="danger")]])


async def safe_edit(msg: Message, text: str, markup=None) -> None:
    try:
        await msg.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as exc:
        if "not modified" not in str(exc).lower():
            raise


async def _del(m: Message) -> None:
    try:
        await m.delete()
    except Exception:  # noqa: BLE001
        pass


# ───────────────────────────── bosh menyu ─────────────────────────────
async def main_text() -> str:
    chats, users, plays = await db.counts()
    return (
        "👑 <b>Owner panel</b>\n\n"
        f"👤 Faol yordamchilar: <b>{len(assistants.items)}</b>\n"
        f"💬 Guruhlar: <b>{chats}</b> · 👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"🎧 Faol ovozli chatlar: <b>{player.active_count()}</b> · 🎵 Jami ijro: <b>{plays}</b>"
    )


def main_markup() -> Markup:
    return Markup(
        inline_keyboard=[
            [B("👤 Yordamchilar", cb="own:asst", style="primary"), B("📣 Reklama", cb="own:bc", style="primary")],
            [B("🖼 Media", cb="own:media", style="primary"), B("💎 Premium emoji", cb="own:emoji", style="primary")],
            [B("🍪 Cookies", cb="own:cookies", style="primary"), B("📊 Statistika", cb="own:stats", style="primary")],
            [B("🔑 API ID/HASH", cb="own:api", style="primary"), B("♻️ Restart", cb="own:restart", style="danger")],
        ]
    )


@router.message(Command("panel", "owner"))
async def panel_cmd(m: Message, state: FSMContext):
    await state.clear()
    await menu.set_owner(m.from_user.id)  # admin buyruqlar menyusini (faqat ega uchun) yangilaymiz
    await m.answer(await main_text(), reply_markup=main_markup())


@router.callback_query(F.data == "own:main")
async def main_cb(q: CallbackQuery, state: FSMContext):
    await state.clear()
    await assistants.login_cancel(q.from_user.id)
    await safe_edit(q.message, await main_text(), main_markup())
    await q.answer()


@router.callback_query(F.data == "own:cancel")
async def cancel_cb(q: CallbackQuery, state: FSMContext):
    await state.clear()
    await assistants.login_cancel(q.from_user.id)
    await safe_edit(q.message, await main_text(), main_markup())
    await q.answer("Bekor qilindi")


@router.message(Command("stats"))
async def stats_cmd(m: Message):
    await m.answer(await main_text(), reply_markup=main_markup())


@router.callback_query(F.data == "own:stats")
async def stats_cb(q: CallbackQuery):
    await safe_edit(q.message, await main_text(), main_markup())
    await q.answer("Yangilandi")


async def _restart() -> None:
    await asyncio.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)


@router.message(Command("reboot"))
async def reboot_cmd(m: Message):
    await m.answer("♻️ Restart...")
    asyncio.create_task(_restart())


@router.callback_query(F.data == "own:restart")
async def restart_cb(q: CallbackQuery):
    await q.answer()
    await q.message.answer("♻️ Restart...")
    asyncio.create_task(_restart())


@router.message(Command("ban", "unban"))
async def ban_cmd(m: Message, command: CommandObject):
    arg = (command.args or "").strip()
    if not arg.lstrip("-").isdigit():
        return await m.answer("ℹ️ Foydalanish: <code>/ban 123456789</code> yoki <code>/unban 123456789</code>")
    uid = int(arg)
    if command.command.lower() == "ban":
        await db.ban(uid)
        await m.answer(f"🚫 <code>{uid}</code> bloklandi.")
    else:
        await db.unban(uid)
        await m.answer(f"✅ <code>{uid}</code> blokdan chiqarildi.")


# ───────────────────────────── Telegram API ID / HASH ─────────────────────────────
def _parse_api(text: str) -> tuple[int, str] | None:
    """Xabardan API ID (raqam) va API HASH (32 ta hex belgi) ni ajratadi — tartibi va ajratuvchisi muhim emas."""
    m_hash = re.search(r"(?<![0-9A-Za-z])([0-9a-fA-F]{32})(?![0-9A-Za-z])", text or "")
    m_id = re.search(r"(?<![0-9A-Za-z])(\d{4,12})(?![0-9A-Za-z])", text or "")
    if not m_hash or not m_id:
        return None
    return int(m_id.group(1)), m_hash.group(1).lower()


@router.callback_query(F.data == "own:api")
async def api_cb(q: CallbackQuery, state: FSMContext):
    await state.set_state(Own.api)
    have = bool(config.API_ID and config.API_HASH)
    status = f"✅ kiritilgan (API ID: <code>{config.API_ID}</code>)" if have else "▫️ kiritilmagan"
    await safe_edit(
        q.message,
        "🔑 <b>Telegram API ID / HASH</b>\n\n"
        f"Holat: {status}\n\n"
        "my.telegram.org → API development tools dan olingan <b>API ID</b> va <b>API HASH</b> ni "
        "bitta xabarda yuboring, masalan:\n<code>12345678 0123456789abcdef0123456789abcdef</code>\n\n"
        "Xabar darhol o'chiriladi, HASH bazada shifrlangan holda saqlanadi.",
        CANCEL,
    )
    await q.answer()


@router.message(Own.api, F.text)
async def got_api(m: Message, state: FSMContext):
    found = _parse_api(m.text)
    await _del(m)
    if not found:
        return await m.answer(
            "❌ API ID (raqam) va API HASH (32 ta belgi) ni bitta xabarda yuboring.", reply_markup=CANCEL
        )
    api_id, api_hash = found
    await db.set_setting("api_id", str(api_id))
    await db.set_setting("api_hash", crypto.enc(api_hash))
    config.API_ID, config.API_HASH = api_id, api_hash
    await state.clear()
    started = await assistants.load_missing()
    await m.answer(
        f"✅ API ID/HASH saqlandi. Ishga tushgan yordamchilar: <b>{len(assistants.items)}</b>"
        + (f" (yangi: {started})" if started else "")
        + "\n\nEndi 👤 Yordamchilar bo'limidan akkaunt qo'shishingiz mumkin.",
        reply_markup=Markup(inline_keyboard=[[BACK]]),
    )


# ───────────────────────────── yordamchilar ─────────────────────────────
async def asst_view() -> tuple[str, Markup]:
    rows = await db.list_assistants()
    ld = player.loads()
    lines = ["👤 <b>Yordamchi akkauntlar</b>", ""]
    kb: list[list] = []
    if not rows:
        lines.append("Hozircha yo'q. Pastdagi tugmalar orqali qo'shing.")
    for uid, name, _phone, _s in rows:
        if uid in assistants.items:
            lines.append(f"✅ <b>{html.escape(name)}</b> (<code>{uid}</code>) — {ld.get(uid, 0)} ta faol chat")
        else:
            err = html.escape(assistants.failed.get(uid, "noma'lum xato"))
            lines.append(f"⚠️ <b>{html.escape(name)}</b> (<code>{uid}</code>) — ishlamayapti: {err}")
        kb.append([B(f"🗑 O'chirish: {name or uid}", cb=f"own:adel:{uid}", style="danger")])
    lines += ["", "Har bir guruhga bitta yordamchi biriktiriladi (eng kam yuklangani)."]
    kb.append([B("➕ Telefon orqali", cb="own:aphone", style="success"), B("🔑 Session string", cb="own:astr", style="primary")])
    kb.append([BACK])
    return "\n".join(lines), Markup(inline_keyboard=kb)


@router.callback_query(F.data == "own:asst")
async def asst_cb(q: CallbackQuery, state: FSMContext):
    await state.clear()
    text, kb = await asst_view()
    await safe_edit(q.message, text, kb)
    await q.answer()


@router.callback_query(F.data == "own:aphone")
async def aphone_cb(q: CallbackQuery, state: FSMContext):
    if not (config.API_ID and config.API_HASH):
        return await q.answer("Avval asosiy menyudagi 🔑 API ID/HASH ni kiriting.", show_alert=True)
    await state.set_state(Own.phone)
    await safe_edit(
        q.message,
        "📱 Yordamchi akkaunt telefon raqamini yuboring (masalan <code>+998901234567</code>).\n\n"
        "⚠️ Alohida (asosiy emas) akkaunt ishlating.",
        CANCEL,
    )
    await q.answer()


@router.message(Own.phone, F.text)
async def got_phone(m: Message, state: FSMContext):
    phone = re.sub(r"[^\d+]", "", m.text)
    if not phone.startswith("+"):
        phone = "+" + phone
    await _del(m)
    wait = await m.answer("⏳ Kod yuborilmoqda...")
    try:
        await assistants.login_begin(m.from_user.id, phone)
    except PhoneNumberInvalid:
        return await wait.edit_text("❌ Telefon raqam noto'g'ri. Qayta yuboring.", reply_markup=CANCEL)
    except FloodWait as exc:
        await state.clear()
        return await wait.edit_text(f"⏳ Telegram {exc.value} soniya kutishni so'radi. Keyinroq urinib ko'ring.")
    except Exception as exc:  # noqa: BLE001
        await state.clear()
        return await wait.edit_text(f"❌ Xato: <code>{html.escape(str(exc)[:200])}</code>")
    await state.set_state(Own.code)
    await wait.edit_text(
        "📲 Telegram akkauntga kod yubordi.\n\n"
        "Kodni <b>raqamlar orasiga bo'sh joy qo'yib</b> yozing, masalan: <code>1 2 3 4 5</code>\n"
        "(oddiy yozsangiz Telegram kodni bekor qilishi mumkin).",
        reply_markup=CANCEL,
    )


async def _login_done(m: Message, state: FSMContext) -> None:
    await state.clear()
    text, kb = await asst_view()
    await m.answer("✅ Yordamchi akkaunt qo'shildi va ishga tushdi.\n\n" + text, reply_markup=kb)


@router.message(Own.code, F.text)
async def got_code(m: Message, state: FSMContext):
    code = re.sub(r"\D", "", m.text)
    await _del(m)
    try:
        result = await assistants.login_code(m.from_user.id, code)
    except PhoneCodeInvalid:
        return await m.answer("❌ Kod noto'g'ri. Qayta yuboring.", reply_markup=CANCEL)
    except PhoneCodeExpired:
        await assistants.login_cancel(m.from_user.id)
        await state.clear()
        return await m.answer("⌛ Kod eskirdi. Qaytadan boshlang: /panel")
    except Exception as exc:  # noqa: BLE001
        await assistants.login_cancel(m.from_user.id)
        await state.clear()
        return await m.answer(f"❌ Xato: <code>{html.escape(str(exc)[:200])}</code>")
    if result == "2fa":
        await state.set_state(Own.password)
        return await m.answer("🔐 Akkauntda 2 bosqichli parol bor. Parolni yuboring:", reply_markup=CANCEL)
    await _login_done(m, state)


@router.message(Own.password, F.text)
async def got_password(m: Message, state: FSMContext):
    pw = m.text
    await _del(m)
    try:
        await assistants.login_password(m.from_user.id, pw)
    except PasswordHashInvalid:
        return await m.answer("❌ Parol noto'g'ri. Qayta yuboring.", reply_markup=CANCEL)
    except Exception as exc:  # noqa: BLE001
        await assistants.login_cancel(m.from_user.id)
        await state.clear()
        return await m.answer(f"❌ Xato: <code>{html.escape(str(exc)[:200])}</code>")
    await _login_done(m, state)


@router.callback_query(F.data == "own:astr")
async def astr_cb(q: CallbackQuery, state: FSMContext):
    if not (config.API_ID and config.API_HASH):
        return await q.answer("Avval asosiy menyudagi 🔑 API ID/HASH ni kiriting.", show_alert=True)
    await state.set_state(Own.session)
    await safe_edit(q.message, "🔑 Pyrogram <b>session string</b> yuboring. Xabar darhol o'chiriladi.", CANCEL)
    await q.answer()


@router.message(Own.session, F.text)
async def got_session(m: Message, state: FSMContext):
    session = m.text.strip()
    await _del(m)
    try:
        await assistants.add_session(session)
    except Exception as exc:  # noqa: BLE001
        await state.clear()
        return await m.answer(f"❌ Session ishlamadi: <code>{html.escape(str(exc)[:200])}</code>")
    await _login_done(m, state)


@router.callback_query(F.data.startswith("own:adel:"))
async def adel_cb(q: CallbackQuery):
    uid = int(q.data.split(":")[2])
    for cid in player.chats_of(uid):
        await player.end(cid)
    await assistants.remove(uid)
    text, kb = await asst_view()
    await safe_edit(q.message, text, kb)
    await q.answer("O'chirildi")


# ───────────────────────────── media ─────────────────────────────
async def media_view() -> tuple[str, Markup]:
    kb = []
    for slot, label in media.SLOTS.items():
        mark = "✅ o'rnatilgan" if await media.get_slot(slot) else "▫️ standart"
        kb.append([B(f"{label} — {mark}", cb=f"own:mslot:{slot}", style="primary")])
    kb.append([BACK])
    text = "🖼 <b>Media</b>\n\nQaysi joyning rasmi yoki GIF'ini almashtiramiz?"
    return text, Markup(inline_keyboard=kb)


@router.callback_query(F.data == "own:media")
async def media_cb(q: CallbackQuery, state: FSMContext):
    await state.clear()
    text, kb = await media_view()
    await safe_edit(q.message, text, kb)
    await q.answer()


@router.callback_query(F.data.startswith("own:mslot:"))
async def mslot_cb(q: CallbackQuery):
    slot = q.data.split(":")[2]
    if slot not in media.SLOTS:
        return await q.answer()
    kb = Markup(inline_keyboard=[
        [B("🖼 Almashtirish", cb=f"own:mset:{slot}", style="success")],
        [B("🗑 Standartga qaytarish", cb=f"own:mclr:{slot}", style="danger")],
        [B("⬅️ Orqaga", cb="own:media", style="primary")],
    ])
    await safe_edit(q.message, f"{media.SLOTS[slot]}\n\nJoriy ko'rinish quyida yuborildi 👇", kb)
    await media.send_with_media(core.bot, q.message.chat.id, slot, "👀 Joriy media")
    await q.answer()


@router.callback_query(F.data.startswith("own:mset:"))
async def mset_cb(q: CallbackQuery, state: FSMContext):
    slot = q.data.split(":")[2]
    await state.set_state(Own.media)
    await state.update_data(slot=slot)
    await safe_edit(
        q.message,
        f"{media.SLOTS.get(slot, slot)}\n\n📎 Yangi <b>rasm yoki GIF</b> yuboring (video ham bo'ladi).",
        CANCEL,
    )
    await q.answer()


@router.message(Own.media)
async def got_media(m: Message, state: FSMContext):
    found = media.extract_media(m)
    if not found:
        return await m.answer("❌ Rasm yoki GIF yuboring.", reply_markup=CANCEL)
    slot = (await state.get_data()).get("slot", "start")
    await media.set_slot(slot, *found)
    await state.clear()
    await media.send_with_media(core.bot, m.chat.id, slot, "✅ Saqlandi. Endi shunday ko'rinadi.")
    text, kb = await media_view()
    await m.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("own:mclr:"))
async def mclr_cb(q: CallbackQuery):
    await media.clear_slot(q.data.split(":")[2])
    text, kb = await media_view()
    await safe_edit(q.message, text, kb)
    await q.answer("Standartga qaytarildi")


# ───────────────────────────── premium emoji ─────────────────────────────
async def emoji_view() -> tuple[str, Markup]:
    mapped = [e for e in premium.USED if premium.norm(e) in premium.EMOJI_MAP]
    free = [e for e in premium.USED if premium.norm(e) not in premium.EMOJI_MAP]
    text = (
        "💎 <b>Premium emoji</b>\n\n"
        "Bot matnlaridagi oddiy emoji o'rniga o'zingizning premium emojingizni qo'yish mumkin: "
        "premium emojini shu yerga yuboring — bot uning oddiy ko'rinishini topib, shunga bog'laydi.\n\n"
        f"✅ Ulangan ({len(mapped)}): {' '.join(mapped) or '—'}\n\n"
        f"▫️ Ulanmagan ({len(free)}): {' '.join(free) or '—'}"
    )
    kb = Markup(inline_keyboard=[
        [B("➕ Premium emoji qo'shish", cb="own:emoji_add", style="success")],
        [B("🎵 Sinab ko'rish", cb="own:emoji_test", style="primary"), B("🗑 Hammasini tozalash", cb="own:emoji_reset", style="danger")],
        [BACK],
    ])
    return text, kb


@router.callback_query(F.data == "own:emoji")
async def emoji_cb(q: CallbackQuery, state: FSMContext):
    await state.clear()
    text, kb = await emoji_view()
    await safe_edit(q.message, text, kb)
    await q.answer()


@router.callback_query(F.data == "own:emoji_add")
async def emoji_add_cb(q: CallbackQuery, state: FSMContext):
    await state.set_state(Own.emoji)
    await safe_edit(
        q.message,
        "💎 Premium emojilarni yuboring (bir xabarda bir nechta bo'lishi mumkin).\n\n"
        "Har bir premium emoji o'zining oddiy ko'rinishi (masalan 🎵) o'rniga ishlatiladi.",
        CANCEL,
    )
    await q.answer()


@router.message(Own.emoji)
async def got_emoji(m: Message, state: FSMContext):
    text = m.text or m.caption or ""
    ents = [e for e in (m.entities or m.caption_entities or []) if e.type == "custom_emoji"]
    if not ents:
        return await m.answer("❌ Xabarda premium emoji topilmadi. Premium emoji yuboring.", reply_markup=CANCEL)
    saved = []
    for e in ents:
        ch = premium.norm(e.extract_from(text)).strip()
        if ch:
            await db.emoji_set(ch, e.custom_emoji_id)
            saved.append(ch)
    premium.load(await db.emoji_all())
    await state.clear()
    await m.answer(f"✅ {len(saved)} ta emoji ulandi: {' '.join(saved)}")
    text2, kb = await emoji_view()
    await m.answer(text2, reply_markup=kb)


@router.callback_query(F.data == "own:emoji_test")
async def emoji_test_cb(q: CallbackQuery):
    await q.message.answer("🧪 " + " ".join(premium.USED))
    await q.answer()


@router.callback_query(F.data == "own:emoji_reset")
async def emoji_reset_cb(q: CallbackQuery):
    await db.emoji_clear()
    premium.load({})
    text, kb = await emoji_view()
    await safe_edit(q.message, text, kb)
    await q.answer("Tozalandi")


# ───────────────────────────── cookies ─────────────────────────────
@router.callback_query(F.data == "own:cookies")
async def cookies_cb(q: CallbackQuery, state: FSMContext):
    await state.set_state(Own.cookies)
    have = os.path.exists(config.COOKIES_FILE)
    await safe_edit(
        q.message,
        "🍪 <b>YouTube cookies</b>\n\n"
        f"Hozirgi holat: {'✅ yuklangan' if have else '▫️ yo‘q'}\n\n"
        "Netscape formatdagi <b>cookies.txt</b> faylini yuboring. Fayl bazada saqlanadi (qayta ishga tushganda yo'qolmaydi) "
        "va xabar darhol o'chiriladi.",
        CANCEL,
    )
    await q.answer()


@router.message(Own.cookies, F.document)
async def got_cookies(m: Message, state: FSMContext):
    doc = m.document
    if doc.file_size and doc.file_size > 2_000_000:
        return await m.answer("❌ Fayl juda katta.", reply_markup=CANCEL)
    buf = io.BytesIO()
    await core.bot.download(doc, destination=buf)
    raw = buf.getvalue().decode("utf-8", "ignore")
    await _del(m)
    if "youtube.com" not in raw and "google.com" not in raw:
        return await m.answer("❌ Bu YouTube cookies fayliga o'xshamaydi (youtube.com topilmadi).", reply_markup=CANCEL)
    with open(config.COOKIES_FILE, "w", encoding="utf-8") as f:
        f.write(raw)
    await db.set_setting("cookies", raw)
    count = sum(1 for ln in raw.splitlines() if ln.strip() and not ln.startswith("#"))
    await state.clear()
    await m.answer(f"✅ Cookies saqlandi ({count} ta yozuv).", reply_markup=Markup(inline_keyboard=[[BACK]]))


# ───────────────────────────── reklama (broadcast) ─────────────────────────────
BC = {"running": False, "cancel": False}


def _bc_markup(btns: list) -> Markup | None:
    if not btns:
        return None
    return Markup(inline_keyboard=[[B(text, url=url, style="primary")] for text, url in btns])


def _bc_menu(has_btns: bool) -> Markup:
    return Markup(inline_keyboard=[
        [B("➕ Tugma qo'shish" + (" ✅" if has_btns else ""), cb="own:bc_btn", style="primary")],
        [B("👥 Guruhlar", cb="own:bc_go:chats", style="success"), B("👤 Foydalanuvchilar", cb="own:bc_go:users", style="success")],
        [B("🌐 Hammasi", cb="own:bc_go:all", style="success")],
        [B("✖️ Bekor qilish", cb="own:cancel", style="danger")],
    ])


@router.callback_query(F.data == "own:bc")
async def bc_cb(q: CallbackQuery, state: FSMContext):
    await state.set_state(Own.bc_content)
    await safe_edit(
        q.message,
        "📣 <b>Reklama</b>\n\nYubormoqchi bo'lgan xabarni yuboring: matn, rasm, GIF yoki video "
        "(formatlash va premium emojilar saqlanadi).",
        CANCEL,
    )
    await q.answer()


@router.message(Own.bc_content)
async def bc_content(m: Message, state: FSMContext):
    await state.update_data(bc_src=[m.chat.id, m.message_id], bc_btns=[])
    await state.set_state(None)
    await m.answer("✅ Reklama qabul qilindi. Kimga yuboramiz?", reply_markup=_bc_menu(False))


@router.callback_query(F.data == "own:bc_btn")
async def bc_btn_cb(q: CallbackQuery, state: FSMContext):
    await state.set_state(Own.bc_buttons)
    await safe_edit(
        q.message,
        "➕ Tugmalarni har qatorga bittadan yozing:\n<code>Matn - https://havola.uz</code>\n\n"
        "Tugma kerak bo'lmasa <code>-</code> yuboring.",
        CANCEL,
    )
    await q.answer()


@router.message(Own.bc_buttons, F.text)
async def bc_buttons(m: Message, state: FSMContext):
    btns = []
    for line in m.text.splitlines():
        mt = re.match(r"^(.+?)\s*[-–—|]\s*(https?://\S+)$", line.strip())
        if mt:
            btns.append((mt.group(1).strip(), mt.group(2)))
    await state.update_data(bc_btns=btns)
    await state.set_state(None)
    await m.answer(f"✅ {len(btns)} ta tugma. Kimga yuboramiz?", reply_markup=_bc_menu(bool(btns)))


async def _targets(kind: str) -> list[int]:
    ids: list[int] = []
    if kind in ("chats", "all"):
        ids += await db.all_chat_ids()
    if kind in ("users", "all"):
        ids += await db.all_user_ids()
    return list(dict.fromkeys(ids))


@router.callback_query(F.data.startswith("own:bc_go:"))
async def bc_go_cb(q: CallbackQuery, state: FSMContext):
    kind = q.data.split(":")[2]
    data = await state.get_data()
    src = data.get("bc_src")
    if not src:
        return await q.answer("Avval reklama xabarini yuboring.", show_alert=True)
    total = len(await _targets(kind))
    await q.message.answer("👀 Ko'rinishi (ko'chirma):")
    try:
        await core.bot.copy_message(
            chat_id=q.message.chat.id, from_chat_id=src[0], message_id=src[1],
            reply_markup=_bc_markup(data.get("bc_btns", [])),
        )
    except Exception as exc:  # noqa: BLE001
        return await q.message.answer(f"❌ Ko'rsatib bo'lmadi: <code>{html.escape(str(exc)[:200])}</code>")
    names = {"chats": "guruhga", "users": "foydalanuvchiga", "all": "manzilga"}
    await q.message.answer(
        f"📣 Jami <b>{total}</b> ta {names[kind]} yuboriladi. Boshlaymizmi?",
        reply_markup=Markup(inline_keyboard=[
            [B("✅ Boshlash", cb=f"own:bc_run:{kind}", style="success"), B("✖️ Bekor", cb="own:cancel", style="danger")],
        ]),
    )
    await q.answer()


@router.callback_query(F.data.startswith("own:bc_run:"))
async def bc_run_cb(q: CallbackQuery, state: FSMContext):
    if BC["running"]:
        return await q.answer("Reklama allaqachon yuborilmoqda.", show_alert=True)
    kind = q.data.split(":")[2]
    data = await state.get_data()
    src = data.get("bc_src")
    if not src:
        return await q.answer("Sessiya tugagan. /panel dan qayta boshlang.", show_alert=True)
    ids = await _targets(kind)
    markup = _bc_markup(data.get("bc_btns", []))
    await state.clear()
    BC.update(running=True, cancel=False)
    await q.answer()
    await safe_edit(q.message, f"📣 Yuborish boshlandi: 0/{len(ids)}", _stop_markup())
    asyncio.create_task(_run_broadcast(q.message, src, markup, ids))


def _stop_markup() -> Markup:
    return Markup(inline_keyboard=[[B("⛔ To'xtatish", cb="own:bc_stop", style="danger")]])


@router.callback_query(F.data == "own:bc_stop")
async def bc_stop_cb(q: CallbackQuery):
    BC["cancel"] = True
    await q.answer("To'xtatilmoqda...")


async def _run_broadcast(progress: Message, src: list[int], markup, ids: list[int]) -> None:
    sent = failed = removed = 0
    total = len(ids)
    try:
        for i, cid in enumerate(ids, 1):
            if BC["cancel"]:
                break
            for attempt in range(2):
                try:
                    await core.bot.copy_message(chat_id=cid, from_chat_id=src[0], message_id=src[1], reply_markup=markup)
                    sent += 1
                    break
                except TelegramRetryAfter as exc:
                    await asyncio.sleep(exc.retry_after + 1)
                    if attempt == 1:
                        failed += 1
                except TelegramForbiddenError:
                    failed += 1
                    removed += 1
                    await (db.remove_chat(cid) if cid < 0 else db.remove_user(cid))
                    break
                except TelegramBadRequest as exc:
                    failed += 1
                    msg = str(exc).lower()
                    if "chat not found" in msg or "deactivated" in msg:
                        removed += 1
                        await (db.remove_chat(cid) if cid < 0 else db.remove_user(cid))
                    break
                except Exception:  # noqa: BLE001
                    failed += 1
                    break
            await asyncio.sleep(0.05)  # ~20 xabar/soniya — Telegram limitidan past
            if i % 40 == 0:
                try:
                    await progress.edit_text(
                        f"📣 Yuborilmoqda: {i}/{total}\n✅ {sent} · ❌ {failed} · 🗑 {removed}", reply_markup=_stop_markup()
                    )
                except Exception:  # noqa: BLE001
                    pass
    finally:
        stopped = BC["cancel"]
        BC.update(running=False, cancel=False)
        try:
            await progress.edit_text(
                f"{'⛔ To‘xtatildi' if stopped else '✅ Tugadi'}\n\n"
                f"Jami: {total}\n✅ Yuborildi: {sent}\n❌ Xato: {failed}\n🗑 Bazadan o'chirildi: {removed}",
                reply_markup=Markup(inline_keyboard=[[BACK]]),
            )
        except Exception:  # noqa: BLE001
            pass
''')

# ══════════ ISHGA TUSHIRISH (main.py) ══════════
import asyncio
import html
import logging

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import assistants
import cobalt
import config
import core
import crypto
import db
import premium
import handlers_owner
import handlers_user
import menu
import player
import song

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("main")


async def _on_stream_end(chat_id: int) -> None:
    await player.on_stream_end(chat_id)


async def _on_closed(chat_id: int) -> None:
    await player.end(chat_id)


async def main() -> None:
    await db.init()
    premium.load(await db.emoji_all())

    # owner paneldan yuklangan cookies bazadan tiklanadi
    saved_cookies = await db.get_setting("cookies")
    if saved_cookies:
        with open(config.COOKIES_FILE, "w", encoding="utf-8") as f:
            f.write(saved_cookies)

    me = await core.bot.get_me()
    core.BOT_USERNAME = me.username or ""
    core.BOT_NAME = me.first_name

    core.bot.session.middleware(premium.EmojiMiddleware())
    await menu.setup()  # buyruqlar menyusi: hamma uchun umumiy + egalar uchun alohida

    assistants.set_callbacks(_on_stream_end, _on_closed)
    # panel orqali kiritilgan API ID/HASH bazadan olinadi (Railway'dagi qiymatdan ustun)
    sid, shash = await db.get_setting("api_id"), await db.get_setting("api_hash")
    if sid and shash:
        try:
            config.API_ID, config.API_HASH = int(sid), crypto.dec(shash)
        except Exception as exc:  # noqa: BLE001
            log.error("bazadagi API ID/HASH o'qilmadi: %s", exc)
    have_api = bool(config.API_ID and config.API_HASH)
    if have_api:
        await assistants.load_all()
    else:
        log.warning("API_ID/API_HASH yo'q: /panel → 🔑 API ID/HASH orqali kiriting")
    if have_api and config.BOOT_SESSION and not assistants.items and not await db.list_assistants():
        try:
            await assistants.add_session(config.BOOT_SESSION)
        except Exception as exc:  # noqa: BLE001
            log.error("SESSION_STRING ishlamadi: %s", exc)

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(handlers_owner.router)  # owner panel birinchi (FSM holatlari ustun)
    dp.include_router(song.router)  # /song — agar handlers_user'da /song bo'lsa, shu qatorni o'chiring
    dp.include_router(handlers_user.router)

    await core.bot.delete_webhook(drop_pending_updates=True)
    log.info("@%s tayyor, yordamchilar: %d", core.BOT_USERNAME, len(assistants.items))
    if cobalt.enabled():
        try:
            cb_line = f"\n🔗 Cobalt API: ✅ v{await cobalt.info()}"
        except Exception as exc:  # noqa: BLE001
            cb_line = f"\n🔗 Cobalt API: ⚠️ <code>{html.escape(str(exc)[:150])}</code>"
    else:
        cb_line = "\n🔗 Cobalt API: o'chiq (COBALT_API_URL bo'sh)"
    await player.log_owner(
        f"✅ <b>{me.first_name}</b> ishga tushdi. Yordamchilar: {len(assistants.items)}. Panel: /panel" + cb_line
        + ("" if have_api else "\n⚠️ API ID/HASH kiritilmagan: /panel → 🔑 API ID/HASH")
    )

    watchdog = asyncio.create_task(assistants.watchdog())  # ishga tushmagan yordamchilarni qayta ulaydi
    try:
        await dp.start_polling(core.bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        watchdog.cancel()
        await assistants.stop_all()
        await core.bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
