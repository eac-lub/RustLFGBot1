# ===== RUST LFG BOT v12.0 (Full + Steam Stats) =====
import os
import re
import asyncio
import sqlite3
import random
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

# ================== CONFIG ==================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_СЮДА_ТОКЕН"
STEAM_API_KEY = os.getenv("STEAM_API_KEY")  # обязательно для /stats
OWNER_ID = 6276697402
ADMIN_IDS = [OWNER_ID]

if not TOKEN or TOKEN == "ВСТАВЬ_СЮДА_ТОКЕН":
    raise ValueError("❌ Укажи BOT_TOKEN в .env")

bot = Bot(token=TOKEN)
dp = Dispatcher()

last_message_time = {}
RATE_LIMIT_SECONDS = 2
DAILY_SWIPE_LIMIT = 45

# ================== TEXTS ==================
TEXTS = {
    "ru": {
        "start": "🦀 <b>Rust LFG Bot</b>\n━━━━━━━━━━━━━━━━\n\nБыстро находи тиммейтов, клан или набирай людей.\n\nВыбери действие:",
        "choose_lang": "🌐 Выбери язык:",
        "choose_country": "🌍 Выбери страну / регион:",
        "lang_set": "✅ Язык сохранён",
        "country_set": "✅ Страна сохранена",
        "cancel": "✅ Отменено",
        "already_has": "У тебя уже есть активная анкета.",
        "no_profile": "У тебя пока нет анкеты.",
        "wait": "⏳ Подожди немного",
        "no_profiles": "Пока нет активных анкет на твоём языке.",
        "shown": "Показано {} из {}",
        "fav_empty": "Избранных пока нет",
        "swipe_limit": "Дневной лимит свайпов достигнут. Приходи завтра!",
        "swipe_restart": "Анкеты закончились, начинаю заново",
        "mutual": "💕 <b>Новый мэтч!</b>\n\nВзаимный интерес с @{}",
        "report_ask": "Опиши причину жалобы:",
        "report_sent": "Жалоба отправлена",
        "banned": "🚫 Вы забанены.\nПричина: {}",
        "m_create": "📝 Создать анкету",
        "m_search": "🔍 Поиск",
        "m_my": "👤 Моя анкета",
        "m_delete": "🗑 Удалить",
        "m_fav": "⭐ Избранное",
        "m_swipe": "💕 Свайп",
        "m_matches": "💞 Мои мэтчи",
        "m_stats": "📊 Статистика",
        "m_check": "🕵️ Проверить игрока",
        "m_lang": "🌐 Язык",
        "m_country": "🌍 Страна",
        "m_new": "🆕 Что нового",
    },
    "en": {
        "start": "🦀 <b>Rust LFG Bot</b>\n━━━━━━━━━━━━━━━━\n\nQuickly find teammates, clan or recruit players.\n\nChoose an action:",
        "choose_lang": "🌐 Choose language:",
        "choose_country": "🌍 Choose country / region:",
        "lang_set": "✅ Language saved",
        "country_set": "✅ Country saved",
        "cancel": "✅ Cancelled",
        "already_has": "You already have an active profile.",
        "no_profile": "You don't have a profile yet.",
        "wait": "⏳ Please wait",
        "no_profiles": "No active profiles in your language.",
        "shown": "Shown {} of {}",
        "fav_empty": "No favorites yet",
        "swipe_limit": "Daily swipe limit reached. Come back tomorrow!",
        "swipe_restart": "No more profiles, starting over",
        "mutual": "💕 <b>New match!</b>\n\nMutual interest with @{}",
        "report_ask": "Describe the reason:",
        "report_sent": "Report sent",
        "banned": "🚫 You are banned.\nReason: {}",
        "m_create": "📝 Create profile",
        "m_search": "🔍 Search",
        "m_my": "👤 My profile",
        "m_delete": "🗑 Delete",
        "m_fav": "⭐ Favorites",
        "m_swipe": "💕 Swipe",
        "m_matches": "💞 My matches",
        "m_stats": "📊 Stats",
        "m_check": "🕵️ Check player",
        "m_lang": "🌐 Language",
        "m_country": "🌍 Country",
        "m_new": "🆕 What's new",
    }
}

