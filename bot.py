# ===== RUST LFG BOT v11.0 (Full) =====
import os
import asyncio
import sqlite3
import random
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

TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН"
raw_owner = os.getenv("OWNER_ID") or "6276697402"
ADMIN_IDS = [int(x.strip()) for x in raw_owner.split(",") if x.strip().isdigit()]
if not ADMIN_IDS:
    ADMIN_IDS = [6276697402]

if not TOKEN or TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН":
    raise ValueError("❌ Укажи токен бота!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

last_message_time = {}
RATE_LIMIT_SECONDS = 2
DAILY_SWIPE_LIMIT = 45

# ================== TEXTS ==================
TEXTS = {
    "ru": {
        "start": "🦀 <b>Rust LFG Bot</b>\n━━━━━━━━━━━━━━━━\n\nБыстро находи тиммейтов, клан или набирай людей.\n\nВыбери действие:",
        "choose_lang": "🌐 Выбери язык интерфейса:",
        "choose_country": "🌍 Выбери свою страну / регион:",
        "lang_set": "✅ Язык сохранён",
        "country_set": "✅ Страна сохранена",
        "cancel": "✅ Отменено",
        "already_has": "У тебя уже есть активная анкета. Сначала удали её.",
        "no_profile": "У тебя пока нет анкеты.",
        "wait": "⏳ Подожди немного",
        "no_profiles": "Пока нет активных анкет на твоём языке.",
        "shown": "Показано {} из {}",
        "fav_empty": "Избранных пока нет",
        "swipe_limit": "Достигнут дневной лимит свайпов. Приходи завтра!",
        "swipe_restart": "Анкеты закончились, начинаю заново",
        "mutual": "💕 <b>Новый мэтч!</b>\n\nУ вас взаимный интерес с @{}",
        "report_ask": "Кратко опиши причину жалобы:",
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
        "m_lang": "🌐 Язык",
        "m_country": "🌍 Страна",
        "m_new": "🆕 Что нового",
    },
    "en": {
        "start": "🦀 <b>Rust LFG Bot</b>\n━━━━━━━━━━━━━━━━\n\nQuickly find teammates, a clan or recruit players.\n\nChoose an action:",
        "choose_lang": "🌐 Choose interface language:",
        "choose_country": "🌍 Choose your country / region:",
        "lang_set": "✅ Language saved",
        "country_set": "✅ Country saved",
        "cancel": "✅ Cancelled",
        "already_has": "You already have an active profile. Delete it first.",
        "no_profile": "You don't have a profile yet.",
        "wait": "⏳ Please wait a moment",
        "no_profiles": "No active profiles in your language yet.",
        "shown": "Shown {} of {}",
        "fav_empty": "No favorites yet",
        "swipe_limit": "Daily swipe limit reached. Come back tomorrow!",
        "swipe_restart": "No more profiles, starting over",
        "mutual": "💕 <b>New match!</b>\n\nYou have mutual interest with @{}",
        "report_ask": "Briefly describe the reason:",
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
                microphone TEXT DEFAULT 'Нет',
                timezone TEXT,
                server TEXT,
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

        # Indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_profiles_active_lang ON profiles(active, language)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_profiles_user ON profiles(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_swipes_user ON swipes(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_swipes_pair ON swipes(user_id, target_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_blacklist ON blacklist(user_id, blocked_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_matches ON matches(user1_id, user2_id)")
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

def is_blocked(user_id: int, target_id: int) -> bool:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM blacklist WHERE user_id = ? AND blocked_id = ?", (user_id, target_id))
        return cur.fetchone() is not None

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
    server = r["server"] or "—"
    contact = "📱 Telegram"
    if r["contact_pref"] == "Discord" and r["discord"]:
        contact = f"🎧 Discord: <code>{r['discord']}</code>"
    elif r["contact_pref"] == "Steam" and r["steam"]:
        contact = f"🎮 Steam: {r['steam']}"

    desc = (r["description"] or "").strip()
    if len(desc) > 230:
        desc = desc[:230] + "..."

    return (
        f"👤 <b>@{username}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎯 {r['looking_for']}\n"
        f"🎂 {r['age']}  •  🎤 {r['microphone']}\n"
        f"🕐 {r['timezone']}  •  🌍 {country}\n"
        f"🖥 {server}\n"
        f"{contact}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"{desc}"
    )

# ================== KEYBOARDS ==================
def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(user_id, "m_create")), KeyboardButton(text=t(user_id, "m_search"))],
            [KeyboardButton(text=t(user_id, "m_my")), KeyboardButton(text=t(user_id, "m_delete"))],
            [KeyboardButton(text=t(user_id, "m_swipe")), KeyboardButton(text=t(user_id, "m_matches"))],
            [KeyboardButton(text=t(user_id, "m_fav")), KeyboardButton(text=t(user_id, "m_stats"))],
            [KeyboardButton(text=t(user_id, "m_lang")), KeyboardButton(text=t(user_id, "m_country"))],
            [KeyboardButton(text=t(user_id, "m_new"))]
        ],
        resize_keyboard=True
    )

