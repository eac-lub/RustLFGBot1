# ===== RUST LFG BOT v9.1 (Clean for Railway) =====
import os
import asyncio
import sqlite3
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

# ================== DATABASE ==================
@contextmanager
def get_db():
    conn = sqlite3.connect("rust_clan.db")
    conn.row_factory = sqlite3.Row
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
        conn.commit()

init_db()

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
                    await event.answer(f"🚫 Вы забанены.\nПричина: {ban_reason}")
                else:
                    await event.answer("Вы забанены", show_alert=True)
                return
        return await handler(event, data)

dp.message.middleware(BanCheckMiddleware())
dp.callback_query.middleware(BanCheckMiddleware())

# ================== HELPERS ==================
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
def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Создать анкету"), KeyboardButton(text="🔍 Искать игроков")],
            [KeyboardButton(text="👤 Моя анкета"), KeyboardButton(text="🗑 Удалить анкету")],
            [KeyboardButton(text="⭐ Избранное"), KeyboardButton(text="💕 Свайп")],
            [KeyboardButton(text="📊 Статистика")]
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

def mic_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎤 Есть микрофон")],
            [KeyboardButton(text="🔇 Нет микрофона")]
        ],
        resize_keyboard=True
    )

def looking_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🤝 Ищу тиммейта / дуо / трио")],
            [KeyboardButton(text="🏰 Ищу клан")],
            [KeyboardButton(text="📢 Набираю игроков в клан")],
            [KeyboardButton(text="🎯 Просто поиграть / любая компания")]
        ],
        resize_keyboard=True
    )

# ================== STATE ==================
user_data: dict[int, dict] = {}
report_data: dict[int, dict] = {}

# ================== START ==================
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO profiles (user_id, username) VALUES (?, ?)",
            (user_id, msg.from_user.username or "Unknown")
        )
        conn.commit()

    await msg.answer(
        "🦀 <b>Rust LFG Bot</b>\n\n"
        "Здесь можно быстро найти тиммейтов, клан или набрать людей к себе.\n\n"
        "Выбери действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.message(Command("cancel"))
async def cmd_cancel(msg: types.Message):
    user_data.pop(msg.from_user.id, None)
    report_data.pop(msg.from_user.id, None)
    await msg.answer("✅ Отменено", reply_markup=main_menu())

# ================== PROFILE CREATION ==================
@dp.message(F.text == "📝 Создать анкету")
async def create_profile_start(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM profiles WHERE user_id = ? AND active = 1 AND looking_for IS NOT NULL",
            (user_id,)
        )
        if cur.fetchone():
            await msg.answer("У тебя уже есть активная анкета. Сначала удали её.")
            return

    user_data[user_id] = {"step": "age"}
    await msg.answer("🎂 Укажи возраст:", reply_markup=age_keyboard())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "age")
async def profile_age(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text.strip()

    if text == "Другой":
        user_data[user_id]["step"] = "age_custom"
        await msg.answer("Напиши свой возраст цифрами (от 14 до 60):", reply_markup=ReplyKeyboardRemove())
        return

    if text not in ["16+", "18+", "21+", "25+", "30+"]:
        await msg.answer("Выбери кнопкой или нажми «Другой»")
        return

    user_data[user_id]["age"] = text
    user_data[user_id]["step"] = "mic"
    await msg.answer("🎤 Микрофон:", reply_markup=mic_keyboard())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "age_custom")
async def profile_age_custom(msg: types.Message):
    user_id = msg.from_user.id
    age = msg.text.strip()

    if not age.isdigit() or not (14 <= int(age) <= 60):
        await msg.answer("Напиши возраст цифрами от 14 до 60")
        return

    user_data[user_id]["age"] = age
    user_data[user_id]["step"] = "mic"
    await msg.answer("🎤 Микрофон:", reply_markup=mic_keyboard())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "mic")
