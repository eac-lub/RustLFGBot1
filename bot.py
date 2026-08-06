# ===== RUST LFG BOT v10.0 (RU/EN + Optimized) =====
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
OWNER_ID = int(os.getenv("OWNER_ID") or "6276697402")

if not TOKEN or TOKEN == "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН":
    raise ValueError("❌ Укажи токен бота!")

ADMIN_IDS = [OWNER_ID]
bot = Bot(token=TOKEN)
dp = Dispatcher()

last_message_time = {}
RATE_LIMIT_SECONDS = 3

# ================== TEXTS ==================
TEXTS = {
    "ru": {
        "start": "🦀 <b>Rust LFG Bot</b>\n\nБыстро находи тиммейтов, клан или набирай людей.\n\nВыбери действие:",
        "choose_lang": "🌐 Выбери язык интерфейса:",
        "lang_set_ru": "✅ Язык: Русский",
        "lang_set_en": "✅ Language: English",
        "cancel": "✅ Отменено",
        "already_has": "У тебя уже есть активная анкета. Сначала удали её.",
        "age": "🎂 Укажи возраст:",
        "age_custom": "Напиши возраст цифрами (14–60):",
        "age_error": "Напиши число от 14 до 60",
        "mic": "🎤 Микрофон:",
        "tz": "🕐 Напиши часовой пояс\nПримеры: <code>МСК+3</code>, <code>UTC+3</code>, <code>Екатеринбург</code>",
        "tz_error": "Напиши часовой пояс нормально",
        "looking": "🎯 Что ты ищешь?",
        "choose_btn": "Выбери кнопкой",
        "created": "✅ <b>Анкета создана!</b>",
        "my_profile": "👤 <b>Твоя анкета</b>",
        "no_profile": "У тебя пока нет анкеты.",
        "delete_q": "Точно удалить анкету?",
        "deleted": "✅ Анкета удалена",
        "cancelled": "Отменено",
        "wait": "⏳ Подожди немного",
        "no_profiles": "Пока нет активных анкет на твоём языке.",
        "shown": "Показано {} из {}",
        "fav_empty": "Избранных пока нет",
        "fav_title": "⭐ <b>Избранное:</b>\n\n",
        "swipe_restart": "Анкеты закончились, начинаю заново",
        "mutual": "💕 Взаимный интерес!\nНапиши: @{}",
        "stats": "📊 Активных анкет: <b>{}</b>",
        "report_ask": "Кратко опиши причину жалобы:",
        "report_sent": "Жалоба отправлена",
        "banned": "🚫 Вы забанены.\nПричина: {}",
        # Меню
        "m_create": "📝 Создать анкету",
        "m_search": "🔍 Искать игроков",
        "m_my": "👤 Моя анкета",
        "m_delete": "🗑 Удалить анкету",
        "m_fav": "⭐ Избранное",
        "m_swipe": "💕 Свайп",
        "m_stats": "📊 Статистика",
        "m_lang": "🌐 Язык",
        # Looking
        "l_team": "🤝 Ищу тиммейта / дуо / трио",
        "l_clan": "🏰 Ищу клан",
        "l_rec": "📢 Набираю игроков в клан",
        "l_cas": "🎯 Просто поиграть",
        "mic_yes": "🎤 Есть микрофон",
        "mic_no": "🔇 Нет микрофона",
        "age_other": "Другой",
    },
    "en": {
        "start": "🦀 <b>Rust LFG Bot</b>\n\nQuickly find teammates, a clan or recruit players.\n\nChoose an action:",
        "choose_lang": "🌐 Choose interface language:",
        "lang_set_ru": "✅ Язык: Русский",
        "lang_set_en": "✅ Language: English",
        "cancel": "✅ Cancelled",
        "already_has": "You already have an active profile. Delete it first.",
        "age": "🎂 Select your age:",
        "age_custom": "Type your age (14–60):",
        "age_error": "Type a number from 14 to 60",
        "mic": "🎤 Microphone:",
        "tz": "🕐 Write your timezone\nExamples: <code>UTC+3</code>, <code>MSK+3</code>, <code>CET</code>",
        "tz_error": "Write a normal timezone",
        "looking": "🎯 What are you looking for?",
        "choose_btn": "Please use the buttons",
        "created": "✅ <b>Profile created!</b>",
        "my_profile": "👤 <b>Your profile</b>",
        "no_profile": "You don't have a profile yet.",
        "delete_q": "Delete your profile?",
        "deleted": "✅ Profile deleted",
        "cancelled": "Cancelled",
        "wait": "⏳ Please wait a moment",
        "no_profiles": "No active profiles in your language yet.",
        "shown": "Shown {} of {}",
        "fav_empty": "No favorites yet",
        "fav_title": "⭐ <b>Favorites:</b>\n\n",
        "swipe_restart": "No more profiles, starting over",
        "mutual": "💕 Mutual interest!\nWrite to: @{}",
        "stats": "📊 Active profiles: <b>{}</b>",
        "report_ask": "Briefly describe the reason:",
        "report_sent": "Report sent",
        "banned": "🚫 You are banned.\nReason: {}",
        # Menu
        "m_create": "📝 Create profile",
        "m_search": "🔍 Search players",
        "m_my": "👤 My profile",
        "m_delete": "🗑 Delete profile",
        "m_fav": "⭐ Favorites",
        "m_swipe": "💕 Swipe",
        "m_stats": "📊 Statistics",
        "m_lang": "🌐 Language",
        # Looking
        "l_team": "🤝 Looking for teammate / duo / trio",
        "l_clan": "🏰 Looking for a clan",
        "l_rec": "📢 Recruiting for my clan",
        "l_cas": "🎯 Just want to play",
        "mic_yes": "🎤 Have microphone",
        "mic_no": "🔇 No microphone",
        "age_other": "Other",
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
                timezone TEXT DEFAULT 'МСК+3',
                date TEXT,
                language TEXT DEFAULT 'ru',
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

        # Индексы
        cur.execute("CREATE INDEX IF NOT EXISTS idx_profiles_active_lang ON profiles(active, language, looking_for)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_profiles_user ON profiles(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_swipes_user ON swipes(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_swipes_pair ON swipes(user_id, target_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_bans_user ON bans(user_id)")

        conn.commit()

def cleanup_old_data():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM swipes WHERE date < datetime('now', '-14 days')")
        conn.commit()

init_db()

# ================== HELPERS ==================
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
    lang = get_lang(user_id)
    return TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))