def lang_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇬🇧 English")]],
        resize_keyboard=True
    )

def country_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Россия"), KeyboardButton(text="🇺🇦 Украина")],
            [KeyboardButton(text="🇰🇿 Казахстан"), KeyboardButton(text="🇧🇾 Беларусь")],
            [KeyboardButton(text="🇪🇺 Европа"), KeyboardButton(text="🇺🇸 США / Канада")],
            [KeyboardButton(text="🌍 Другая")]
        ],
        resize_keyboard=True
    )

def age_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="16+"), KeyboardButton(text="18+"), KeyboardButton(text="21+")],
            [KeyboardButton(text="25+"), KeyboardButton(text="30+"), KeyboardButton(text="Другой")]
        ],
        resize_keyboard=True
    )

def mic_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎤 Есть микрофон" if get_lang(user_id) == "ru" else "🎤 Have mic")],
            [KeyboardButton(text="🔇 Нет микрофона" if get_lang(user_id) == "ru" else "🔇 No mic")]
        ],
        resize_keyboard=True
    )

def contact_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    if get_lang(user_id) == "ru":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Telegram"), KeyboardButton(text="🎧 Discord")],
                [KeyboardButton(text="🎮 Steam"), KeyboardButton(text="Любой")]
            ],
            resize_keyboard=True
        )
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telegram"), KeyboardButton(text="🎧 Discord")],
            [KeyboardButton(text="🎮 Steam"), KeyboardButton(text="Any")]
        ],
        resize_keyboard=True
    )

def looking_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    if get_lang(user_id) == "ru":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🤝 Ищу тиммейта / дуо / трио")],
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
                    await event.answer(t(user.id, "banned").format(reason))
                else:
                    await event.answer("Banned", show_alert=True)
                return
        return await handler(event, data)

dp.message.middleware(BanCheckMiddleware())
dp.callback_query.middleware(BanCheckMiddleware())

# ================== START + LANG + COUNTRY ==================
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

    lang = row["language"] if row else None
    country = row["country"] if row else None

    if not lang or lang not in ("ru", "en"):
        await msg.answer(TEXTS["ru"]["choose_lang"], reply_markup=lang_keyboard())
        user_data[user_id] = {"step": "choose_lang"}
        return

    if not country:
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

# ================== PROFILE CREATION (simplified clean version) ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_create"], TEXTS["en"]["m_create"]]))
async def create_profile_start(msg: types.Message):
    user_id = msg.from_user.id
    update_last_active(user_id)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM profiles WHERE user_id = ? AND active = 1 AND looking_for IS NOT NULL", (user_id,))
        if cur.fetchone():
            await msg.answer(t(user_id, "already_has"))
            return
    user_data[user_id] = {"step": "age"}
    await msg.answer("🎂 Укажи возраст:" if get_lang(user_id) == "ru" else "🎂 Select age:", reply_markup=age_keyboard())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "age")