# ================== DATABASE ==================
@contextmanager
def get_db():
    conn = sqlite3.connect("rust_clan.db", timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_profiles_lang ON profiles(active, language)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_swipes_user ON swipes(user_id)")
        conn.commit()

def cleanup_old_data():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM swipes WHERE date < datetime('now', '-21 days')")
        cur.execute("""
            UPDATE profiles SET active = 0 
            WHERE active = 1 AND (last_active IS NULL OR last_active < datetime('now', '-45 days'))
        """)
        conn.commit()

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
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE profiles SET last_active = ? WHERE user_id = ?",
                    (datetime.now().isoformat(), user_id))
        conn.commit()

def is_banned(user_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT reason FROM bans WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row["reason"] if row else None

def get_daily_swipes(user_id: int) -> int:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM swipes WHERE user_id = ? AND date >= datetime('now', '-1 day')", (user_id,))
        return cur.fetchone()["cnt"]

def check_rate_limit(user_id: int) -> bool:
    now = datetime.now()
    last = last_message_time.get(user_id)
    if last and (now - last).total_seconds() < RATE_LIMIT_SECONDS:
        return False
    last_message_time[user_id] = now
    return True

def format_profile(r, lang="ru") -> str:
    username = r["username"] or "Unknown"
    country = r["country"] or "—"
    contact = "📱 Telegram"
    if r["contact_pref"] == "Discord" and r["discord"]:
        contact = f"🎧 Discord: <code>{r['discord']}</code>"
    elif r["contact_pref"] == "Steam" and r["steam"]:
        contact = f"🎮 Steam: {r['steam']}"

    desc = (r["description"] or "")[:230]
    if len(r["description"] or "") > 230:
        desc += "..."

    return (
        f"👤 <b>@{username}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎯 {r['looking_for']}\n"
        f"🎂 {r['age']}  •  🎤 {r['microphone']}\n"
        f"🕐 {r['timezone']}  •  🌍 {country}\n"
        f"{contact}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"{desc}"
    )

# ================== STEAM STATS ==================
async def resolve_steamid(text: str) -> str | None:
    text = text.strip()
    if re.fullmatch(r"7656119\d{10}", text):
        return text
    match = re.search(r"profiles/(\d{17})", text)
    if match:
        return match.group(1)
    match = re.search(r"steamcommunity\.com/id/([^/\s]+)", text)
    if match and STEAM_API_KEY:
        vanity = match.group(1)
        url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={vanity}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get("response", {}).get("success") == 1:
                    return data["response"]["steamid"]
    return None

async def get_rust_stats(steamid: str) -> dict:
    result = {"hours": None, "kills": None, "deaths": None, "kd": None, "name": "Unknown"}
    if not STEAM_API_KEY:
        return result

    async with aiohttp.ClientSession() as session:
        # Name
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steamid}"
        async with session.get(url) as resp:
            data = await resp.json()
            players = data.get("response", {}).get("players", [])
            if players:
                result["name"] = players[0].get("personaname", "Unknown")

        # Hours
        url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={STEAM_API_KEY}&steamid={steamid}&include_appinfo=1&appids_filter[0]=252490"
        async with session.get(url) as resp:
            data = await resp.json()
            games = data.get("response", {}).get("games", [])
            if games:
                result["hours"] = round(games[0].get("playtime_forever", 0) / 60, 1)

        # Kills / Deaths
        url = f"https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v2/?key={STEAM_API_KEY}&appid=252490&steamid={steamid}"
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                stats = {s["name"]: s["value"] for s in data.get("playerstats", {}).get("stats", [])}
                result["kills"] = stats.get("kill_player")
                result["deaths"] = stats.get("deaths")
                if result["kills"] is not None and result["deaths"]:
                    result["kd"] = round(result["kills"] / result["deaths"], 2)
                elif result["kills"] is not None:
                    result["kd"] = result["kills"]
    return result

# ================== KEYBOARDS ==================
def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(user_id, "m_create")), KeyboardButton(text=t(user_id, "m_search"))],
            [KeyboardButton(text=t(user_id, "m_my")), KeyboardButton(text=t(user_id, "m_delete"))],
            [KeyboardButton(text=t(user_id, "m_swipe")), KeyboardButton(text=t(user_id, "m_matches"))],
            [KeyboardButton(text=t(user_id, "m_fav")), KeyboardButton(text=t(user_id, "m_check"))],
            [KeyboardButton(text=t(user_id, "m_stats")), KeyboardButton(text=t(user_id, "m_new"))],
            [KeyboardButton(text=t(user_id, "m_lang")), KeyboardButton(text=t(user_id, "m_country"))]
        ],
        resize_keyboard=True
    )