def is_banned(user_id: int):
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT reason FROM bans WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return row["reason"] if row else None
    except:
        return None

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def check_rate_limit(user_id: int) -> bool:
    now = datetime.now()
    last = last_message_time.get(user_id)
    if last and (now - last).total_seconds() < RATE_LIMIT_SECONDS:
        return False
    last_message_time[user_id] = now
    return True

# ================== KEYBOARDS ==================
def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(user_id, "m_create")), KeyboardButton(text=t(user_id, "m_search"))],
            [KeyboardButton(text=t(user_id, "m_my")), KeyboardButton(text=t(user_id, "m_delete"))],
            [KeyboardButton(text=t(user_id, "m_fav")), KeyboardButton(text=t(user_id, "m_swipe"))],
            [KeyboardButton(text=t(user_id, "m_stats")), KeyboardButton(text=t(user_id, "m_lang"))]
        ],
        resize_keyboard=True
    )

def age_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="16+"), KeyboardButton(text="18+"), KeyboardButton(text="21+")],
            [KeyboardButton(text="25+"), KeyboardButton(text="30+"), KeyboardButton(text=t(user_id, "age_other"))]
        ],
        resize_keyboard=True
    )

def mic_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(user_id, "mic_yes"))],
            [KeyboardButton(text=t(user_id, "mic_no"))]
        ],
        resize_keyboard=True
    )

def looking_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(user_id, "l_team"))],
            [KeyboardButton(text=t(user_id, "l_clan"))],
            [KeyboardButton(text=t(user_id, "l_rec"))],
            [KeyboardButton(text=t(user_id, "l_cas"))]
        ],
        resize_keyboard=True
    )

def lang_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇬🇧 English")]
        ],
        resize_keyboard=True
    )

# ================== STATE ==================
user_data: dict[int, dict] = {}
report_data: dict[int, dict] = {}

# ================== MIDDLEWARE ==================
class BanCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = None
        if isinstance(event, types.Message):
            user = event.from_user
        elif isinstance(event, types.CallbackQuery):
            user = event.from_user
        if user:
            ban_reason = is_banned(user.id)
            if ban_reason:
                if isinstance(event, types.Message):
                    await event.answer(t(user.id, "banned").format(ban_reason))
                else:
                    await event.answer("Banned", show_alert=True)
                return
        return await handler(event, data)

dp.message.middleware(BanCheckMiddleware())
dp.callback_query.middleware(BanCheckMiddleware())

