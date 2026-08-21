# ===== RUST LFG BOT v14.0 (Fixed + Full Admin + Mass Ready) =====
import os
import re
import html
import asyncio
import sqlite3
import aiohttp
from datetime import datetime
from contextlib import contextmanager
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, BaseMiddleware, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError

# ================== CONFIG ==================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_ТОКЕН"
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
OWNER_ID = 6276697402
ADMIN_IDS = [OWNER_ID]

DB_PATH = os.getenv("DB_PATH", "/data/rust_clan.db")
RUSTYLUB_URL = "https://rustylub.github.io/Rusty.Lub/"

if not TOKEN or TOKEN == "ВСТАВЬ_ТОКЕН":
    raise ValueError("❌ Укажи BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

last_message_time = {}
RATE_LIMIT_SECONDS = 1.5
DAILY_SWIPE_LIMIT = 50
REPORT_LIMIT_PER_DAY = 3

# ================== TEXTS ==================
TEXTS = {
    "ru": {
        "start": (
            "🦀 <b>Rust LFG Bot</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Быстро находи тиммейтов, дуо, трио или клан.\n"
            "Создавай анкету, свайпай и находи игроков за минуты.\n\n"
            "🔥 Полезный сайт по Rust:\n"
            f"<a href='{RUSTYLUB_URL}'>Rusty.Lub</a>\n"
            "• Ошибки и фиксы\n"
            "• Бинды / FPS\n"
            "• Калькулятор рейда\n"
            "• Гайды\n\n"
            "Выбери действие ниже 👇"
        ),
        "choose_lang": "🌐 Выбери язык:",
        "choose_country": "🌍 Выбери страну:",
        "lang_set": "✅ Язык сохранён",
        "country_set": "✅ Страна сохранена",
        "cancel": "✅ Отменено",
        "already_has": "У тебя уже есть активная анкета.",
        "no_profile": "У тебя пока нет анкеты.",
        "wait": "⏳ Подожди немного",
        "no_profiles": "Пока нет активных анкет.",
        "shown": "Показано {} из {}",
        "fav_empty": "Избранных пока нет",
        "swipe_limit": "Дневной лимит свайпов. Завтра снова!",
        "swipe_restart": "Анкеты закончились, начинаю заново",
        "mutual": "💕 <b>Новый мэтч!</b>\nВзаимный интерес с @{}",
        "report_ask": "Опиши причину жалобы:",
        "report_sent": "Жалоба отправлена",
        "report_limit": "Слишком много жалоб за сутки",
        "banned": "🚫 Вы забанены.\nПричина: {}",
        "m_create": "📝 Создать",
        "m_search": "🔍 Поиск",
        "m_my": "👤 Анкета",
        "m_delete": "🗑 Удалить",
        "m_fav": "⭐ Избранное",
        "m_swipe": "💕 Свайп",
        "m_matches": "💞 Мэтчи",
        "m_stats": "📊 Стата",
        "m_check": "🕵️ Проверить",
        "m_web": "🌐 Rusty.Lub",
        "m_lang": "🌐 Язык",
        "m_country": "🌍 Страна",
        "m_new": "🆕 Новое",
        "rustylub": (
            "🔥 <b>Rusty.Lub</b>\n\n"
            "Ультимативный справочник по Rust:\n"
            "• Ошибки и фиксы\n"
            "• Бинды и FPS\n"
            "• Калькулятор рейда\n"
            "• Гайды по оружию и монументам\n\n"
            f"👉 <a href='{RUSTYLUB_URL}'>Открыть сайт</a>"
        ),
    },
    "en": {
        "start": (
            "🦀 <b>Rust LFG Bot</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Quickly find teammates, duo, trio or a clan.\n"
            "Create a profile, swipe and meet players in minutes.\n\n"
            "🔥 Useful Rust website:\n"
            f"<a href='{RUSTYLUB_URL}'>Rusty.Lub</a>\n"
            "• Error fixes\n"
            "• Keybinds / FPS\n"
            "• Raid calculator\n"
            "• Guides\n\n"
            "Choose an action below 👇"
        ),
        "choose_lang": "🌐 Choose language:",
        "choose_country": "🌍 Choose country:",
        "lang_set": "✅ Language saved",
        "country_set": "✅ Country saved",
        "cancel": "✅ Cancelled",
        "already_has": "You already have an active profile.",
        "no_profile": "You don't have a profile yet.",
        "wait": "⏳ Please wait",
        "no_profiles": "No active profiles yet.",
        "shown": "Shown {} of {}",
        "fav_empty": "No favorites yet",
        "swipe_limit": "Daily swipe limit reached. Come back tomorrow!",
        "swipe_restart": "No more profiles, starting over",
        "mutual": "💕 <b>New match!</b>\nMutual interest with @{}",
        "report_ask": "Describe the reason:",
        "report_sent": "Report sent",
        "report_limit": "Too many reports today",
        "banned": "🚫 You are banned.\nReason: {}",
        "m_create": "📝 Create",
        "m_search": "🔍 Search",
        "m_my": "👤 Profile",
        "m_delete": "🗑 Delete",
        "m_fav": "⭐ Favorites",
        "m_swipe": "💕 Swipe",
        "m_matches": "💞 Matches",
        "m_stats": "📊 Stats",
        "m_check": "🕵️ Check",
        "m_web": "🌐 Rusty.Lub",
        "m_lang": "🌐 Language",
        "m_country": "🌍 Country",
        "m_new": "🆕 New",
        "rustylub": (
            "🔥 <b>Rusty.Lub</b>\n\n"
            "Ultimate Rust handbook:\n"
            "• Error fixes\n"
            "• Keybinds & FPS\n"
            "• Raid calculator\n"
            "• Guides\n\n"
            f"👉 <a href='{RUSTYLUB_URL}'>Open website</a>"
        ),
    }
}

# ================== DATABASE ==================
@contextmanager
def get_db():
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                looking_for TEXT,
                description TEXT,
                age TEXT,
                microphone TEXT,
                timezone TEXT,
                country TEXT,
                discord TEXT,
                steam TEXT,
                contact_pref TEXT DEFAULT 'Telegram',
                date TEXT,
                language TEXT DEFAULT 'ru',
                last_active TEXT,
                active INTEGER DEFAULT 1
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                favorite_id INTEGER,
                date TEXT,
                UNIQUE(user_id, favorite_id)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                reason TEXT,
                banned_by INTEGER,
                date TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER,
                reported_id INTEGER,
                reason TEXT,
                date TEXT,
                resolved INTEGER DEFAULT 0
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS swipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                target_id INTEGER,
                action TEXT,
                date TEXT,
                UNIQUE(user_id, target_id)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                blocked_id INTEGER,
                date TEXT,
                UNIQUE(user_id, blocked_id)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                date TEXT,
                UNIQUE(user1_id, user2_id)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                date TEXT,
                sent_by INTEGER
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                active INTEGER DEFAULT 1,
                date TEXT,
                created_by INTEGER
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                details TEXT,
                date TEXT
            )
        ''')
        cur.execute("CREATE INDEX IF NOT EXISTS idx_profiles_lang ON profiles(active, language)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_swipes_user ON swipes(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id, date)")
        conn.commit()

def cleanup_old_data():
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM swipes WHERE date < datetime('now', '-90 days')")
            conn.commit()
    except Exception as e:
        print("Cleanup error:", e)

init_db()

# ================== HELPERS ==================
def is_admin(user_id) -> bool:
    try:
        return int(user_id) in ADMIN_IDS
    except:
        return False

def get_lang(user_id: int) -> str:
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT language FROM profiles WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if row and row["language"] in ("ru", "en"):
                return row["language"]
    except:
        pass
    return "ru"

def t(user_id: int, key: str) -> str:
    return TEXTS.get(get_lang(user_id), TEXTS["ru"]).get(key, key)

def update_last_active(user_id: int):
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE profiles SET last_active = ? WHERE user_id = ?",
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
    except:
        pass

def is_banned(user_id: int):
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT reason FROM bans WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return row["reason"] if row else None
    except:
        return None

def get_daily_swipes(user_id: int) -> int:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as cnt FROM swipes WHERE user_id = ? AND date >= datetime('now', '-1 day')",
            (user_id,)
        )
        return cur.fetchone()["cnt"]

def get_daily_reports(user_id: int) -> int:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as cnt FROM reports WHERE reporter_id = ? AND date >= datetime('now', '-1 day')",
            (user_id,)
        )
        return cur.fetchone()["cnt"]

def check_rate_limit(user_id: int) -> bool:
    now = datetime.now()
    last = last_message_time.get(user_id)
    if last and (now - last).total_seconds() < RATE_LIMIT_SECONDS:
        return False
    last_message_time[user_id] = now
    return True

def admin_log(admin_id: int, action: str, details: str = ""):
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO admin_logs (admin_id, action, details, date) VALUES (?, ?, ?, ?)",
                (admin_id, action, details[:500], datetime.now().isoformat())
            )
            conn.commit()
    except Exception as e:
        print("admin_log:", e)

def format_profile(r) -> str:
    username = html.escape(r["username"] or "Unknown")
    country = html.escape(r["country"] or "—")
    looking = html.escape(r["looking_for"] or "—")
    age = html.escape(r["age"] or "—")
    mic = html.escape(r["microphone"] or "—")
    tz = html.escape(r["timezone"] or "—")
    desc = html.escape((r["description"] or "")[:220])
    if len(r["description"] or "") > 220:
        desc += "..."

    contact = "📱 Telegram"
    if r["contact_pref"] == "Discord" and r["discord"]:
        contact = f"🎧 Discord: <code>{html.escape(r['discord'])}</code>"
    elif r["contact_pref"] == "Steam" and r["steam"]:
        contact = f"🎮 Steam: {html.escape(r['steam'])}"

    return (
        f"👤 <b>@{username}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎯 {looking}\n"
        f"🎂 {age}  •  🎤 {mic}\n"
        f"🕐 {tz}  •  🌍 {country}\n"
        f"{contact}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"{desc}"
    )

def get_random_ad() -> str | None:
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT text FROM ads WHERE active = 1 ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
            return row["text"] if row else None
    except:
        return None

def get_bot_stats() -> dict:
    with get_db() as conn:
        cur = conn.cursor()
        s = {}
        cur.execute("SELECT COUNT(*) as c FROM profiles")
        s["users"] = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM profiles WHERE active=1 AND looking_for IS NOT NULL")
        s["profiles"] = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM profiles WHERE language='ru'")
        s["ru"] = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM profiles WHERE language='en'")
        s["en"] = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM matches")
        s["matches"] = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM swipes")
        s["swipes"] = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM bans")
        s["bans"] = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM reports WHERE resolved=0")
        s["reports_open"] = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM ads WHERE active=1")
        s["ads"] = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM profiles WHERE date >= datetime('now', '-1 day')")
        s["new_24h"] = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM profiles WHERE last_active >= datetime('now', '-1 day')")
        s["active_24h"] = cur.fetchone()["c"]
    return s

# ================== STEAM ==================
async def resolve_steamid(text: str) -> str | None:
    text = text.strip()
    if re.fullmatch(r"7656119\d{10}", text):
        return text
    m = re.search(r"profiles/(\d{17})", text)
    if m:
        return m.group(1)
    m = re.search(r"steamcommunity\.com/id/([^/\s]+)", text)
    if m and STEAM_API_KEY:
        vanity = m.group(1)
        url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={vanity}"
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as s:
                async with s.get(url) as r:
                    data = await r.json()
                    if data.get("response", {}).get("success") == 1:
                        return data["response"]["steamid"]
        except:
            return None
    return None

async def get_rust_stats(steamid: str) -> dict:
    res = {"hours": None, "kills": None, "deaths": None, "kd": None, "name": "Unknown"}
    if not STEAM_API_KEY:
        return res
    timeout = aiohttp.ClientTimeout(total=12)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as s:
            url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steamid}"
            async with s.get(url) as r:
                data = await r.json()
                players = data.get("response", {}).get("players", [])
                if players:
                    res["name"] = players[0].get("personaname", "Unknown")

            url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={STEAM_API_KEY}&steamid={steamid}&include_appinfo=1&appids_filter[0]=252490"
            async with s.get(url) as r:
                data = await r.json()
                games = data.get("response", {}).get("games", [])
                if games:
                    res["hours"] = round(games[0].get("playtime_forever", 0) / 60, 1)

            url = f"https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v2/?key={STEAM_API_KEY}&appid=252490&steamid={steamid}"
            async with s.get(url) as r:
                if r.status == 200:
                    data = await r.json()
                    stats = {x["name"]: x["value"] for x in data.get("playerstats", {}).get("stats", [])}
                    res["kills"] = stats.get("kill_player")
                    res["deaths"] = stats.get("deaths")
                    if res["kills"] is not None and res["deaths"]:
                        res["kd"] = round(res["kills"] / res["deaths"], 2)
                    elif res["kills"] is not None:
                        res["kd"] = res["kills"]
    except Exception as e:
        print("Steam API error:", e)
    return res

# ================== KEYBOARDS ==================
def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(user_id, "m_create")), KeyboardButton(text=t(user_id, "m_search"))],
            [KeyboardButton(text=t(user_id, "m_my")), KeyboardButton(text=t(user_id, "m_delete"))],
            [KeyboardButton(text=t(user_id, "m_swipe")), KeyboardButton(text=t(user_id, "m_matches"))],
            [KeyboardButton(text=t(user_id, "m_fav")), KeyboardButton(text=t(user_id, "m_check"))],
            [KeyboardButton(text=t(user_id, "m_web")), KeyboardButton(text=t(user_id, "m_stats"))],
            [KeyboardButton(text=t(user_id, "m_lang")), KeyboardButton(text=t(user_id, "m_country")), KeyboardButton(text=t(user_id, "m_new"))]
        ],
        resize_keyboard=True
    )

def lang_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇬🇧 English")]],
        resize_keyboard=True
    )

def country_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Россия"), KeyboardButton(text="🇺🇦 Украина")],
            [KeyboardButton(text="🇰🇿 Казахстан"), KeyboardButton(text="🇧🇾 Беларусь")],
            [KeyboardButton(text="🇪🇺 Европа"), KeyboardButton(text="🇺🇸 США / Канада")],
            [KeyboardButton(text="🌍 Другая")]
        ],
        resize_keyboard=True
    )

def age_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="16+"), KeyboardButton(text="18+"), KeyboardButton(text="21+")],
            [KeyboardButton(text="25+"), KeyboardButton(text="30+"), KeyboardButton(text="Другой")]
        ],
        resize_keyboard=True
    )

def mic_keyboard(user_id):
    ru = get_lang(user_id) == "ru"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎤 Есть" if ru else "🎤 Yes")],
            [KeyboardButton(text="🔇 Нет" if ru else "🔇 No")]
        ],
        resize_keyboard=True
    )

def contact_keyboard(user_id):
    ru = get_lang(user_id) == "ru"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telegram"), KeyboardButton(text="🎧 Discord")],
            [KeyboardButton(text="🎮 Steam"), KeyboardButton(text="Любой" if ru else "Any")]
        ],
        resize_keyboard=True
    )

def looking_keyboard(user_id):
    ru = get_lang(user_id) == "ru"
    if ru:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🤝 Ищу тиммейта")],
                [KeyboardButton(text="🏰 Ищу клан")],
                [KeyboardButton(text="📢 Набираю в клан")],
                [KeyboardButton(text="🎯 Просто поиграть")]
            ],
            resize_keyboard=True
        )
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🤝 Looking for teammate")],
            [KeyboardButton(text="🏰 Looking for clan")],
            [KeyboardButton(text="📢 Recruiting")],
            [KeyboardButton(text="🎯 Just play")]
        ],
        resize_keyboard=True
    )

# ================== STATE ==================
user_data: dict[int, dict] = {}
report_data: dict[int, dict] = {}

# ================== MIDDLEWARE ==================
class BanCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user:
            reason = is_banned(user.id)
            if reason:
                if isinstance(event, types.Message):
                    await event.answer(t(user.id, "banned").format(html.escape(str(reason))))
                else:
                    await event.answer("Banned", show_alert=True)
                return
        return await handler(event, data)

dp.message.middleware(BanCheckMiddleware())
dp.callback_query.middleware(BanCheckMiddleware())

# ================== START ==================
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    user_id = msg.from_user.id
    update_last_active(user_id)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO profiles (user_id, username, date, last_active) VALUES (?, ?, ?, ?)",
            (user_id, msg.from_user.username or "Unknown", datetime.now().isoformat(), datetime.now().isoformat())
        )
        conn.commit()
        cur.execute("SELECT language, country FROM profiles WHERE user_id = ?", (user_id,))
        row = cur.fetchone()

    if not row or not row["language"] or row["language"] not in ("ru", "en"):
        await msg.answer(TEXTS["ru"]["choose_lang"], reply_markup=lang_keyboard())
        user_data[user_id] = {"step": "choose_lang"}
        return

    if not row["country"]:
        await msg.answer(t(user_id, "choose_country"), reply_markup=country_keyboard())
        user_data[user_id] = {"step": "choose_country"}
        return

    await msg.answer(
        t(user_id, "start"),
        reply_markup=main_menu(user_id),
        parse_mode="HTML",
        disable_web_page_preview=False
    )
    ad = get_random_ad()
    if ad:
        await asyncio.sleep(0.25)
        await msg.answer(f"📢 {ad}")

@dp.message(F.text.in_(["🇷🇺 Русский", "🇬🇧 English"]))
async def set_language(msg: types.Message):
    user_id = msg.from_user.id
    lang = "ru" if "Русский" in msg.text else "en"
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE profiles SET language = ? WHERE user_id = ?", (lang, user_id))
        conn.commit()
    await msg.answer(t(user_id, "lang_set"))
    await msg.answer(t(user_id, "choose_country"), reply_markup=country_keyboard())
    user_data[user_id] = {"step": "choose_country"}

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "choose_country")
async def set_country(msg: types.Message):
    user_id = msg.from_user.id
    country = msg.text.strip()
    allowed = ["🇷🇺 Россия", "🇺🇦 Украина", "🇰🇿 Казахстан", "🇧🇾 Беларусь", "🇪🇺 Европа", "🇺🇸 США / Канада", "🌍 Другая"]
    if country not in allowed:
        await msg.answer("Выбери кнопкой")
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE profiles SET country = ? WHERE user_id = ?", (country, user_id))
        conn.commit()
    user_data.pop(user_id, None)
    await msg.answer(t(user_id, "country_set"))
    await msg.answer(
        t(user_id, "start"),
        reply_markup=main_menu(user_id),
        parse_mode="HTML",
        disable_web_page_preview=False
    )

@dp.message(Command("cancel"))
async def cmd_cancel(msg: types.Message):
    user_data.pop(msg.from_user.id, None)
    report_data.pop(msg.from_user.id, None)
    await msg.answer(t(msg.from_user.id, "cancel"), reply_markup=main_menu(msg.from_user.id))

# ================== PROFILE CREATE ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_create"], TEXTS["en"]["m_create"]]))
async def create_start(msg: types.Message):
    user_id = msg.from_user.id
    update_last_active(user_id)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM profiles WHERE user_id=? AND active=1 AND looking_for IS NOT NULL", (user_id,))
        if cur.fetchone():
            await msg.answer(t(user_id, "already_has"))
            return
    user_data[user_id] = {"step": "age"}
    await msg.answer("🎂 Возраст / Age:", reply_markup=age_keyboard())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "age")
async def p_age(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text.strip()
    if text == "Другой":
        user_data[user_id]["step"] = "age_custom"
        await msg.answer("Напиши возраст (14-60):", reply_markup=ReplyKeyboardRemove())
        return
    if text not in ["16+", "18+", "21+", "25+", "30+"]:
        await msg.answer("Выбери кнопкой")
        return
    user_data[user_id]["age"] = text
    user_data[user_id]["step"] = "mic"
    await msg.answer("🎤 Микрофон:", reply_markup=mic_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "age_custom")
async def p_age_c(msg: types.Message):
    user_id = msg.from_user.id
    if not msg.text.isdigit() or not (14 <= int(msg.text) <= 60):
        await msg.answer("Число от 14 до 60")
        return
    user_data[user_id]["age"] = msg.text
    user_data[user_id]["step"] = "mic"
    await msg.answer("🎤 Микрофон:", reply_markup=mic_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "mic")
async def p_mic(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["mic"] = "Есть" if ("Есть" in msg.text or "Yes" in msg.text) else "Нет"
    user_data[user_id]["step"] = "tz"
    await msg.answer("🕐 Часовой пояс (МСК+3 / UTC+3):", reply_markup=ReplyKeyboardRemove())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tz")
async def p_tz(msg: types.Message):
    user_id = msg.from_user.id
    if len(msg.text.strip()) < 2:
        await msg.answer("Напиши нормально")
        return
    user_data[user_id]["tz"] = msg.text.strip()[:40]
    user_data[user_id]["step"] = "contact"
    await msg.answer("📞 Как связываться?", reply_markup=contact_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "contact")
async def p_contact(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text
    if "Discord" in text:
        user_data[user_id]["contact_pref"] = "Discord"
        user_data[user_id]["step"] = "discord"
        await msg.answer("Введи Discord:", reply_markup=ReplyKeyboardRemove())
    elif "Steam" in text:
        user_data[user_id]["contact_pref"] = "Steam"
        user_data[user_id]["step"] = "steam"
        await msg.answer("Введи Steam / ссылку:", reply_markup=ReplyKeyboardRemove())
    else:
        user_data[user_id]["contact_pref"] = "Telegram"
        user_data[user_id]["discord"] = None
        user_data[user_id]["steam"] = None
        user_data[user_id]["step"] = "looking"
        await msg.answer("🎯 Что ищешь?", reply_markup=looking_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "discord")
async def p_discord(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["discord"] = msg.text.strip()[:60]
    user_data[user_id]["steam"] = None
    user_data[user_id]["step"] = "looking"
    await msg.answer("🎯 Что ищешь?", reply_markup=looking_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "steam")
async def p_steam(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["steam"] = msg.text.strip()[:120]
    user_data[user_id]["discord"] = None
    user_data[user_id]["step"] = "looking"
    await msg.answer("🎯 Что ищешь?", reply_markup=looking_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "looking")
async def p_looking(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["looking"] = msg.text[:80]
    user_data[user_id]["step"] = "desc"
    await msg.answer("📝 Коротко о себе:", reply_markup=ReplyKeyboardRemove())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "desc")
async def p_desc(msg: types.Message):
    user_id = msg.from_user.id
    if len(msg.text.strip()) < 8:
        await msg.answer("Слишком коротко (мин. 8 символов)")
        return
    data = user_data[user_id]
    data["description"] = msg.text.strip()[:700]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM profiles WHERE user_id=?", (user_id,))
        exists = cur.fetchone()
        if exists:
            cur.execute('''
                UPDATE profiles SET
                    username=?, looking_for=?, description=?, age=?, microphone=?, timezone=?,
                    discord=?, steam=?, contact_pref=?, date=?, language=?, last_active=?, active=1
                WHERE user_id=?
            ''', (
                msg.from_user.username or "Unknown", data.get("looking"), data.get("description"),
                data.get("age"), data.get("mic"), data.get("tz"), data.get("discord"), data.get("steam"),
                data.get("contact_pref", "Telegram"), datetime.now().isoformat(), get_lang(user_id),
                datetime.now().isoformat(), user_id
            ))
        else:
            cur.execute('''
                INSERT INTO profiles
                (user_id, username, looking_for, description, age, microphone, timezone,
                 discord, steam, contact_pref, date, language, last_active, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                user_id, msg.from_user.username or "Unknown", data.get("looking"), data.get("description"),
                data.get("age"), data.get("mic"), data.get("tz"), data.get("discord"), data.get("steam"),
                data.get("contact_pref", "Telegram"), datetime.now().isoformat(), get_lang(user_id),
                datetime.now().isoformat()
            ))
        conn.commit()
    await msg.answer("✅ Анкета создана!", reply_markup=main_menu(user_id))
    user_data.pop(user_id, None)