def lang_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇬🇧 English")]], resize_keyboard=True)

def country_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🇷🇺 Россия"), KeyboardButton(text="🇺🇦 Украина")],
        [KeyboardButton(text="🇰🇿 Казахстан"), KeyboardButton(text="🇧🇾 Беларусь")],
        [KeyboardButton(text="🇪🇺 Европа"), KeyboardButton(text="🇺🇸 США / Канада")],
        [KeyboardButton(text="🌍 Другая")]
    ], resize_keyboard=True)

def age_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="16+"), KeyboardButton(text="18+"), KeyboardButton(text="21+")],
        [KeyboardButton(text="25+"), KeyboardButton(text="30+"), KeyboardButton(text="Другой")]
    ], resize_keyboard=True)

def mic_keyboard(user_id):
    ru = get_lang(user_id) == "ru"
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🎤 Есть микрофон" if ru else "🎤 Have mic")],
        [KeyboardButton(text="🔇 Нет микрофона" if ru else "🔇 No mic")]
    ], resize_keyboard=True)

def contact_keyboard(user_id):
    ru = get_lang(user_id) == "ru"
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📱 Telegram"), KeyboardButton(text="🎧 Discord")],
        [KeyboardButton(text="🎮 Steam"), KeyboardButton(text="Любой" if ru else "Any")]
    ], resize_keyboard=True)

def looking_keyboard(user_id):
    ru = get_lang(user_id) == "ru"
    if ru:
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🤝 Ищу тиммейта / дуо / трио")],
            [KeyboardButton(text="🏰 Ищу клан")],
            [KeyboardButton(text="📢 Набираю в клан")],
            [KeyboardButton(text="🎯 Просто поиграть")]
        ], resize_keyboard=True)
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🤝 Looking for teammate")],
        [KeyboardButton(text="🏰 Looking for clan")],
        [KeyboardButton(text="📢 Recruiting")],
        [KeyboardButton(text="🎯 Just play")]
    ], resize_keyboard=True)

# ================== STATE ==================
user_data = {}
report_data = {}

# ================== MIDDLEWARE ==================
class BanCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user:
            reason = is_banned(user.id)
            if reason:
                if isinstance(event, types.Message):
                    await event.answer(t(user.id, "banned").format(reason))
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
        cur.execute("INSERT OR IGNORE INTO profiles (user_id, username) VALUES (?, ?)",
                    (user_id, msg.from_user.username or "Unknown"))
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
    await msg.answer(t(user_id, "start"), reply_markup=main_menu(user_id), parse_mode="HTML")

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
    await msg.answer(t(user_id, "start"), reply_markup=main_menu(user_id), parse_mode="HTML")

@dp.message(Command("cancel"))
async def cmd_cancel(msg: types.Message):
    user_data.pop(msg.from_user.id, None)
    report_data.pop(msg.from_user.id, None)
    await msg.answer(t(msg.from_user.id, "cancel"), reply_markup=main_menu(msg.from_user.id))

# ================== PROFILE CREATION ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_create"], TEXTS["en"]["m_create"]]))
async def create_start(msg: types.Message):
    user_id = msg.from_user.id
    update_last_active(user_id)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM profiles WHERE user_id = ? AND active = 1 AND looking_for IS NOT NULL", (user_id,))
        if cur.fetchone():
            await msg.answer(t(user_id, "already_has"))
            return
    user_data[user_id] = {"step": "age"}
    await msg.answer("🎂 Возраст:" if get_lang(user_id) == "ru" else "🎂 Age:", reply_markup=age_keyboard())

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
async def p_age_custom(msg: types.Message):
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
    user_data[user_id]["mic"] = "Есть" if "Есть" in msg.text or "Have" in msg.text else "Нет"
    user_data[user_id]["step"] = "tz"
    await msg.answer("🕐 Часовой пояс (МСК+3 / UTC+3):", reply_markup=ReplyKeyboardRemove())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tz")
async def p_tz(msg: types.Message):
    user_id = msg.from_user.id
    if len(msg.text.strip()) < 2:
        await msg.answer("Напиши нормально")
        return
    user_data[user_id]["tz"] = msg.text.strip()
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
    user_data[user_id]["looking"] = msg.text
    user_data[user_id]["step"] = "desc"
    await msg.answer("📝 Коротко о себе (опыт, роль, когда играешь):", reply_markup=ReplyKeyboardRemove())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "desc")