# ================== START + LANGUAGE ==================
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO profiles (user_id, username) VALUES (?, ?)",
                    (user_id, msg.from_user.username or "Unknown"))
        conn.commit()

        cur.execute("SELECT language FROM profiles WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        lang = row["language"] if row else None

    if not lang or lang not in ("ru", "en"):
        await msg.answer(TEXTS["ru"]["choose_lang"], reply_markup=lang_keyboard())
        user_data[user_id] = {"step": "choose_lang"}
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

    user_data.pop(user_id, None)
    text = TEXTS[lang]["lang_set_ru"] if lang == "ru" else TEXTS[lang]["lang_set_en"]
    await msg.answer(text)
    await msg.answer(t(user_id, "start"), reply_markup=main_menu(user_id), parse_mode="HTML")

@dp.message(F.text.in_([TEXTS["ru"]["m_lang"], TEXTS["en"]["m_lang"]]))
async def change_lang(msg: types.Message):
    await msg.answer(t(msg.from_user.id, "choose_lang"), reply_markup=lang_keyboard())
    user_data[msg.from_user.id] = {"step": "choose_lang"}

@dp.message(Command("cancel"))
async def cmd_cancel(msg: types.Message):
    user_data.pop(msg.from_user.id, None)
    report_data.pop(msg.from_user.id, None)
    await msg.answer(t(msg.from_user.id, "cancel"), reply_markup=main_menu(msg.from_user.id))

# ================== PROFILE CREATION ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_create"], TEXTS["en"]["m_create"]]))
async def create_profile_start(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM profiles WHERE user_id = ? AND active = 1 AND looking_for IS NOT NULL", (user_id,))
        if cur.fetchone():
            await msg.answer(t(user_id, "already_has"))
            return
    user_data[user_id] = {"step": "age"}
    await msg.answer(t(user_id, "age"), reply_markup=age_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "age")
async def profile_age(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text.strip()
    other = t(user_id, "age_other")

    if text == other:
        user_data[user_id]["step"] = "age_custom"
        await msg.answer(t(user_id, "age_custom"), reply_markup=ReplyKeyboardRemove())
        return
    if text not in ["16+", "18+", "21+", "25+", "30+"]:
        await msg.answer(t(user_id, "choose_btn"))
        return

    user_data[user_id]["age"] = text
    user_data[user_id]["step"] = "mic"
    await msg.answer(t(user_id, "mic"), reply_markup=mic_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "age_custom")
async def profile_age_custom(msg: types.Message):
    user_id = msg.from_user.id
    age = msg.text.strip()
    if not age.isdigit() or not (14 <= int(age) <= 60):
        await msg.answer(t(user_id, "age_error"))
        return
    user_data[user_id]["age"] = age
    user_data[user_id]["step"] = "mic"
    await msg.answer(t(user_id, "mic"), reply_markup=mic_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "mic")
async def profile_mic(msg: types.Message):
    user_id = msg.from_user.id
    yes = t(user_id, "mic_yes")
    no = t(user_id, "mic_no")
    if msg.text not in [yes, no]:
        await msg.answer(t(user_id, "choose_btn"))
        return
    user_data[user_id]["mic"] = "Есть" if msg.text == yes else "Нет"
    user_data[user_id]["step"] = "tz"
    await msg.answer(t(user_id, "tz"), reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tz")
async def profile_tz(msg: types.Message):
    user_id = msg.from_user.id
    tz = msg.text.strip()
    if len(tz) < 2 or len(tz) > 30:
        await msg.answer(t(user_id, "tz_error"))
        return
    user_data[user_id]["tz"] = tz
    user_data[user_id]["step"] = "looking"
    await msg.answer(t(user_id, "looking"), reply_markup=looking_keyboard(user_id))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "looking")
async def profile_looking(msg: types.Message):
    user_id = msg.from_user.id
    choice = msg.text

    mapping = {
        t(user_id, "l_team"): "teammate",
        t(user_id, "l_clan"): "looking_clan",
        t(user_id, "l_rec"): "recruiting",
        t(user_id, "l_cas"): "casual"
    }

    if choice not in mapping:
        await msg.answer(t(user_id, "choose_btn"))
        return

    user_data[user_id]["looking"] = choice
    path = mapping[choice]

    if path == "teammate":
        user_data[user_id]["step"] = "tm_experience"
        text = "⚔️ <b>Ищешь тиммейта</b>\n\nСколько примерно часов / вайпов у тебя в Rust?" if get_lang(user_id) == "ru" else \
               "⚔️ <b>Looking for teammate</b>\n\nHow many hours / wipes do you have in Rust?"
        await msg.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

    elif path == "looking_clan":
        user_data[user_id]["step"] = "lc_experience"
        text = "🏰 <b>Ищешь клан</b>\n\nСколько примерно часов / вайпов у тебя?" if get_lang(user_id) == "ru" else \
               "🏰 <b>Looking for a clan</b>\n\nHow many hours / wipes do you have?"
        await msg.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

    elif path == "recruiting":
        user_data[user_id]["step"] = "rec_name"
        text = "📢 <b>Набираешь в клан</b>\n\nНапиши название клана:" if get_lang(user_id) == "ru" else \
               "📢 <b>Recruiting for clan</b>\n\nWrite clan name:"
        await msg.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

    elif path == "casual":
        user_data[user_id]["step"] = "cas_level"
        if get_lang(user_id) == "ru":
            kb = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text="Новичок"), KeyboardButton(text="Средний")],
                [KeyboardButton(text="Опытный"), KeyboardButton(text="Очень опытный")]
            ], resize_keyboard=True)
            await msg.answer("🎯 <b>Просто поиграть</b>\n\nКакой у тебя уровень?", reply_markup=kb, parse_mode="HTML")
        else:
            kb = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text="Newbie"), KeyboardButton(text="Average")],
                [KeyboardButton(text="Experienced"), KeyboardButton(text="Very experienced")]
            ], resize_keyboard=True)
            await msg.answer("🎯 <b>Just want to play</b>\n\nWhat is your level?", reply_markup=kb, parse_mode="HTML")