async def profile_age(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text.strip()
    if text == "Другой":
        user_data[user_id]["step"] = "age_custom"
        await msg.answer("Напиши возраст цифрами (14-60):", reply_markup=ReplyKeyboardRemove())
        return
    if text not in ["16+", "18+", "21+", "25+", "30+"]:
        await msg.answer("Выбери кнопкой")
        return
    user_data[user_id]["age"] = text
    user_data[user_id]["step"] = "mic"
    await msg.answer("🎤 Микрофон:", reply_markup=mic_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "age_custom")
async def profile_age_custom(msg: types.Message):
    user_id = msg.from_user.id
    if not msg.text.isdigit() or not (14 <= int(msg.text) <= 60):
        await msg.answer("Напиши число от 14 до 60")
        return
    user_data[user_id]["age"] = msg.text
    user_data[user_id]["step"] = "mic"
    await msg.answer("🎤 Микрофон:", reply_markup=mic_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "mic")
async def profile_mic(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text
    user_data[user_id]["mic"] = "Есть" if "Есть" in text or "Have" in text else "Нет"
    user_data[user_id]["step"] = "tz"
    await msg.answer("🕐 Напиши часовой пояс (например МСК+3 / UTC+3):", reply_markup=ReplyKeyboardRemove())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tz")
async def profile_tz(msg: types.Message):
    user_id = msg.from_user.id
    tz = msg.text.strip()
    if len(tz) < 2:
        await msg.answer("Напиши нормальный часовой пояс")
        return
    user_data[user_id]["tz"] = tz
    user_data[user_id]["step"] = "contact_pref"
    await msg.answer("📞 Как с тобой лучше связываться?", reply_markup=contact_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "contact_pref")
async def profile_contact_pref(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text
    if "Discord" in text:
        user_data[user_id]["contact_pref"] = "Discord"
        user_data[user_id]["step"] = "discord"
        await msg.answer("Введи Discord (username или username#1234):", reply_markup=ReplyKeyboardRemove())
    elif "Steam" in text:
        user_data[user_id]["contact_pref"] = "Steam"
        user_data[user_id]["step"] = "steam"
        await msg.answer("Введи ссылку на Steam или ник:", reply_markup=ReplyKeyboardRemove())
    else:
        user_data[user_id]["contact_pref"] = "Telegram"
        user_data[user_id]["discord"] = None
        user_data[user_id]["steam"] = None
        user_data[user_id]["step"] = "looking"
        await msg.answer("🎯 Что ты ищешь?", reply_markup=looking_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "discord")
async def profile_discord(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["discord"] = msg.text.strip()[:50]
    user_data[user_id]["steam"] = None
    user_data[user_id]["step"] = "looking"
    await msg.answer("🎯 Что ты ищешь?", reply_markup=looking_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "steam")
async def profile_steam(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["steam"] = msg.text.strip()[:100]
    user_data[user_id]["discord"] = None
    user_data[user_id]["step"] = "looking"
    await msg.answer("🎯 Что ты ищешь?", reply_markup=looking_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "looking")
async def profile_looking(msg: types.Message):
    user_id = msg.from_user.id
    choice = msg.text
    user_data[user_id]["looking"] = choice
    user_data[user_id]["step"] = "description"
    await msg.answer(
        "📝 Расскажи о себе коротко:\n• Опыт\n• Роль\n• Когда играешь\n• Что важно",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "description")
async def profile_description(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text.strip()
    if len(text) < 10:
        await msg.answer("Слишком коротко (минимум 10 символов)")
        return
    user_data[user_id]["description"] = text[:600]
    await save_profile(msg)

async def save_profile(msg: types.Message):
    user_id = msg.from_user.id
    data = user_data.get(user_id)
    if not data:
        return
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO profiles
                (user_id, username, looking_for, description, age, microphone, timezone,
                 discord, steam, contact_pref, date, language, last_active, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                user_id,
                msg.from_user.username or "Unknown",
                data.get("looking"),
                data.get("description"),
                data.get("age"),
                data.get("mic"),
                data.get("tz"),
                data.get("discord"),
                data.get("steam"),
                data.get("contact_pref", "Telegram"),
                datetime.now().isoformat(),
                get_lang(user_id),
                datetime.now().isoformat()
            ))
            conn.commit()
    except Exception as e:
        await msg.answer(f"Ошибка: {e}")
        user_data.pop(user_id, None)
        return

    await msg.answer("✅ Анкета создана!", reply_markup=main_menu(user_id))
    user_data.pop(user_id, None)

# ================== MY PROFILE / DELETE ==================
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
        [InlineKeyboardButton(text="✅ Да", callback_data="delete_yes"),
         InlineKeyboardButton(text="❌ Нет", callback_data="delete_no")]
    ])
    await msg.answer("Точно удалить анкету?", reply_markup=kb)

@dp.callback_query(F.data.in_(["delete_yes", "delete_no"]))
async def delete_cb(call: types.CallbackQuery):
    if call.data == "delete_yes":
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE profiles SET active = 0 WHERE user_id = ?", (call.from_user.id,))
            conn.commit()
        await call.message.edit_text("✅ Анкета удалена")
    else:
        await call.message.edit_text("Отменено")
    await call.answer()

# ================== SEARCH ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_search"], TEXTS["en"]["m_search"]]))
async def search_players(msg: types.Message):
    user_id = msg.from_user.id
    update_last_active(user_id)
    if not check_rate_limit(user_id):
        await msg.answer(t(user_id, "wait"))
        return

    lang = get_lang(user_id)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM profiles WHERE active = 1 AND looking_for IS NOT NULL AND language = ?", (lang,))
        total = cur.fetchone()["cnt"]
        if total == 0:
            await msg.answer(t(user_id, "no_profiles"))
            return
        cur.execute('''
            SELECT * FROM profiles
            WHERE active = 1 AND looking_for IS NOT NULL AND language = ?
              AND user_id != ?
              AND user_id NOT IN (SELECT blocked_id FROM blacklist WHERE user_id = ?)
            ORDER BY id DESC LIMIT 10
        ''', (lang, user_id, user_id))
        results = cur.fetchall()

    for r in results:
        text = format_profile(r, lang)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать", url=f"tg://user?id={r['user_id']}")],
            [
                InlineKeyboardButton(text="⭐", callback_data=f"fav_{r['user_id']}"),
                InlineKeyboardButton(text="🚫", callback_data=f"block_{r['user_id']}"),
                InlineKeyboardButton(text="⚠️", callback_data=f"report_{r['user_id']}")
            ]
        ])
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")
        await asyncio.sleep(0.12)

    await msg.answer(t(user_id, "shown").format(len(results), total))

# ================== SWIPE ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_swipe"], TEXTS["en"]["m_swipe"]]))
async def swipe_start(msg: types.Message):
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
        # Приоритет тем, кто лайкнул тебя
        cur.execute('''
            SELECT p.* FROM profiles p
            JOIN swipes s ON s.user_id = p.user_id
            WHERE s.target_id = ? AND s.action = 'like'
              AND p.active = 1 AND p.language = ? AND p.looking_for IS NOT NULL
              AND p.user_id != ?
              AND p.user_id NOT IN (SELECT target_id FROM swipes WHERE user_id = ?)
              AND p.user_id NOT IN (SELECT blocked_id FROM blacklist WHERE user_id = ?)
            ORDER BY RANDOM() LIMIT 1
        ''', (user_id, lang, user_id, user_id, user_id))
        r = cur.fetchone()

        if not r:
            cur.execute('''
                SELECT * FROM profiles
                WHERE active = 1 AND language = ? AND looking_for IS NOT NULL
                  AND user_id != ?
                  AND user_id NOT IN (SELECT target_id FROM swipes WHERE user_id = ?)
                  AND user_id NOT IN (SELECT blocked_id FROM blacklist WHERE user_id = ?)
                ORDER BY RANDOM() LIMIT 1
            ''', (lang, user_id, user_id, user_id))
            r = cur.fetchone()

    if not r:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM swipes WHERE user_id = ?", (user_id,))
            conn.commit()
        await msg.answer(t(user_id, "swipe_restart"))
        return await swipe_start(msg)

    text = format_profile(r, lang)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❤️", callback_data=f"swipe_like_{r['user_id']}"),
        InlineKeyboardButton(text="⛔", callback_data=f"swipe_dislike_{r['user_id']}")
    ]])
    await msg.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.startswith("swipe_"))