# ================== MY / DELETE ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_my"], TEXTS["en"]["m_my"]]))
async def my_profile(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM profiles WHERE user_id=? AND active=1", (user_id,))
        r = cur.fetchone()
    if not r or not r["looking_for"]:
        await msg.answer(t(user_id, "no_profile"))
        return
    await msg.answer(format_profile(r), parse_mode="HTML")

@dp.message(F.text.in_([TEXTS["ru"]["m_delete"], TEXTS["en"]["m_delete"]]))
async def delete_profile(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="del_yes"),
         InlineKeyboardButton(text="❌ Нет", callback_data="del_no")]
    ])
    await msg.answer("Удалить анкету?", reply_markup=kb)

@dp.callback_query(F.data.in_(["del_yes", "del_no"]))
async def del_cb(call: types.CallbackQuery):
    if call.data == "del_yes":
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE profiles SET active=0 WHERE user_id=?", (call.from_user.id,))
            conn.commit()
        await call.message.edit_text("✅ Удалено")
    else:
        await call.message.edit_text("Отменено")
    await call.answer()

# ================== SEARCH ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_search"], TEXTS["en"]["m_search"]]))
async def search(msg: types.Message):
    user_id = msg.from_user.id
    update_last_active(user_id)
    if not check_rate_limit(user_id):
        await msg.answer(t(user_id, "wait"))
        return
    lang = get_lang(user_id)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as c FROM profiles WHERE active=1 AND looking_for IS NOT NULL AND language=?",
            (lang,)
        )
        total = cur.fetchone()["c"]
        if total == 0:
            await msg.answer(t(user_id, "no_profiles"))
            return
        cur.execute('''
            SELECT * FROM profiles
            WHERE active=1 AND looking_for IS NOT NULL AND language=?
              AND user_id != ?
              AND user_id NOT IN (SELECT blocked_id FROM blacklist WHERE user_id=?)
            ORDER BY id DESC LIMIT 8
        ''', (lang, user_id, user_id))
        rows = cur.fetchall()
    for r in rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать", url=f"tg://user?id={r['user_id']}")],
            [
                InlineKeyboardButton(text="⭐", callback_data=f"fav_{r['user_id']}"),
                InlineKeyboardButton(text="🚫", callback_data=f"block_{r['user_id']}"),
                InlineKeyboardButton(text="⚠️", callback_data=f"report_{r['user_id']}")
            ]
        ])
        await msg.answer(format_profile(r), reply_markup=kb, parse_mode="HTML")
        await asyncio.sleep(0.08)
    await msg.answer(t(user_id, "shown").format(len(rows), total))