# ===== PATH 1: Teammate =====
@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_experience")
async def tm_experience(msg: types.Message):
    user_id = msg.from_user.id
    if len(msg.text.strip()) < 2:
        await msg.answer("Напиши хотя бы примерно" if get_lang(user_id) == "ru" else "Write at least something")
        return
    user_data[user_id]["experience"] = msg.text.strip()
    user_data[user_id]["step"] = "tm_role"

    if get_lang(user_id) == "ru":
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Builder"), KeyboardButton(text="PvP / Fighter")],
            [KeyboardButton(text="Farmer / Gatherer"), KeyboardButton(text="All-rounder")],
            [KeyboardButton(text="Другое")]
        ], resize_keyboard=True)
        await msg.answer("Какая у тебя основная роль?", reply_markup=kb)
    else:
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Builder"), KeyboardButton(text="PvP / Fighter")],
            [KeyboardButton(text="Farmer / Gatherer"), KeyboardButton(text="All-rounder")],
            [KeyboardButton(text="Other")]
        ], resize_keyboard=True)
        await msg.answer("What is your main role?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_role")
async def tm_role(msg: types.Message):
    user_id = msg.from_user.id
    role = msg.text.strip()
    if role in ["Другое", "Other"]:
        user_data[user_id]["step"] = "tm_role_custom"
        await msg.answer("Напиши свою роль:" if get_lang(user_id) == "ru" else "Write your role:", reply_markup=ReplyKeyboardRemove())
        return
    user_data[user_id]["role"] = role
    user_data[user_id]["step"] = "tm_style"
    await ask_style(msg)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_role_custom")
async def tm_role_custom(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["role"] = msg.text.strip()
    user_data[user_id]["step"] = "tm_style"
    await ask_style(msg)

async def ask_style(msg: types.Message):
    user_id = msg.from_user.id
    if get_lang(user_id) == "ru":
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Агрессивный"), KeyboardButton(text="Спокойный")],
            [KeyboardButton(text="Смешанный")]
        ], resize_keyboard=True)
        await msg.answer("Какой стиль игры?", reply_markup=kb)
    else:
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Aggressive"), KeyboardButton(text="Chill")],
            [KeyboardButton(text="Mixed")]
        ], resize_keyboard=True)
        await msg.answer("What playstyle do you prefer?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_style")
async def tm_style(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["style"] = msg.text.strip()
    user_data[user_id]["step"] = "tm_size"

    if get_lang(user_id) == "ru":
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Дуо"), KeyboardButton(text="Трио")],
            [KeyboardButton(text="4-5 человек"), KeyboardButton(text="Любой размер")]
        ], resize_keyboard=True)
        await msg.answer("В каком составе хочешь играть?", reply_markup=kb)
    else:
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Duo"), KeyboardButton(text="Trio")],
            [KeyboardButton(text="4-5 players"), KeyboardButton(text="Any size")]
        ], resize_keyboard=True)
        await msg.answer("Preferred group size?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_size")