async def p_desc(msg: types.Message):
    user_id = msg.from_user.id
    if len(msg.text.strip()) < 8:
        await msg.answer("Слишком коротко")
        return
    user_data[user_id]["description"] = msg.text.strip()[:700]
    data = user_data[user_id]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT OR REPLACE INTO profiles
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
        cur.execute("SELECT * FROM profiles WHERE user_id = ? AND active = 1", (user_id,))
        r = cur.fetchone()
    if not r or not r["looking_for"]:
        await msg.answer(t(user_id, "no_profile"))
        return
    await msg.answer(format_profile(r, get_lang(user_id)), parse_mode="HTML")

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
            cur.execute("UPDATE profiles SET active = 0 WHERE user_id = ?", (call.from_user.id,))
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
        cur.execute("SELECT COUNT(*) as c FROM profiles WHERE active=1 AND looking_for IS NOT NULL AND language=?", (lang,))
        total = cur.fetchone()["c"]
        if total == 0:
            await msg.answer(t(user_id, "no_profiles"))
            return
        cur.execute('''
            SELECT * FROM profiles WHERE active=1 AND looking_for IS NOT NULL AND language=?
            AND user_id != ? AND user_id NOT IN (SELECT blocked_id FROM blacklist WHERE user_id=?)
            ORDER BY id DESC LIMIT 8
        ''', (lang, user_id, user_id))
        rows = cur.fetchall()
    for r in rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать", url=f"tg://user?id={r['user_id']}")],
            [InlineKeyboardButton(text="⭐", callback_data=f"fav_{r['user_id']}"),
             InlineKeyboardButton(text="🚫", callback_data=f"block_{r['user_id']}"),
             InlineKeyboardButton(text="⚠️", callback_data=f"report_{r['user_id']}")]
        ])
        await msg.answer(format_profile(r, lang), reply_markup=kb, parse_mode="HTML")
        await asyncio.sleep(0.1)
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
            AND p.user_id != ? AND p.user_id NOT IN (SELECT target_id FROM swipes WHERE user_id=?)
            AND p.user_id NOT IN (SELECT blocked_id FROM blacklist WHERE user_id=?)
            ORDER BY RANDOM() LIMIT 1
        ''', (user_id, lang, user_id, user_id, user_id))
        r = cur.fetchone()
        if not r:
            cur.execute('''
                SELECT * FROM profiles WHERE active=1 AND language=? AND looking_for IS NOT NULL
                AND user_id != ? AND user_id NOT IN (SELECT target_id FROM swipes WHERE user_id=?)
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
    await msg.answer(format_profile(r, lang), reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.startswith("swipe_"))
async def swipe_cb(call: types.CallbackQuery):
    user_id = call.from_user.id
    action = call.data.split("_")[1]
    target = int(call.data.split("_")[2])
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO swipes (user_id, target_id, action, date) VALUES (?,?,?,?)",
                    (user_id, target, action, datetime.now().isoformat()))
        conn.commit()
        if action == "like":
            cur.execute("SELECT 1 FROM swipes WHERE user_id=? AND target_id=? AND action='like'", (target, user_id))
            if cur.fetchone():
                u1, u2 = min(user_id, target), max(user_id, target)
                cur.execute("INSERT OR IGNORE INTO matches (user1_id, user2_id, date) VALUES (?,?,?)",
                            (u1, u2, datetime.now().isoformat()))
                conn.commit()
                cur.execute("SELECT username FROM profiles WHERE user_id=?", (target,))
                other = cur.fetchone()
                name = other["username"] if other else "Unknown"
                await call.message.answer(t(user_id, "mutual").format(name), parse_mode="HTML")
                try:
                    cur.execute("SELECT username FROM profiles WHERE user_id=?", (user_id,))
                    me = cur.fetchone()
                    myname = me["username"] if me else "Unknown"
                    await bot.send_message(target, t(target, "mutual").format(myname), parse_mode="HTML")
                except:
                    pass
    await call.answer()
    try:
        await call.message.delete()
    except:
        pass