# ================== SWIPE ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_swipe"], TEXTS["en"]["m_swipe"]]))
async def swipe(msg: types.Message):
    user_id = msg.from_user.id
    update_last_active(user_id)
    if not check_rate_limit(user_id):
        await msg.answer(t(user_id, "wait"))
        return
    if get_daily_swipes(user_id) >= DAILY_SWIPE_LIMIT:
        await msg.answer(t(user_id, "swipe_limit"))
        return
    lang = get_lang(user_id)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT p.* FROM profiles p
            JOIN swipes s ON s.user_id = p.user_id
            WHERE s.target_id=? AND s.action='like' AND p.active=1 AND p.language=?
              AND p.user_id != ?
              AND p.user_id NOT IN (SELECT target_id FROM swipes WHERE user_id=?)
              AND p.user_id NOT IN (SELECT blocked_id FROM blacklist WHERE user_id=?)
            ORDER BY RANDOM() LIMIT 1
        ''', (user_id, lang, user_id, user_id, user_id))
        r = cur.fetchone()
        if not r:
            cur.execute('''
                SELECT * FROM profiles
                WHERE active=1 AND language=? AND looking_for IS NOT NULL
                  AND user_id != ?
                  AND user_id NOT IN (SELECT target_id FROM swipes WHERE user_id=?)
                  AND user_id NOT IN (SELECT blocked_id FROM blacklist WHERE user_id=?)
                ORDER BY RANDOM() LIMIT 1
            ''', (lang, user_id, user_id, user_id))
            r = cur.fetchone()
    if not r:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM swipes WHERE user_id=?", (user_id,))
            conn.commit()
        await msg.answer(t(user_id, "swipe_restart"))
        return await swipe(msg)

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❤️", callback_data=f"swipe_like_{r['user_id']}"),
        InlineKeyboardButton(text="⛔", callback_data=f"swipe_dislike_{r['user_id']}")
    ]])
    await msg.answer(format_profile(r), reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.startswith("swipe_"))
async def swipe_cb(call: types.CallbackQuery):
    user_id = call.from_user.id
    parts = call.data.split("_")
    if len(parts) < 3:
        await call.answer()
        return
    action = parts[1]
    try:
        target = int(parts[2])
    except:
        await call.answer()
        return

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO swipes (user_id, target_id, action, date) VALUES (?,?,?,?)",
            (user_id, target, action, datetime.now().isoformat())
        )
        conn.commit()
        if action == "like":
            cur.execute(
                "SELECT 1 FROM swipes WHERE user_id=? AND target_id=? AND action='like'",
                (target, user_id)
            )
            if cur.fetchone():
                u1, u2 = min(user_id, target), max(user_id, target)
                cur.execute(
                    "INSERT OR IGNORE INTO matches (user1_id, user2_id, date) VALUES (?,?,?)",
                    (u1, u2, datetime.now().isoformat())
                )
                conn.commit()
                cur.execute("SELECT username FROM profiles WHERE user_id=?", (target,))
                other = cur.fetchone()
                name = html.escape(other["username"] if other else "Unknown")
                await call.message.answer(t(user_id, "mutual").format(name), parse_mode="HTML")
                try:
                    cur.execute("SELECT username FROM profiles WHERE user_id=?", (user_id,))
                    me = cur.fetchone()
                    myname = html.escape(me["username"] if me else "Unknown")
                    await bot.send_message(target, t(target, "mutual").format(myname), parse_mode="HTML")
                except:
                    pass
    await call.answer()
    try:
        await call.message.delete()
    except:
        pass

# ================== MATCHES / FAV / BLOCK / REPORT ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_matches"], TEXTS["en"]["m_matches"]]))
async def matches(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT CASE WHEN user1_id=? THEN user2_id ELSE user1_id END as pid
            FROM matches WHERE user1_id=? OR user2_id=?
            ORDER BY date DESC LIMIT 15
        ''', (user_id, user_id, user_id))
        rows = cur.fetchall()
    if not rows:
        await msg.answer("Мэтчей пока нет")
        return
    for row in rows:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM profiles WHERE user_id=?", (row["pid"],))
            p = cur.fetchone()
        if p and p["active"]:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬", url=f"tg://user?id={p['user_id']}")]
            ])
            await msg.answer(format_profile(p), reply_markup=kb, parse_mode="HTML")
            await asyncio.sleep(0.08)