async def tm_size(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["size"] = msg.text.strip()
    user_data[user_id]["step"] = "tm_time"
    text = "Когда обычно играешь?" if get_lang(user_id) == "ru" else "When do you usually play?"
    await msg.answer(text, reply_markup=ReplyKeyboardRemove())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_time")
async def tm_time(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["online"] = msg.text.strip()
    user_data[user_id]["step"] = "tm_extra"
    text = "Есть что добавить? (можно «нет»)" if get_lang(user_id) == "ru" else "Anything to add? (you can write «no»)"
    await msg.answer(text)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_extra")
async def tm_extra(msg: types.Message):
    user_id = msg.from_user.id
    extra = msg.text.strip()
    if extra.lower() in ["нет", "no", "-", ""]:
        extra = "—"
    data = user_data[user_id]
    if get_lang(user_id) == "ru":
        desc = f"Опыт: {data.get('experience')}\nРоль: {data.get('role')}\nСтиль: {data.get('style')}\nСостав: {data.get('size')}\nОнлайн: {data.get('online')}\nДополнительно: {extra}"
    else:
        desc = f"Experience: {data.get('experience')}\nRole: {data.get('role')}\nStyle: {data.get('style')}\nGroup: {data.get('size')}\nOnline: {data.get('online')}\nExtra: {extra}"
    user_data[user_id]["description"] = desc
    await save_profile(msg)

# ===== PATH 2: Looking for clan =====
@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "lc_experience")
async def lc_experience(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["experience"] = msg.text.strip()
    user_data[user_id]["step"] = "lc_role"
    if get_lang(user_id) == "ru":
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Builder"), KeyboardButton(text="PvP")],
            [KeyboardButton(text="Farmer"), KeyboardButton(text="All-rounder")],
            [KeyboardButton(text="Любая роль")]
        ], resize_keyboard=True)
        await msg.answer("Какую роль хочешь в клане?", reply_markup=kb)
    else:
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Builder"), KeyboardButton(text="PvP")],
            [KeyboardButton(text="Farmer"), KeyboardButton(text="All-rounder")],
            [KeyboardButton(text="Any role")]
        ], resize_keyboard=True)
        await msg.answer("What role do you want in a clan?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "lc_role")
async def lc_role(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["role"] = msg.text.strip()
    user_data[user_id]["step"] = "lc_size"
    if get_lang(user_id) == "ru":
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Маленький (до 8)"), KeyboardButton(text="Средний (8-15)")],
            [KeyboardButton(text="Большой (15+)"), KeyboardButton(text="Не важно")]
        ], resize_keyboard=True)
        await msg.answer("Какой размер клана предпочитаешь?", reply_markup=kb)
    else:
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Small (up to 8)"), KeyboardButton(text="Medium (8-15)")],
            [KeyboardButton(text="Large (15+)"), KeyboardButton(text="Doesn't matter")]
        ], resize_keyboard=True)
        await msg.answer("Preferred clan size?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "lc_size")
async def lc_size(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["clan_size"] = msg.text.strip()
    user_data[user_id]["step"] = "lc_server"
    text = "На каком типе серверов хочешь играть?" if get_lang(user_id) == "ru" else "What server type do you prefer?"
    await msg.answer(text, reply_markup=ReplyKeyboardRemove())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "lc_server")
async def lc_server(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["server"] = msg.text.strip()
    user_data[user_id]["step"] = "lc_extra"
    text = "Что ещё важно? (можно «нет»)" if get_lang(user_id) == "ru" else "Anything else important? (you can write «no»)"
    await msg.answer(text)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "lc_extra")
async def lc_extra(msg: types.Message):
    user_id = msg.from_user.id
    extra = msg.text.strip()
    if extra.lower() in ["нет", "no", "-", ""]:
        extra = "—"
    data = user_data[user_id]
    if get_lang(user_id) == "ru":
        desc = f"Опыт: {data.get('experience')}\nЖелаемая роль: {data.get('role')}\nРазмер клана: {data.get('clan_size')}\nСервер: {data.get('server')}\nДополнительно: {extra}"
    else:
        desc = f"Experience: {data.get('experience')}\nDesired role: {data.get('role')}\nClan size: {data.get('clan_size')}\nServer: {data.get('server')}\nExtra: {extra}"
    user_data[user_id]["description"] = desc
    await save_profile(msg)

# ===== PATH 3: Recruiting =====
@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "rec_name")
async def rec_name(msg: types.Message):
    user_id = msg.from_user.id
    if len(msg.text.strip()) < 2:
        await msg.answer("Напиши название" if get_lang(user_id) == "ru" else "Write the name")
        return
    user_data[user_id]["clan_name"] = msg.text.strip()
    user_data[user_id]["step"] = "rec_members"
    text = "Сколько человек сейчас в клане?" if get_lang(user_id) == "ru" else "How many members are in the clan now?"
    await msg.answer(text)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "rec_members")
async def rec_members(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["members"] = msg.text.strip()
    user_data[user_id]["step"] = "rec_server"
    text = "На каком сервере / типе серверов?" if get_lang(user_id) == "ru" else "What server / server type?"
    await msg.answer(text)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "rec_server")