# ================== MATCHES ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_matches"], TEXTS["en"]["m_matches"]]))
async def matches(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT CASE WHEN user1_id=? THEN user2_id ELSE user1_id END as pid
            FROM matches WHERE user1_id=? OR user2_id=? ORDER BY date DESC LIMIT 15
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
        if p:
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Написать", url=f"tg://user?id={p['user_id']}")]])
            await msg.answer(format_profile(p, get_lang(user_id)), reply_markup=kb, parse_mode="HTML")
            await asyncio.sleep(0.08)

# ================== FAV / BLOCK / REPORT ==================
@dp.callback_query(F.data.startswith("fav_"))
async def fav_cb(call: types.CallbackQuery):
    uid, tid = call.from_user.id, int(call.data.split("_")[1])
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM favorites WHERE user_id=? AND favorite_id=?", (uid, tid))
        if cur.fetchone():
            cur.execute("DELETE FROM favorites WHERE user_id=? AND favorite_id=?", (uid, tid))
            await call.answer("Убрано")
        else:
            cur.execute("INSERT OR IGNORE INTO favorites (user_id, favorite_id, date) VALUES (?,?,?)",
                        (uid, tid, datetime.now().isoformat()))
            await call.answer("Добавлено")
        conn.commit()

@dp.callback_query(F.data.startswith("block_"))
async def block_cb(call: types.CallbackQuery):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO blacklist (user_id, blocked_id, date) VALUES (?,?,?)",
                    (call.from_user.id, int(call.data.split("_")[1]), datetime.now().isoformat()))
        conn.commit()
    await call.answer("Заблокирован")