async def handle_swipe(call: types.CallbackQuery):
    user_id = call.from_user.id
    action = call.data.split("_")[1]
    target_id = int(call.data.split("_")[2])

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO swipes (user_id, target_id, action, date) VALUES (?, ?, ?, ?)",
                    (user_id, target_id, action, datetime.now().isoformat()))
        conn.commit()

        if action == "like":
            cur.execute("SELECT 1 FROM swipes WHERE user_id = ? AND target_id = ? AND action = 'like'",
                        (target_id, user_id))
            if cur.fetchone():
                u1, u2 = min(user_id, target_id), max(user_id, target_id)
                cur.execute("INSERT OR IGNORE INTO matches (user1_id, user2_id, date) VALUES (?, ?, ?)",
                            (u1, u2, datetime.now().isoformat()))
                conn.commit()

                cur.execute("SELECT username FROM profiles WHERE user_id = ?", (target_id,))
                other = cur.fetchone()
                other_name = other["username"] if other else "Unknown"

                await call.message.answer(t(user_id, "mutual").format(other_name), parse_mode="HTML")
                try:
                    cur.execute("SELECT username FROM profiles WHERE user_id = ?", (user_id,))
                    me = cur.fetchone()
                    my_name = me["username"] if me else "Unknown"
                    await bot.send_message(target_id, t(target_id, "mutual").format(my_name), parse_mode="HTML")
                except:
                    pass

    await call.answer()
    try:
        await call.message.delete()
    except:
        pass