async def rec_server(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["server"] = msg.text.strip()
    user_data[user_id]["step"] = "rec_req"
    text = "Какие требования к игрокам?" if get_lang(user_id) == "ru" else "What are the requirements for players?"
    await msg.answer(text)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "rec_req")
async def rec_req(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["requirements"] = msg.text.strip()
    user_data[user_id]["step"] = "rec_extra"
    text = "Есть что добавить о клане? (можно «нет»)" if get_lang(user_id) == "ru" else "Anything to add about the clan? (you can write «no»)"
    await msg.answer(text)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "rec_extra")
async def rec_extra(msg: types.Message):
    user_id = msg.from_user.id
    extra = msg.text.strip()
    if extra.lower() in ["нет", "no", "-", ""]:
        extra = "—"
    data = user_data[user_id]
    if get_lang(user_id) == "ru":
        desc = f"Клан: {data.get('clan_name')}\nСейчас человек: {data.get('members')}\nСервер: {data.get('server')}\nТребования: {data.get('requirements')}\nДополнительно: {extra}"
    else:
        desc = f"Clan: {data.get('clan_name')}\nMembers now: {data.get('members')}\nServer: {data.get('server')}\nRequirements: {data.get('requirements')}\nExtra: {extra}"
    user_data[user_id]["description"] = desc
    await save_profile(msg)

# ===== PATH 4: Casual =====
@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "cas_level")
async def cas_level(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["level"] = msg.text.strip()
    user_data[user_id]["step"] = "cas_like"
    if get_lang(user_id) == "ru":
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Фарм / строительство"), KeyboardButton(text="PvP")],
            [KeyboardButton(text="Всё подряд"), KeyboardButton(text="Просто почиллить")]
        ], resize_keyboard=True)
        await msg.answer("Что больше нравится делать?", reply_markup=kb)
    else:
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Farming / Building"), KeyboardButton(text="PvP")],
            [KeyboardButton(text="Everything"), KeyboardButton(text="Just chill")]
        ], resize_keyboard=True)
        await msg.answer("What do you enjoy most?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "cas_like")
async def cas_like(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["like"] = msg.text.strip()
    user_data[user_id]["step"] = "cas_time"
    text = "Когда обычно свободен?" if get_lang(user_id) == "ru" else "When are you usually free?"
    await msg.answer(text, reply_markup=ReplyKeyboardRemove())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "cas_time")
async def cas_time(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["online"] = msg.text.strip()
    user_data[user_id]["step"] = "cas_extra"
    text = "Есть что добавить? (можно «нет»)" if get_lang(user_id) == "ru" else "Anything to add? (you can write «no»)"
    await msg.answer(text)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "cas_extra")
async def cas_extra(msg: types.Message):
    user_id = msg.from_user.id
    extra = msg.text.strip()
    if extra.lower() in ["нет", "no", "-", ""]:
        extra = "—"
    data = user_data[user_id]
    if get_lang(user_id) == "ru":
        desc = f"Уровень: {data.get('level')}\nЛюбит: {data.get('like')}\nОнлайн: {data.get('online')}\nДополнительно: {extra}"
    else:
        desc = f"Level: {data.get('level')}\nEnjoys: {data.get('like')}\nOnline: {data.get('online')}\nExtra: {extra}"
    user_data[user_id]["description"] = desc
    await save_profile(msg)

# ================== SAVE ==================
async def save_profile(msg: types.Message):
    user_id = msg.from_user.id
    data = user_data.get(user_id)
    if not data:
        await msg.answer("Ошибка данных" if get_lang(user_id) == "ru" else "Data error")
        return

    lang = get_lang(user_id)
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO profiles
                (user_id, username, looking_for, description, age, microphone, timezone, date, language, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                user_id,
                msg.from_user.username or "Unknown",
                data.get("looking"),
                data.get("description"),
                data.get("age"),
                data.get("mic"),
                data.get("tz"),
                datetime.now().isoformat(),
                lang
            ))
            conn.commit()
    except Exception as e:
        await msg.answer(f"Error: {e}")
        user_data.pop(user_id, None)
        return

    await msg.answer(
        f"{t(user_id, 'created')}\n\n"
        f"🎯 {data.get('looking')}\n"
        f"🎂 {data.get('age')}\n"
        f"🎤 {data.get('mic')}\n"
        f"🕐 {data.get('tz')}\n\n"
        f"📝 {data.get('description')}",
        reply_markup=main_menu(user_id),
        parse_mode="HTML"
    )
    user_data.pop(user_id, None)