async def profile_mic(msg: types.Message):
    user_id = msg.from_user.id

    if msg.text not in ["🎤 Есть микрофон", "🔇 Нет микрофона"]:
        await msg.answer("Выбери кнопкой")
        return

    user_data[user_id]["mic"] = "Есть" if "Есть" in msg.text else "Нет"
    user_data[user_id]["step"] = "tz"
    await msg.answer(
        "🕐 Напиши свой часовой пояс\n"
        "Примеры: <code>МСК+3</code>, <code>UTC+3</code>, <code>Екатеринбург</code>, <code>Питер</code>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tz")
async def profile_tz(msg: types.Message):
    user_id = msg.from_user.id
    tz = msg.text.strip()

    if len(tz) < 2 or len(tz) > 30:
        await msg.answer("Напиши часовой пояс нормально (например МСК+3)")
        return

    user_data[user_id]["tz"] = tz
    user_data[user_id]["step"] = "looking"
    await msg.answer("🎯 Что ты ищешь?", reply_markup=looking_keyboard())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "looking")
async def profile_looking(msg: types.Message):
    user_id = msg.from_user.id
    choice = msg.text

    options = {
        "🤝 Ищу тиммейта / дуо / трио": "teammate",
        "🏰 Ищу клан": "looking_clan",
        "📢 Набираю игроков в клан": "recruiting",
        "🎯 Просто поиграть / любая компания": "casual"
    }

    if choice not in options:
        await msg.answer("Выбери один из вариантов кнопкой")
        return

    user_data[user_id]["looking"] = choice
    path = options[choice]

    # 1. Ищу тиммейта
    if path == "teammate":
        user_data[user_id]["step"] = "tm_experience"
        await msg.answer(
            "⚔️ <b>Ищешь тиммейта</b>\n\n"
            "Сколько примерно часов у тебя в Rust?\n"
            "(или сколько вайпов отыграл)",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

    # 2. Ищу клан
    elif path == "looking_clan":
        user_data[user_id]["step"] = "lc_experience"
        await msg.answer(
            "🏰 <b>Ищешь клан</b>\n\n"
            "Сколько примерно часов / вайпов у тебя в игре?",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

    # 3. Набираю в клан
    elif path == "recruiting":
        user_data[user_id]["step"] = "rec_name"
        await msg.answer(
            "📢 <b>Набираешь игроков в клан</b>\n\n"
            "Напиши <b>название клана</b>:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

    # 4. Просто поиграть
    elif path == "casual":
        user_data[user_id]["step"] = "cas_level"
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Новичок"), KeyboardButton(text="Средний")],
                [KeyboardButton(text="Опытный"), KeyboardButton(text="Очень опытный")]
            ],
            resize_keyboard=True
        )
        await msg.answer(
            "🎯 <b>Просто поиграть</b>\n\n"
            "Какой у тебя уровень в Rust?",
            reply_markup=kb,
            parse_mode="HTML"
        )

# ========== ПУТЬ 1: Ищу тиммейта ==========
@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_experience")
async def tm_experience(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text.strip()
    if len(text) < 2:
        await msg.answer("Напиши хотя бы примерно")
        return

    user_data[user_id]["experience"] = text
    user_data[user_id]["step"] = "tm_role"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Builder"), KeyboardButton(text="PvP / Fighter")],
            [KeyboardButton(text="Farmer / Gatherer"), KeyboardButton(text="All-rounder")],
            [KeyboardButton(text="Другое")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Какая у тебя основная роль?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_role")
async def tm_role(msg: types.Message):
    user_id = msg.from_user.id
    role = msg.text.strip()

    if role == "Другое":
        user_data[user_id]["step"] = "tm_role_custom"
        await msg.answer("Напиши свою роль:", reply_markup=ReplyKeyboardRemove())
        return

    user_data[user_id]["role"] = role
    user_data[user_id]["step"] = "tm_style"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Агрессивный"), KeyboardButton(text="Спокойный")],
            [KeyboardButton(text="Смешанный")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Какой стиль игры предпочитаешь?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_role_custom")
async def tm_role_custom(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["role"] = msg.text.strip()
    user_data[user_id]["step"] = "tm_style"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Агрессивный"), KeyboardButton(text="Спокойный")],
            [KeyboardButton(text="Смешанный")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Какой стиль игры предпочитаешь?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_style")
async def tm_style(msg: types.Message):
    user_id = msg.from_user.id
    if msg.text not in ["Агрессивный", "Спокойный", "Смешанный"]:
        await msg.answer("Выбери кнопкой")
        return

    user_data[user_id]["style"] = msg.text
    user_data[user_id]["step"] = "tm_size"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Дуо"), KeyboardButton(text="Трио")],
            [KeyboardButton(text="4-5 человек"), KeyboardButton(text="Любой размер")]
        ],
        resize_keyboard=True
    )
    await msg.answer("В каком составе хочешь играть?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_size")
async def tm_size(msg: types.Message):
    user_id = msg.from_user.id
    if msg.text not in ["Дуо", "Трио", "4-5 человек", "Любой размер"]:
        await msg.answer("Выбери кнопкой")
        return

    user_data[user_id]["size"] = msg.text
    user_data[user_id]["step"] = "tm_time"
    await msg.answer(
        "Когда обычно играешь?\n"
        "(например: вечера МСК, выходные, с 18:00 и т.д.)",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_time")
async def tm_time(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["online"] = msg.text.strip()
    user_data[user_id]["step"] = "tm_extra"
    await msg.answer(
        "Есть что добавить?\n"
        "(что важно в тиммейте, сервер, особенности и т.д.)\n\n"
        "Можешь написать «нет» или «-»"
    )

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tm_extra")
async def tm_extra(msg: types.Message):
    user_id = msg.from_user.id
    extra = msg.text.strip()
    if extra.lower() in ["нет", "-", "no", ""]:
        extra = "—"

    data = user_data[user_id]
    description = (
        f"Опыт: {data.get('experience')}\n"
        f"Роль: {data.get('role')}\n"
        f"Стиль: {data.get('style')}\n"
        f"Состав: {data.get('size')}\n"
        f"Онлайн: {data.get('online')}\n"
        f"Дополнительно: {extra}"
    )
    user_data[user_id]["description"] = description
    await save_profile(msg)

# ========== ПУТЬ 2: Ищу клан ==========
@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "lc_experience")
async def lc_experience(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["experience"] = msg.text.strip()
    user_data[user_id]["step"] = "lc_role"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Builder"), KeyboardButton(text="PvP")],
            [KeyboardButton(text="Farmer"), KeyboardButton(text="All-rounder")],
            [KeyboardButton(text="Любая роль")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Какую роль хочешь в клане?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "lc_role")
async def lc_role(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["role"] = msg.text.strip()
    user_data[user_id]["step"] = "lc_size"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Маленький (до 8)"), KeyboardButton(text="Средний (8-15)")],
            [KeyboardButton(text="Большой (15+)"), KeyboardButton(text="Не важно")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Какой размер клана предпочитаешь?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "lc_size")
async def lc_size(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["clan_size"] = msg.text.strip()
    user_data[user_id]["step"] = "lc_server"
    await msg.answer(
        "На каком типе серверов хочешь играть?\n"
        "(monthly / weekly / modded / любой / конкретный сервер)",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "lc_server")
async def lc_server(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["server"] = msg.text.strip()
    user_data[user_id]["step"] = "lc_extra"
    await msg.answer(
        "Что ещё важно?\n"
        "(микрофон обязателен, активность, возраст и т.д.)\n\n"
        "Можешь написать «нет»"
    )

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "lc_extra")
async def lc_extra(msg: types.Message):
    user_id = msg.from_user.id
    extra = msg.text.strip()
    if extra.lower() in ["нет", "-", "no", ""]:
        extra = "—"

    data = user_data[user_id]
    description = (
        f"Опыт: {data.get('experience')}\n"
        f"Желаемая роль: {data.get('role')}\n"
        f"Размер клана: {data.get('clan_size')}\n"
        f"Сервер: {data.get('server')}\n"
        f"Дополнительно: {extra}"
    )
    user_data[user_id]["description"] = description
    await save_profile(msg)

# ========== ПУТЬ 3: Набираю в клан ==========
@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "rec_name")
async def rec_name(msg: types.Message):
    user_id = msg.from_user.id
    name = msg.text.strip()
    if len(name) < 2:
        await msg.answer("Напиши название клана")
        return

    user_data[user_id]["clan_name"] = name
    user_data[user_id]["step"] = "rec_members"
    await msg.answer("Сколько человек сейчас в клане?")

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "rec_members")
async def rec_members(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["members"] = msg.text.strip()
    user_data[user_id]["step"] = "rec_server"
    await msg.answer(
        "На каком сервере / типе серверов играете?\n"
        "(название сервера или monthly/weekly/modded)"
    )

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "rec_server")
async def rec_server(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["server"] = msg.text.strip()
    user_data[user_id]["step"] = "rec_req"
    await msg.answer(
        "Какие требования к игрокам?\n"
        "(часы, микрофон, активность, возраст и т.д.)"
    )

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "rec_req")
async def rec_req(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["requirements"] = msg.text.strip()
    user_data[user_id]["step"] = "rec_extra"
    await msg.answer(
        "Есть что добавить о клане?\n"
        "(атмосфера, цели, особенности)\n\n"
        "Можешь написать «нет»"
    )

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "rec_extra")
async def rec_extra(msg: types.Message):
    user_id = msg.from_user.id
    extra = msg.text.strip()
    if extra.lower() in ["нет", "-", "no", ""]:
        extra = "—"

    data = user_data[user_id]
    description = (
        f"Клан: {data.get('clan_name')}\n"
        f"Сейчас человек: {data.get('members')}\n"
        f"Сервер: {data.get('server')}\n"
        f"Требования: {data.get('requirements')}\n"
        f"Дополнительно: {extra}"
    )
    user_data[user_id]["description"] = description
    await save_profile(msg)

# ========== ПУТЬ 4: Просто поиграть ==========
@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "cas_level")
async def cas_level(msg: types.Message):
    user_id = msg.from_user.id
    if msg.text not in ["Новичок", "Средний", "Опытный", "Очень опытный"]:
        await msg.answer("Выбери кнопкой")
        return

    user_data[user_id]["level"] = msg.text
    user_data[user_id]["step"] = "cas_like"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Фарм / строительство"), KeyboardButton(text="PvP")],
            [KeyboardButton(text="Всё подряд"), KeyboardButton(text="Просто почиллить")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Что больше всего нравится делать в игре?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "cas_like")
async def cas_like(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["like"] = msg.text.strip()
    user_data[user_id]["step"] = "cas_time"
    await msg.answer(
        "Когда обычно свободен играть?",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "cas_time")
async def cas_time(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]["online"] = msg.text.strip()
    user_data[user_id]["step"] = "cas_extra"
    await msg.answer(
        "Есть что добавить?\n"
        "(можно написать «нет»)"
    )

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "cas_extra")
async def cas_extra(msg: types.Message):
    user_id = msg.from_user.id
    extra = msg.text.strip()
    if extra.lower() in ["нет", "-", "no", ""]:
        extra = "—"

    data = user_data[user_id]
    description = (
        f"Уровень: {data.get('level')}\n"
        f"Любит: {data.get('like')}\n"
        f"Онлайн: {data.get('online')}\n"
        f"Дополнительно: {extra}"
    )
    user_data[user_id]["description"] = description
    await save_profile(msg)

# ================== СОХРАНЕНИЕ ==================
async def save_profile(msg: types.Message):
    user_id = msg.from_user.id
    data = user_data.get(user_id)
    if not data:
        await msg.answer("Данные потерялись. Начни создание анкеты заново.")
        return

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO profiles
                (user_id, username, looking_for, description, age, microphone, timezone, date, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                user_id,
                msg.from_user.username or "Unknown",
                data.get("looking"),
                data.get("description"),
                data.get("age"),
                data.get("mic"),
                data.get("tz"),
                datetime.now().isoformat()
            ))
            conn.commit()
    except Exception as e:
        await msg.answer(f"Ошибка сохранения: {e}")
        user_data.pop(user_id, None)
        return

    await msg.answer(
        f"✅ <b>Анкета создана!</b>\n\n"
        f"🎯 {data.get('looking')}\n"
        f"🎂 Возраст: {data.get('age')}\n"
        f"🎤 Микрофон: {data.get('mic')}\n"
        f"🕐 Часовой пояс: {data.get('tz')}\n\n"
        f"📝 {data.get('description')}",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    user_data.pop(user_id, None)

# ================== MY PROFILE ==================
@dp.message(F.text == "👤 Моя анкета")
async def my_profile(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT looking_for, description, age, microphone, timezone
            FROM profiles WHERE user_id = ? AND active = 1
        ''', (user_id,))
        r = cur.fetchone()

    if not r or not r["looking_for"]:
        await msg.answer("У тебя пока нет анкеты.")
        return

    await msg.answer(
        f"👤 <b>Твоя анкета</b>\n\n"
        f"🎯 {r['looking_for']}\n"
        f"🎂 Возраст: {r['age']}\n"
        f"🎤 Микрофон: {r['microphone']}\n"
        f"🕐 {r['timezone']}\n\n"
        f"📝 {r['description']}",
        parse_mode="HTML"
    )

@dp.message(F.text == "🗑 Удалить анкету")
async def delete_profile_confirm(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data="delete_yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="delete_no")]
    ])
    await msg.answer("Точно удалить анкету?", reply_markup=kb)

@dp.callback_query(F.data.in_(["delete_yes", "delete_no"]))
async def delete_profile_callback(call: types.CallbackQuery):
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
@dp.message(F.text == "🔍 Искать игроков")
async def search_players(msg: types.Message):
    user_id = msg.from_user.id
    if not check_rate_limit(user_id):
        await msg.answer("⏳ Подожди немного")
        return

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM profiles WHERE active = 1 AND looking_for IS NOT NULL")
        total = cur.fetchone()["cnt"]

        if total == 0:
            await msg.answer("Пока нет активных анкет.")
            return

        cur.execute('''
            SELECT user_id, username, looking_for, description, age, microphone, timezone
            FROM profiles
            WHERE active = 1 AND looking_for IS NOT NULL
            ORDER BY id DESC LIMIT 12
        ''')
        results = cur.fetchall()

    for r in results:
        text = (
            f"👤 @{r['username'] or 'Unknown'}\n"
            f"🎯 {r['looking_for']}\n"
            f"🎂 {r['age']} | 🎤 {r['microphone']} | 🕐 {r['timezone']}\n\n"
            f"{r['description'][:180]}{'...' if len(r['description'] or '') > 180 else ''}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать", url=f"tg://user?id={r['user_id']}")],
            [
                InlineKeyboardButton(text="⭐", callback_data=f"fav_{r['user_id']}"),
                InlineKeyboardButton(text="⚠️", callback_data=f"report_{r['user_id']}")
            ]
        ])
        await msg.answer(text, reply_markup=kb)
        await asyncio.sleep(0.2)

    await msg.answer(f"Показано {len(results)} из {total}")

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
            await call.answer("Убрано из избранного")
        else:
            cur.execute(
                "INSERT OR IGNORE INTO favorites (user_id, favorite_id, date) VALUES (?, ?, ?)",
                (user_id, target_id, datetime.now().isoformat())
            )
            await call.answer("Добавлено в избранное")
        conn.commit()

@dp.message(F.text == "⭐ Избранное")
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
        await msg.answer("Избранных пока нет")
        return

    text = "⭐ <b>Избранное:</b>\n\n"
    for r in rows:
        text += f"@{r['username'] or 'Unknown'}\n{r['looking_for']}\n{r['age']} | {r['microphone']}\n➖\n"
    await msg.answer(text, parse_mode="HTML")

# ================== SWIPE ==================
@dp.message(F.text == "💕 Свайп")
async def swipe_start(msg: types.Message):
    user_id = msg.from_user.id
    if not check_rate_limit(user_id):
        await msg.answer("⏳ Подожди немного")
        return

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT user_id, username, looking_for, age, description, microphone, timezone
            FROM profiles
            WHERE active = 1 AND looking_for IS NOT NULL
              AND user_id != ?
              AND user_id NOT IN (SELECT target_id FROM swipes WHERE user_id = ?)
            ORDER BY RANDOM() LIMIT 1
        ''', (user_id, user_id))
        r = cur.fetchone()

    if not r:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM swipes WHERE user_id = ?", (user_id,))
            conn.commit()
        await msg.answer("Анкеты закончились, начинаю заново")
        return await swipe_start(msg)

    text = (
        f"👤 @{r['username'] or 'Unknown'}\n"
        f"🎯 {r['looking_for']}\n"
        f"🎂 {r['age']} | 🎤 {r['microphone']} | 🕐 {r['timezone']}\n\n"
        f"{r['description'][:150]}{'...' if len(r['description'] or '') > 150 else ''}"
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
        cur.execute(
            "INSERT OR IGNORE INTO swipes (user_id, target_id, action, date) VALUES (?, ?, ?, ?)",
            (user_id, target_id, action, datetime.now().isoformat())
        )
        conn.commit()

        if action == "like":
            cur.execute(
                "SELECT 1 FROM swipes WHERE user_id = ? AND target_id = ? AND action = 'like'",
                (target_id, user_id)
            )
            if cur.fetchone():
                cur.execute("SELECT username FROM profiles WHERE user_id = ?", (target_id,))
                row = cur.fetchone()
                username = row["username"] if row else "Unknown"
                await call.message.answer(f"💕 Взаимный интерес!\nНапиши: @{username}")

    await call.answer()
    try:
        await call.message.delete()
    except:
        pass

# ================== STATS ==================
@dp.message(F.text == "📊 Статистика")
async def stats(msg: types.Message):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM profiles WHERE active = 1 AND looking_for IS NOT NULL")
        count = cur.fetchone()["cnt"]
    await msg.answer(f"📊 Активных анкет: <b>{count}</b>", parse_mode="HTML")

# ================== REPORTS ==================
@dp.callback_query(F.data.startswith("report_"))
async def report_start(call: types.CallbackQuery):
    report_data[call.from_user.id] = {"target": int(call.data.split("_")[1])}
    await call.message.answer("Кратко опиши причину жалобы:")
    await call.answer()

@dp.message(lambda m: m.from_user.id in report_data and m.from_user.id not in user_data)
async def report_reason(msg: types.Message):
    user_id = msg.from_user.id
    target_id = report_data[user_id]["target"]
    reason = msg.text[:300]

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO reports (reporter_id, reported_id, reason, date) VALUES (?, ?, ?, ?)",
            (user_id, target_id, reason, datetime.now().isoformat())
        )
        conn.commit()

    await msg.answer("Жалоба отправлена")
    report_data.pop(user_id, None)

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f"⚠️ Жалоба\nОт: {user_id}\nНа: {target_id}\n{reason}")
        except:
            pass

# ================== ADMIN ==================
@dp.message(Command("ban"))
async def cmd_ban(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return

    args = msg.text.split(maxsplit=2)
    if len(args) < 3:
        await msg.answer("Использование: /ban user_id причина")
        return

    try:
        target = int(args[1])
        reason = args[2]
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO bans (user_id, reason, banned_by, date) VALUES (?, ?, ?, ?)",
                (target, reason, msg.from_user.id, datetime.now().isoformat())
            )
            cur.execute("UPDATE profiles SET active = 0 WHERE user_id = ?", (target,))
            conn.commit()
        await msg.answer(f"Забанен {target}")
        try:
            await bot.send_message(target, f"🚫 Вы забанены.\nПричина: {reason}")
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
        await msg.answer(f"Разбанен {target}")
    except:
        await msg.answer("Ошибка")

# ================== MAIN ==================
async def main():
    print("🤖 Rust LFG Bot v9.1 запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