# ================== MATCHES ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_matches"], TEXTS["en"]["m_matches"]]))
async def show_matches(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT CASE WHEN user1_id = ? THEN user2_id ELSE user1_id END as partner_id, date
            FROM matches WHERE user1_id = ? OR user2_id = ?
            ORDER BY date DESC LIMIT 20
        ''', (user_id, user_id, user_id))
        rows = cur.fetchall()

    if not rows:
        await msg.answer("Мэтчей пока нет" if get_lang(user_id) == "ru" else "No matches yet")
        return

    for row in rows:
        pid = row["partner_id"]
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM profiles WHERE user_id = ?", (pid,))
            p = cur.fetchone()
        if not p:
            continue
        text = format_profile(p, get_lang(user_id))
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать", url=f"tg://user?id={pid}")]
        ])
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")
        await asyncio.sleep(0.1)

# ================== FAVORITES & BLOCK ==================
@dp.callback_query(F.data.startswith("fav_"))
async def toggle_fav(call: types.CallbackQuery):
    user_id = call.from_user.id
    target = int(call.data.split("_")[1])
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM favorites WHERE user_id = ? AND favorite_id = ?", (user_id, target))
        if cur.fetchone():
            cur.execute("DELETE FROM favorites WHERE user_id = ? AND favorite_id = ?", (user_id, target))
            await call.answer("Убрано")
        else:
            cur.execute("INSERT OR IGNORE INTO favorites (user_id, favorite_id, date) VALUES (?, ?, ?)",
                        (user_id, target, datetime.now().isoformat()))
            await call.answer("Добавлено")
        conn.commit()

@dp.callback_query(F.data.startswith("block_"))
async def block_user(call: types.CallbackQuery):
    user_id = call.from_user.id
    target = int(call.data.split("_")[1])
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO blacklist (user_id, blocked_id, date) VALUES (?, ?, ?)",
                    (user_id, target, datetime.now().isoformat()))
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
            WHERE f.user_id = ? AND p.active = 1
        ''', (user_id,))
        rows = cur.fetchall()
    if not rows:
        await msg.answer(t(user_id, "fav_empty"))
        return
    for r in rows:
        await msg.answer(format_profile(r, get_lang(user_id)), parse_mode="HTML")
        await asyncio.sleep(0.1)

# ================== STATS ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_stats"], TEXTS["en"]["m_stats"]]))
async def stats(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM profiles WHERE active = 1 AND looking_for IS NOT NULL AND language = ?", (lang,))
        count = cur.fetchone()["cnt"]
    await msg.answer(f"📊 Активных анкет: <b>{count}</b>", parse_mode="HTML")

# ================== REPORTS ==================
@dp.callback_query(F.data.startswith("report_"))
async def report_start(call: types.CallbackQuery):
    report_data[call.from_user.id] = {"target": int(call.data.split("_")[1])}
    await call.message.answer(t(call.from_user.id, "report_ask"))
    await call.answer()

@dp.message(lambda m: m.from_user.id in report_data and m.from_user.id not in user_data)
async def report_reason(msg: types.Message):
    user_id = msg.from_user.id
    target = report_data[user_id]["target"]
    reason = msg.text[:300]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO reports (reporter_id, reported_id, reason, date) VALUES (?, ?, ?, ?)",
                    (user_id, target, reason, datetime.now().isoformat()))
        conn.commit()
    await msg.answer(t(user_id, "report_sent"))
    report_data.pop(user_id, None)
    for admin in ADMIN_IDS:
        try:
            await bot.send_message(admin, f"⚠️ Жалоба\nОт: {user_id}\nНа: {target}\n{reason}")
        except:
            pass