# ================== MY PROFILE / DELETE ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_my"], TEXTS["en"]["m_my"]]))
async def my_profile(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT looking_for, description, age, microphone, timezone FROM profiles WHERE user_id = ? AND active = 1", (user_id,))
        r = cur.fetchone()
    if not r or not r["looking_for"]:
        await msg.answer(t(user_id, "no_profile"))
        return
    await msg.answer(
        f"{t(user_id, 'my_profile')}\n\n"
        f"🎯 {r['looking_for']}\n"
        f"🎂 {r['age']} | 🎤 {r['microphone']} | 🕐 {r['timezone']}\n\n"
        f"📝 {r['description']}",
        parse_mode="HTML"
    )

@dp.message(F.text.in_([TEXTS["ru"]["m_delete"], TEXTS["en"]["m_delete"]]))
async def delete_profile_confirm(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да" if get_lang(msg.from_user.id) == "ru" else "✅ Yes", callback_data="delete_yes")],
        [InlineKeyboardButton(text="❌ Нет" if get_lang(msg.from_user.id) == "ru" else "❌ No", callback_data="delete_no")]
    ])
    await msg.answer(t(msg.from_user.id, "delete_q"), reply_markup=kb)

@dp.callback_query(F.data.in_(["delete_yes", "delete_no"]))
async def delete_profile_callback(call: types.CallbackQuery):
    if call.data == "delete_yes":
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE profiles SET active = 0 WHERE user_id = ?", (call.from_user.id,))
            conn.commit()
        await call.message.edit_text(t(call.from_user.id, "deleted"))
    else:
        await call.message.edit_text(t(call.from_user.id, "cancelled"))
    await call.answer()

# ================== SEARCH (filtered by language) ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_search"], TEXTS["en"]["m_search"]]))
async def search_players(msg: types.Message):
    user_id = msg.from_user.id
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
            SELECT user_id, username, looking_for, description, age, microphone, timezone
            FROM profiles
            WHERE active = 1 AND looking_for IS NOT NULL AND language = ?
            ORDER BY id DESC LIMIT 12
        ''', (lang,))
        results = cur.fetchall()

    for r in results:
        text = (
            f"👤 @{r['username'] or 'Unknown'}\n"
            f"🎯 {r['looking_for']}\n"
            f"🎂 {r['age']} | 🎤 {r['microphone']} | 🕐 {r['timezone']}\n\n"
            f"{(r['description'] or '')[:180]}{'...' if len(r['description'] or '') > 180 else ''}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать" if lang == "ru" else "💬 Message", url=f"tg://user?id={r['user_id']}")],
            [
                InlineKeyboardButton(text="⭐", callback_data=f"fav_{r['user_id']}"),
                InlineKeyboardButton(text="⚠️", callback_data=f"report_{r['user_id']}")
            ]
        ])
        await msg.answer(text, reply_markup=kb)
        await asyncio.sleep(0.15)

    await msg.answer(t(user_id, "shown").format(len(results), total))

# ================== FAVORITES ==================
@dp.callback_query(F.data.startswith("fav_"))
async def toggle_favorite(call: types.CallbackQuery):
    user_id = call.from_user.id
    target_id = int(call.data.split("_")[1])
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM favorites WHERE user_id = ? AND favorite_id = ?", (user_id, target_id))
        if cur.fetchone():
            cur.execute("DELETE FROM favorites WHERE user_id = ? AND favorite_id = ?", (user_id, target_id))
            await call.answer("Убрано" if get_lang(user_id) == "ru" else "Removed")
        else:
            cur.execute("INSERT OR IGNORE INTO favorites (user_id, favorite_id, date) VALUES (?, ?, ?)",
                        (user_id, target_id, datetime.now().isoformat()))
            await call.answer("Добавлено" if get_lang(user_id) == "ru" else "Added")
        conn.commit()

@dp.message(F.text.in_([TEXTS["ru"]["m_fav"], TEXTS["en"]["m_fav"]]))
async def show_favorites(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT p.username, p.looking_for, p.age, p.microphone
            FROM favorites f
            JOIN profiles p ON f.favorite_id = p.user_id
            WHERE f.user_id = ? AND p.active = 1
        ''', (user_id,))
        rows = cur.fetchall()
    if not rows:
        await msg.answer(t(user_id, "fav_empty"))
        return
    text = t(user_id, "fav_title")
    for r in rows:
        text += f"@{r['username'] or 'Unknown'}\n{r['looking_for']}\n{r['age']} | {r['microphone']}\n➖\n"
    await msg.answer(text, parse_mode="HTML")