@dp.message(F.text.in_([TEXTS["ru"]["m_fav"], TEXTS["en"]["m_fav"]]))
async def show_fav(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT p.* FROM favorites f JOIN profiles p ON f.favorite_id=p.user_id
            WHERE f.user_id=? AND p.active=1
        ''', (user_id,))
        rows = cur.fetchall()
    if not rows:
        await msg.answer(t(user_id, "fav_empty"))
        return
    for r in rows:
        await msg.answer(format_profile(r, get_lang(user_id)), parse_mode="HTML")
        await asyncio.sleep(0.08)

@dp.callback_query(F.data.startswith("report_"))
async def report_start(call: types.CallbackQuery):
    report_data[call.from_user.id] = {"target": int(call.data.split("_")[1])}
    await call.message.answer(t(call.from_user.id, "report_ask"))
    await call.answer()

@dp.message(lambda m: m.from_user.id in report_data and m.from_user.id not in user_data)
async def report_reason(msg: types.Message):
    uid = msg.from_user.id
    target = report_data[uid]["target"]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO reports (reporter_id, reported_id, reason, date) VALUES (?,?,?,?)",
                    (uid, target, msg.text[:300], datetime.now().isoformat()))
        conn.commit()
    await msg.answer(t(uid, "report_sent"))
    report_data.pop(uid, None)
    for admin in ADMIN_IDS:
        try:
            await bot.send_message(admin, f"⚠️ Жалоба\nОт: {uid}\nНа: {target}\n{msg.text[:200]}")
        except:
            pass

# ================== STEAM CHECK ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_check"], TEXTS["en"]["m_check"]]))
@dp.message(Command("stats"))
async def check_player(msg: types.Message):
    user_id = msg.from_user.id
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer(
            "Отправь SteamID или ссылку:\n"
            "<code>/stats 76561199180387602</code>\n"
            "или просто напиши ссылку после команды",
            parse_mode="HTML"
        )
        return

    status = await msg.answer("⏳ Получаю статистику...")
    steamid = await resolve_steamid(args[1])
    if not steamid:
        await status.edit_text("❌ Не распознал SteamID / ссылку")
        return

    stats = await get_rust_stats(steamid)
    hours = f"{stats['hours']} ч" if stats["hours"] is not None else "скрыто"
    kills = stats["kills"] if stats["kills"] is not None else "—"
    deaths = stats["deaths"] if stats["deaths"] is not None else "—"
    kd = stats["kd"] if stats["kd"] is not None else "—"

    text = (
        f"👤 <b>{stats['name']}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⏱ Часы в Rust: <b>{hours}</b>\n"
        f"⚔️ Убийств: <b>{kills}</b>\n"
        f"💀 Смертей: <b>{deaths}</b>\n"
        f"📊 K/D: <b>{kd}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<a href='https://steamcommunity.com/profiles/{steamid}'>Steam профиль</a> • "
        f"<a href='https://rustbans.ru/rust-player-stats?steamid={steamid}'>rustbans</a>"
    )
    await status.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)

# ================== STATS & UPDATES ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_stats"], TEXTS["en"]["m_stats"]]))
async def bot_stats(msg: types.Message):
    lang = get_lang(msg.from_user.id)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM profiles WHERE active=1 AND looking_for IS NOT NULL AND language=?", (lang,))
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
    text = "🆕 <b>Последние обновления</b>\n\n"
    for r in rows:
        text += f"• {r['date'][:10]}\n{r['text']}\n\n"
    await msg.answer(text, parse_mode="HTML")

# ================== ADMIN ==================
@dp.message(Command("admin"))
async def admin_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM profiles WHERE active=1 AND looking_for IS NOT NULL")
        p = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM reports WHERE resolved=0")
        r = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM matches")
        m = cur.fetchone()["c"]
    await msg.answer(f"🛠 Анкет: {p}\nЖалоб: {r}\nМэтчей: {m}\n\n/reports\n/update текст\n/ban id причина")

@dp.message(Command("update"))
async def update_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer("/update Текст обновления")
        return
    text = args[1]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO updates (text, date, sent_by) VALUES (?,?,?)",
                    (text, datetime.now().isoformat(), msg.from_user.id))
        cur.execute("SELECT user_id, language FROM profiles")
        users = cur.fetchall()
        conn.commit()
    ok = fail = 0
    for u in users:
        if u["user_id"] in ADMIN_IDS:
            continue
        try:
            lang = u["language"] if u["language"] in ("ru", "en") else "ru"
            msg_text = f"🆕 <b>Обновление</b>\n\n{text}" if lang == "ru" else f"🆕 <b>Update</b>\n\n{text}"
            await bot.send_message(u["user_id"], msg_text, parse_mode="HTML")
            ok += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1
    await msg.answer(f"✅ {ok} | ❌ {fail}")

@dp.message(Command("ban"))
async def ban_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    args = msg.text.split(maxsplit=2)
    if len(args) < 3:
        await msg.answer("/ban user_id причина")
        return
    target = int(args[1])
    reason = args[2]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO bans (user_id, reason, banned_by, date) VALUES (?,?,?,?)",
                    (target, reason, msg.from_user.id, datetime.now().isoformat()))
        cur.execute("UPDATE profiles SET active=0 WHERE user_id=?", (target,))
        conn.commit()
    await msg.answer(f"Забанен {target}")

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
        await msg.answer(f"Разбанен {target}")
    except:
        await msg.answer("Ошибка")

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
        await msg.answer(f"⚠️ #{r['id']}\nОт: {r['reporter_id']}\nНа: {r['reported_id']}\n{r['reason']}", reply_markup=kb)

@dp.callback_query(F.data.startswith("aban_"))
async def aban(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    target, rid = int(parts[1]), int(parts[2])
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO bans (user_id, reason, banned_by, date) VALUES (?,?,?,?)",
                    (target, "Жалоба", call.from_user.id, datetime.now().isoformat()))
        cur.execute("UPDATE profiles SET active=0 WHERE user_id=?", (target,))
        cur.execute("UPDATE reports SET resolved=1 WHERE id=?", (rid,))
        conn.commit()
    await call.message.edit_text(f"Забанен {target}")
    await call.answer()

@dp.callback_query(F.data.startswith("arej_"))
async def arej(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rid = int(call.data.split("_")[1])
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE reports SET resolved=1 WHERE id=?", (rid,))
        conn.commit()
    await call.message.edit_text("Отклонено")
    await call.answer()

# ================== LANG / COUNTRY CHANGE ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_lang"], TEXTS["en"]["m_lang"]]))
async def change_lang(msg: types.Message):
    await msg.answer(t(msg.from_user.id, "choose_lang"), reply_markup=lang_keyboard())

@dp.message(F.text.in_([TEXTS["ru"]["m_country"], TEXTS["en"]["m_country"]]))
async def change_country(msg: types.Message):
    await msg.answer(t(msg.from_user.id, "choose_country"), reply_markup=country_keyboard())
    user_data[msg.from_user.id] = {"step": "choose_country"}

# ================== MAIN ==================
async def main():
    cleanup_old_data()
    print("🤖 Rust LFG Bot v12.0 запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