# ================== ADMIN ==================
@dp.message(Command("admin"))
async def admin_panel(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM profiles WHERE active = 1 AND looking_for IS NOT NULL")
        profiles = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM reports WHERE resolved = 0")
        reports = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM matches")
        matches = cur.fetchone()["c"]
    await msg.answer(
        f"🛠 <b>Админ-панель</b>\n\n"
        f"Анкет: <b>{profiles}</b>\n"
        f"Открытых жалоб: <b>{reports}</b>\n"
        f"Мэтчей: <b>{matches}</b>\n\n"
        f"/reports — жалобы\n"
        f"/update текст — рассылка",
        parse_mode="HTML"
    )

@dp.message(Command("reports"))
async def admin_reports(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reports WHERE resolved = 0 ORDER BY id DESC LIMIT 15")
        rows = cur.fetchall()
    if not rows:
        await msg.answer("Жалоб нет")
        return
    for r in rows:
        text = f"⚠️ #{r['id']}\nОт: {r['reporter_id']}\nНа: {r['reported_id']}\n{r['reason']}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚫 Бан", callback_data=f"aban_{r['reported_id']}_{r['id']}"),
            InlineKeyboardButton(text="✅ Ок", callback_data=f"arej_{r['id']}")
        ]])
        await msg.answer(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("aban_"))
async def admin_ban(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    target, rid = int(parts[1]), int(parts[2])
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO bans (user_id, reason, banned_by, date) VALUES (?, ?, ?, ?)",
                    (target, "Жалоба", call.from_user.id, datetime.now().isoformat()))
        cur.execute("UPDATE profiles SET active = 0 WHERE user_id = ?", (target,))
        cur.execute("UPDATE reports SET resolved = 1 WHERE id = ?", (rid,))
        conn.commit()
    await call.message.edit_text(f"Забанен {target}")
    await call.answer()

@dp.callback_query(F.data.startswith("arej_"))
async def admin_reject(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rid = int(call.data.split("_")[1])
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE reports SET resolved = 1 WHERE id = ?", (rid,))
        conn.commit()
    await call.message.edit_text("Отклонено")
    await call.answer()

@dp.message(Command("ban"))
async def cmd_ban(msg: types.Message):
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
        cur.execute("INSERT OR REPLACE INTO bans (user_id, reason, banned_by, date) VALUES (?, ?, ?, ?)",
                    (target, reason, msg.from_user.id, datetime.now().isoformat()))
        cur.execute("UPDATE profiles SET active = 0 WHERE user_id = ?", (target,))
        conn.commit()
    await msg.answer(f"Забанен {target}")

@dp.message(Command("unban"))
async def cmd_unban(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        target = int(msg.text.split()[1])
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM bans WHERE user_id = ?", (target,))
            conn.commit()
        await msg.answer(f"Разбанен {target}")
    except:
        await msg.answer("Ошибка")

@dp.message(Command("update"))
async def cmd_update(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer("Использование: /update Текст обновления")
        return
    text = args[1].strip()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO updates (text, date, sent_by) VALUES (?, ?, ?)",
                    (text, datetime.now().isoformat(), msg.from_user.id))
        cur.execute("SELECT user_id, language FROM profiles")
        users = cur.fetchall()
        conn.commit()

    success = failed = 0
    for u in users:
        if u["user_id"] in ADMIN_IDS:
            continue
        lang = u["language"] if u["language"] in ("ru", "en") else "ru"
        msg_text = f"🆕 <b>Обновление бота</b>\n\n{text}" if lang == "ru" else f"🆕 <b>Bot Update</b>\n\n{text}"
        try:
            await bot.send_message(u["user_id"], msg_text, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    await msg.answer(f"✅ Отправлено: {success}\nНе удалось: {failed}")

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
    print("🤖 Rust LFG Bot v11.0 запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