@dp.callback_query(F.data.startswith("fav_"))
async def fav_cb(call: types.CallbackQuery):
    uid = call.from_user.id
    try:
        tid = int(call.data.split("_")[1])
    except:
        await call.answer()
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM favorites WHERE user_id=? AND favorite_id=?", (uid, tid))
        if cur.fetchone():
            cur.execute("DELETE FROM favorites WHERE user_id=? AND favorite_id=?", (uid, tid))
            await call.answer("Убрано")
        else:
            cur.execute(
                "INSERT OR IGNORE INTO favorites (user_id, favorite_id, date) VALUES (?,?,?)",
                (uid, tid, datetime.now().isoformat())
            )
            await call.answer("Добавлено")
        conn.commit()

@dp.callback_query(F.data.startswith("block_"))
async def block_cb(call: types.CallbackQuery):
    try:
        tid = int(call.data.split("_")[1])
    except:
        await call.answer()
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO blacklist (user_id, blocked_id, date) VALUES (?,?,?)",
            (call.from_user.id, tid, datetime.now().isoformat())
        )
        conn.commit()
    await call.answer("Заблокирован")

@dp.message(F.text.in_([TEXTS["ru"]["m_fav"], TEXTS["en"]["m_fav"]]))
async def show_fav(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT p.* FROM favorites f
            JOIN profiles p ON f.favorite_id = p.user_id
            WHERE f.user_id=? AND p.active=1
        ''', (user_id,))
        rows = cur.fetchall()
    if not rows:
        await msg.answer(t(user_id, "fav_empty"))
        return
    for r in rows:
        await msg.answer(format_profile(r), parse_mode="HTML")
        await asyncio.sleep(0.08)

@dp.callback_query(F.data.startswith("report_"))
async def report_start(call: types.CallbackQuery):
    uid = call.from_user.id
    if get_daily_reports(uid) >= REPORT_LIMIT_PER_DAY:
        await call.answer(t(uid, "report_limit"), show_alert=True)
        return
    try:
        tid = int(call.data.split("_")[1])
    except:
        await call.answer()
        return
    report_data[uid] = {"target": tid}
    await call.message.answer(t(uid, "report_ask"))
    await call.answer()

@dp.message(lambda m: m.from_user.id in report_data and user_data.get(m.from_user.id, {}).get("step") is None)
async def report_reason(msg: types.Message):
    uid = msg.from_user.id
    if uid not in report_data:
        return
    if get_daily_reports(uid) >= REPORT_LIMIT_PER_DAY:
        await msg.answer(t(uid, "report_limit"))
        report_data.pop(uid, None)
        return
    target = report_data[uid]["target"]
    reason = (msg.text or "")[:300]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO reports (reporter_id, reported_id, reason, date) VALUES (?,?,?,?)",
            (uid, target, reason, datetime.now().isoformat())
        )
        conn.commit()
    await msg.answer(t(uid, "report_sent"))
    report_data.pop(uid, None)
    for admin in ADMIN_IDS:
        try:
            await bot.send_message(
                admin,
                f"⚠️ Жалоба\nОт: <code>{uid}</code>\nНа: <code>{target}</code>\n{html.escape(reason)}",
                parse_mode="HTML"
            )
        except:
            pass

# ================== CHECK / WEB / STATS ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_check"], TEXTS["en"]["m_check"]]))
@dp.message(Command("stats"))
async def check_player(msg: types.Message):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer(
            "Пример:\n<code>/stats 76561199180387602</code>\nили ссылка на профиль",
            parse_mode="HTML"
        )
        return
    status = await msg.answer("⏳ Ищу...")
    steamid = await resolve_steamid(args[1])
    if not steamid:
        await status.edit_text("❌ Не распознал SteamID")
        return
    stats = await get_rust_stats(steamid)
    hours = f"{stats['hours']} ч" if stats["hours"] is not None else "скрыто"
    kills = stats["kills"] if stats["kills"] is not None else "—"
    deaths = stats["deaths"] if stats["deaths"] is not None else "—"
    kd = stats["kd"] if stats["kd"] is not None else "—"
    name = html.escape(stats["name"])
    text = (
        f"👤 <b>{name}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⏱ Часы: <b>{hours}</b>\n"
        f"⚔️ Убийств: <b>{kills}</b>\n"
        f"💀 Смертей: <b>{deaths}</b>\n"
        f"📊 K/D: <b>{kd}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<a href='https://steamcommunity.com/profiles/{steamid}'>Steam</a> • "
        f"<a href='https://rustbans.ru/rust-player-stats?steamid={steamid}'>rustbans</a>"
    )
    await status.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)

@dp.message(F.text.in_([TEXTS["ru"]["m_web"], TEXTS["en"]["m_web"]]))
async def web_app(msg: types.Message):
    await msg.answer(t(msg.from_user.id, "rustylub"), parse_mode="HTML", disable_web_page_preview=False)

@dp.message(F.text.in_([TEXTS["ru"]["m_stats"], TEXTS["en"]["m_stats"]]))
async def bot_stats_user(msg: types.Message):
    lang = get_lang(msg.from_user.id)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as c FROM profiles WHERE active=1 AND looking_for IS NOT NULL AND language=?",
            (lang,)
        )
        count = cur.fetchone()["c"]
    await msg.answer(f"📊 Активных анкет: <b>{count}</b>", parse_mode="HTML")

@dp.message(F.text.in_([TEXTS["ru"]["m_new"], TEXTS["en"]["m_new"]]))
async def whats_new(msg: types.Message):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT text, date FROM updates ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()
    if not rows:
        await msg.answer("Пока нет обновлений")
        return
    text = "🆕 <b>Обновления</b>\n\n"
    for r in rows:
        text += f"• {str(r['date'])[:10]}\n{html.escape(r['text'])}\n\n"
    await msg.answer(text, parse_mode="HTML")

@dp.message(F.text.in_([TEXTS["ru"]["m_lang"], TEXTS["en"]["m_lang"]]))
async def change_lang(msg: types.Message):
    await msg.answer(t(msg.from_user.id, "choose_lang"), reply_markup=lang_keyboard())

@dp.message(F.text.in_([TEXTS["ru"]["m_country"], TEXTS["en"]["m_country"]]))
async def change_country(msg: types.Message):
    await msg.answer(t(msg.from_user.id, "choose_country"), reply_markup=country_keyboard())
    user_data[msg.from_user.id] = {"step": "choose_country"}

# ================== ADMIN ==================
@dp.message(Command("admin"))
async def admin_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    s = get_bot_stats()
    text = (
        "🛠 <b>Админ-панель</b>\n"
        "━━━━━━━━━━━━━━━━\n"
        f"👥 Юзеров: <b>{s['users']}</b>\n"
        f"📋 Анкет: <b>{s['profiles']}</b>\n"
        f"🇷🇺 {s['ru']} | 🇬🇧 {s['en']}\n"
        f"💞 Мэтчей: <b>{s['matches']}</b>\n"
        f"💕 Свайпов: <b>{s['swipes']}</b>\n"
        f"🚫 Банов: <b>{s['bans']}</b>\n"
        f"⚠️ Жалоб: <b>{s['reports_open']}</b>\n"
        f"📢 Реклам: <b>{s['ads']}</b>\n"
        f"🆕 За 24ч: <b>{s['new_24h']}</b>\n"
        f"🟢 Активны 24ч: <b>{s['active_24h']}</b>\n"
        "━━━━━━━━━━━━━━━━\n"
        "/user ID\n/profile ID\n/ban ID причина\n/unban ID\n/bans\n"
        "/deactivate ID\n/activate ID\n/clear_swipes ID\n"
        "/reports\n/update текст\n/add_ad текст\n/list_ads\n/del_ad ID\n"
        "/last 20\n/logs\n/say ID текст\n/stats_full"
    )
    await msg.answer(text, parse_mode="HTML")

@dp.message(Command("stats_full"))
async def stats_full(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    s = get_bot_stats()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT country, COUNT(*) as c FROM profiles WHERE country IS NOT NULL GROUP BY country ORDER BY c DESC LIMIT 10"
        )
        countries = cur.fetchall()
        cur.execute(
            "SELECT looking_for, COUNT(*) as c FROM profiles WHERE looking_for IS NOT NULL GROUP BY looking_for ORDER BY c DESC"
        )
        looking = cur.fetchall()
    text = f"📊 <b>Полная статистика</b>\n\nЮзеры: {s['users']}\nАнкеты: {s['profiles']}\nМэтчи: {s['matches']}\n\n<b>Страны:</b>\n"
    for c in countries:
        text += f"• {html.escape(str(c['country']))}: {c['c']}\n"
    text += "\n<b>Цели:</b>\n"
    for l in looking:
        text += f"• {html.escape(str(l['looking_for']))}: {l['c']}\n"
    await msg.answer(text, parse_mode="HTML")

@dp.message(Command("user"))
async def admin_user(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        uid = int(msg.text.split()[1])
    except:
        await msg.answer("/user user_id")
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM profiles WHERE user_id=?", (uid,))
        p = cur.fetchone()
        cur.execute("SELECT reason, date FROM bans WHERE user_id=?", (uid,))
        ban = cur.fetchone()
        cur.execute("SELECT COUNT(*) as c FROM swipes WHERE user_id=?", (uid,))
        sw = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM matches WHERE user1_id=? OR user2_id=?", (uid, uid))
        mt = cur.fetchone()["c"]
    if not p:
        await msg.answer("Не найден")
        return
    text = (
        f"👤 <b>{uid}</b>\n"
        f"@{html.escape(p['username'] or '—')}\n"
        f"Lang: {p['language']} | Country: {html.escape(p['country'] or '—')}\n"
        f"Active: {p['active']}\n"
        f"Looking: {html.escape(p['looking_for'] or '—')}\n"
        f"Created: {str(p['date'])[:19]}\n"
        f"Last: {str(p['last_active'])[:19]}\n"
        f"Swipes: {sw} | Matches: {mt}\n"
    )
    if ban:
        text += f"🚫 {html.escape(ban['reason'])} ({str(ban['date'])[:19]})"
    await msg.answer(text, parse_mode="HTML")
    admin_log(msg.from_user.id, "user_info", str(uid))

@dp.message(Command("profile"))
async def admin_profile(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        uid = int(msg.text.split()[1])
    except:
        await msg.answer("/profile user_id")
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM profiles WHERE user_id=?", (uid,))
        r = cur.fetchone()
    if not r or not r["looking_for"]:
        await msg.answer("Анкеты нет")
        return
    await msg.answer(format_profile(r), parse_mode="HTML")

@dp.message(Command("deactivate"))
async def admin_deactivate(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        uid = int(msg.text.split()[1])
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE profiles SET active=0 WHERE user_id=?", (uid,))
            conn.commit()
        admin_log(msg.from_user.id, "deactivate", str(uid))
        await msg.answer(f"Деактивирован {uid}")
    except:
        await msg.answer("/deactivate user_id")

@dp.message(Command("activate"))
async def admin_activate(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        uid = int(msg.text.split()[1])
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE profiles SET active=1 WHERE user_id=?", (uid,))
            conn.commit()
        admin_log(msg.from_user.id, "activate", str(uid))
        await msg.answer(f"Активирован {uid}")
    except:
        await msg.answer("/activate user_id")

@dp.message(Command("clear_swipes"))
async def admin_clear_swipes(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        uid = int(msg.text.split()[1])
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM swipes WHERE user_id=?", (uid,))
            conn.commit()
        admin_log(msg.from_user.id, "clear_swipes", str(uid))
        await msg.answer(f"Свайпы {uid} очищены")
    except:
        await msg.answer("/clear_swipes user_id")

@dp.message(Command("bans"))
async def admin_bans(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, reason, date FROM bans ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
    if not rows:
        await msg.answer("Банов нет")
        return
    text = "🚫 <b>Баны</b>\n\n"
    for r in rows:
        text += f"• <code>{r['user_id']}</code> — {html.escape(r['reason'] or '')}\n"
    await msg.answer(text, parse_mode="HTML")

@dp.message(Command("last"))
async def admin_last(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    limit = 15
    try:
        limit = min(int(msg.text.split()[1]), 50)
    except:
        pass
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, username, date, language FROM profiles ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()
    text = f"🆕 Последние {len(rows)}:\n\n"
    for r in rows:
        text += f"• <code>{r['user_id']}</code> @{html.escape(r['username'] or '—')} [{r['language']}]\n"
    await msg.answer(text, parse_mode="HTML")

@dp.message(Command("logs"))
async def admin_logs_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM admin_logs ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
    if not rows:
        await msg.answer("Логов нет")
        return
    text = "📜 <b>Логи</b>\n\n"
    for r in rows:
        text += f"• {str(r['date'])[:16]} | {r['admin_id']} | {r['action']} | {html.escape(r['details'] or '')}\n"
    await msg.answer(text, parse_mode="HTML")

@dp.message(Command("say"))
async def admin_say(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    args = msg.text.split(maxsplit=2)
    if len(args) < 3:
        await msg.answer("/say user_id текст")
        return
    try:
        uid = int(args[1])
        text = args[2][:2000]
        await bot.send_message(uid, f"📩 Сообщение от администрации:\n\n{text}")
        admin_log(msg.from_user.id, "say", f"{uid}: {text[:80]}")
        await msg.answer("✅ Отправлено")
    except Exception as e:
        await msg.answer(f"Ошибка: {e}")

@dp.message(Command("ban"))
async def ban_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    args = msg.text.split(maxsplit=2)
    if len(args) < 3:
        await msg.answer("/ban user_id причина")
        return
    try:
        target = int(args[1])
    except:
        await msg.answer("Неверный ID")
        return
    reason = args[2][:200]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO bans (user_id, reason, banned_by, date) VALUES (?,?,?,?)",
            (target, reason, msg.from_user.id, datetime.now().isoformat())
        )
        cur.execute("UPDATE profiles SET active=0 WHERE user_id=?", (target,))
        conn.commit()
    admin_log(msg.from_user.id, "ban", f"{target}: {reason}")
    await msg.answer(f"🚫 Забанен {target}")
    try:
        await bot.send_message(target, f"🚫 Вы забанены.\nПричина: {reason}")
    except:
        pass

@dp.message(Command("unban"))
async def unban_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        target = int(msg.text.split()[1])
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM bans WHERE user_id=?", (target,))
            conn.commit()
        admin_log(msg.from_user.id, "unban", str(target))
        await msg.answer(f"✅ Разбанен {target}")
    except:
        await msg.answer("/unban user_id")

@dp.message(Command("update"))
async def update_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer("/update Текст")
        return
    text = args[1].strip()
    if len(text) > 1500:
        await msg.answer("Макс. 1500 символов")
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO updates (text, date, sent_by) VALUES (?,?,?)",
            (text, datetime.now().isoformat(), msg.from_user.id)
        )
        cur.execute("SELECT user_id, language FROM profiles")
        users = cur.fetchall()
        conn.commit()
    await msg.answer(f"Начинаю рассылку ({len(users)} чел.)...")
    ok = fail = 0
    for u in users:
        if u["user_id"] in ADMIN_IDS:
            continue
        try:
            lang = u["language"] if u["language"] in ("ru", "en") else "ru"
            txt = f"🆕 <b>Обновление</b>\n\n{text}" if lang == "ru" else f"🆕 <b>Update</b>\n\n{text}"
            await bot.send_message(u["user_id"], txt, parse_mode="HTML")
            ok += 1
            await asyncio.sleep(0.05)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            try:
                await bot.send_message(u["user_id"], txt, parse_mode="HTML")
                ok += 1
            except:
                fail += 1
        except:
            fail += 1
    admin_log(msg.from_user.id, "update", f"ok={ok} fail={fail}")
    await msg.answer(f"✅ {ok} | ❌ {fail}")

@dp.message(Command("add_ad"))
async def add_ad(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer("/add_ad Текст рекламы")
        return
    text = args[1].strip()
    if len(text) > 500:
        await msg.answer("Макс. 500 символов")
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO ads (text, date, created_by) VALUES (?,?,?)",
            (text, datetime.now().isoformat(), msg.from_user.id)
        )
        conn.commit()
    admin_log(msg.from_user.id, "add_ad", text[:80])
    await msg.answer("✅ Реклама добавлена")

@dp.message(Command("list_ads"))
async def list_ads(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, text, active FROM ads ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
    if not rows:
        await msg.answer("Реклам нет")
        return
    text = "📢 Рекламы:\n\n"
    for r in rows:
        st = "✅" if r["active"] else "❌"
        text += f"{st} #{r['id']}: {html.escape(r['text'][:70])}\n"
    await msg.answer(text, parse_mode="HTML")

@dp.message(Command("del_ad"))
async def del_ad(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        ad_id = int(msg.text.split()[1])
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE ads SET active=0 WHERE id=?", (ad_id,))
            conn.commit()
        admin_log(msg.from_user.id, "del_ad", str(ad_id))
        await msg.answer(f"✅ Реклама #{ad_id} отключена")
    except:
        await msg.answer("/del_ad id")

@dp.message(Command("reports"))
async def reports_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reports WHERE resolved=0 ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()
    if not rows:
        await msg.answer("Жалоб нет")
        return
    for r in rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚫 Бан", callback_data=f"aban_{r['reported_id']}_{r['id']}"),
            InlineKeyboardButton(text="✅ Ок", callback_data=f"arej_{r['id']}")
        ]])
        await msg.answer(
            f"⚠️ #{r['id']}\nОт: <code>{r['reporter_id']}</code>\nНа: <code>{r['reported_id']}</code>\n{html.escape(r['reason'] or '')}",
            reply_markup=kb,
            parse_mode="HTML"
        )

@dp.callback_query(F.data.startswith("aban_"))
async def aban(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    try:
        target, rid = int(parts[1]), int(parts[2])
    except:
        await call.answer()
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO bans (user_id, reason, banned_by, date) VALUES (?,?,?,?)",
            (target, "Жалоба", call.from_user.id, datetime.now().isoformat())
        )
        cur.execute("UPDATE profiles SET active=0 WHERE user_id=?", (target,))
        cur.execute("UPDATE reports SET resolved=1 WHERE id=?", (rid,))
        conn.commit()
    admin_log(call.from_user.id, "ban_from_report", str(target))
    await call.message.edit_text(f"Забанен {target}")
    await call.answer()

@dp.callback_query(F.data.startswith("arej_"))
async def arej(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        rid = int(call.data.split("_")[1])
    except:
        await call.answer()
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE reports SET resolved=1 WHERE id=?", (rid,))
        conn.commit()
    await call.message.edit_text("Отклонено")
    await call.answer()

# ================== MAIN ==================
async def main():
    cleanup_old_data()
    print("🤖 Rust LFG Bot v14.0 запущен")
    print(f"📁 DB: {DB_PATH}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