# ================== SWIPE (filtered by language) ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_swipe"], TEXTS["en"]["m_swipe"]]))
async def swipe_start(msg: types.Message):
    user_id = msg.from_user.id
    if not check_rate_limit(user_id):
        await msg.answer(t(user_id, "wait"))
        return

    lang = get_lang(user_id)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT user_id, username, looking_for, age, description, microphone, timezone
            FROM profiles
            WHERE active = 1 AND looking_for IS NOT NULL AND language = ?
              AND user_id != ?
              AND user_id NOT IN (SELECT target_id FROM swipes WHERE user_id = ?)
            ORDER BY id DESC LIMIT 40
        ''', (lang, user_id, user_id))
        results = cur.fetchall()

    if not results:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM swipes WHERE user_id = ?", (user_id,))
            conn.commit()
        await msg.answer(t(user_id, "swipe_restart"))
        return await swipe_start(msg)

    r = random.choice(results)
    text = (
        f"👤 @{r['username'] or 'Unknown'}\n"
        f"🎯 {r['looking_for']}\n"
        f"🎂 {r['age']} | 🎤 {r['microphone']} | 🕐 {r['timezone']}\n\n"
        f"{(r['description'] or '')[:150]}{'...' if len(r['description'] or '') > 150 else ''}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❤️", callback_data=f"swipe_like_{r['user_id']}"),
        InlineKeyboardButton(text="⛔", callback_data=f"swipe_dislike_{r['user_id']}")
    ]])
    await msg.answer(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("swipe_"))
async def handle_swipe(call: types.CallbackQuery):
    user_id = call.from_user.id
    parts = call.data.split("_")
    action = parts[1]
    target_id = int(parts[2])

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO swipes (user_id, target_id, action, date) VALUES (?, ?, ?, ?)",
                    (user_id, target_id, action, datetime.now().isoformat()))
        conn.commit()

        if action == "like":
            cur.execute("SELECT 1 FROM swipes WHERE user_id = ? AND target_id = ? AND action = 'like'", (target_id, user_id))
            if cur.fetchone():
                cur.execute("SELECT username FROM profiles WHERE user_id = ?", (target_id,))
                row = cur.fetchone()
                username = row["username"] if row else "Unknown"
                await call.message.answer(t(user_id, "mutual").format(username))

    await call.answer()
    try:
        await call.message.delete()
    except:
        pass

# ================== STATS ==================
@dp.message(F.text.in_([TEXTS["ru"]["m_stats"], TEXTS["en"]["m_stats"]]))
async def stats(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM profiles WHERE active = 1 AND looking_for IS NOT NULL AND language = ?", (lang,))
        count = cur.fetchone()["cnt"]
    await msg.answer(t(user_id, "stats").format(count), parse_mode="HTML")

# ================== REPORTS ==================
@dp.callback_query(F.data.startswith("report_"))
async def report_start(call: types.CallbackQuery):
    report_data[call.from_user.id] = {"target": int(call.data.split("_")[1])}
    await call.message.answer(t(call.from_user.id, "report_ask"))
    await call.answer()

@dp.message(lambda m: m.from_user.id in report_data and m.from_user.id not in user_data)
async def report_reason(msg: types.Message):
    user_id = msg.from_user.id
    target_id = report_data[user_id]["target"]
    reason = msg.text[:300]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO reports (reporter_id, reported_id, reason, date) VALUES (?, ?, ?, ?)",
                    (user_id, target_id, reason, datetime.now().isoformat()))
        conn.commit()
    await msg.answer(t(user_id, "report_sent"))
    report_data.pop(user_id, None)
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f"⚠️ Report\nFrom: {user_id}\nTo: {target_id}\n{reason}")
        except:
            pass

# ================== ADMIN ==================
@dp.message(Command("ban"))
async def cmd_ban(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    args = msg.text.split(maxsplit=2)
    if len(args) < 3:
        await msg.answer("Usage: /ban user_id reason")
        return
    try:
        target = int(args[1])
        reason = args[2]
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO bans (user_id, reason, banned_by, date) VALUES (?, ?, ?, ?)",
                        (target, reason, msg.from_user.id, datetime.now().isoformat()))
            cur.execute("UPDATE profiles SET active = 0 WHERE user_id = ?", (target,))
            conn.commit()
        await msg.answer(f"Banned {target}")
        try:
            await bot.send_message(target, t(target, "banned").format(reason))
        except:
            pass
    except Exception as e:
        await msg.answer(str(e))

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
        await msg.answer(f"Unbanned {target}")
    except:
        await msg.answer("Error")

# ================== MAIN ==================
async def main():
    cleanup_old_data()
    print("🤖 Rust LFG Bot v10.0 (RU/EN) запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
