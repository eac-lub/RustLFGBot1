# ===== RUST LFG BOT v8.5 (Clean & Secure) =====

import os
import asyncio
import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, BaseMiddleware, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, ReplyKeyboardMarkup, KeyboardButton

# ================== CONFIG ==================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле!")

ADMIN_IDS = [OWNER_ID]

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================== ANTI-SPAM ==================
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
                steam_id TEXT,
                microphone TEXT DEFAULT 'Нет',
                timezone TEXT DEFAULT 'UTC+3',
                max_players INTEGER DEFAULT 1,
                avatar_path TEXT,
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
            CREATE TABLE IF NOT EXISTS clans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                name TEXT,
                tag TEXT,
                description TEXT,
                server TEXT,
                members INTEGER DEFAULT 1,
                max_members INTEGER DEFAULT 10,
                active INTEGER DEFAULT 1,
                date TEXT
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS clan_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan_id INTEGER,
                user_id INTEGER,
                role TEXT DEFAULT 'member',
                joined_date TEXT,
                UNIQUE(clan_id, user_id)
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                message TEXT,
                date TEXT
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
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                enabled INTEGER DEFAULT 1
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
            CREATE TABLE IF NOT EXISTS moderators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                assigned_by INTEGER,
                date TEXT
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

# ================== TEXTS ==================
TEXTS = {
    'ru': {
        'start': "🦀 Добро пожаловать в RustLFG Bot!\n\nЗдесь ты можешь:\n✅ Создать анкету\n✅ Найти команду\n✅ Создать клан\n✅ Общаться\n\nВыберите действие:",
        'profile_created': "✅ Анкета создана!\n\n👥 Ищет: {looking}\n🎂 Возраст: {age}\n📝 {desc}\n🎤 Микрофон: {mic}\n🕐 Часовой пояс: {tz}\n👥 Группа: {max} чел.\n🆔 Steam: {steam}\n📸 Аватар: {avatar}",
        'no_profiles': "😕 Нет активных анкет.",
        'deleted': "✅ Анкета удалена",
        'stats': "📊 Всего активных игроков: **{count}**",
        'profile_already_exists': "У вас уже есть анкета.",
        'confirm_delete': "⚠️ Вы уверены, что хотите удалить анкету?",
        'cancel': "✅ Действие отменено.",
        'spam_warning': "⏳ Не спамьте! Подождите несколько секунд.",
        'desc_too_long': "❌ Описание слишком длинное (макс. 500 символов).",
        'steam_invalid': "❌ Steam ID должен содержать только цифры (или '-' чтобы пропустить).",
        'already_in_clan': "❌ Вы уже состоите в клане.",
        'age_question': "🎂 Выберите возраст:",
        'mic_question': "🎤 Есть ли у вас микрофон?",
        'tz_question': "🕐 Выберите часовой пояс:",
        'group_question': "👥 Сколько человек вы ищете?",
        'description_question': "📝 Расскажите о себе (макс. 500 символов):",
        'steam_question': "🆔 Ваш Steam ID (или '-' пропустить):",
        'avatar_question': "📸 Отправьте фото или '-' чтобы пропустить:",
    },
    'en': {
        'start': "🦀 Welcome to RustLFG Bot!\n\nYou can:\n✅ Create a profile\n✅ Find a team\n✅ Create a clan\n✅ Chat\n\nChoose an action:",
        'profile_created': "✅ Profile created!\n\n👥 Looking for: {looking}\n🎂 Age: {age}\n📝 {desc}\n🎤 Mic: {mic}\n🕐 Timezone: {tz}\n👥 Group: {max}\n🆔 Steam: {steam}\n📸 Avatar: {avatar}",
        'no_profiles': "😕 No active profiles.",
        'deleted': "✅ Profile deleted",
        'stats': "📊 Total active players: **{count}**",
        'profile_already_exists': "You already have a profile.",
        'confirm_delete': "⚠️ Are you sure you want to delete your profile?",
        'cancel': "✅ Action cancelled.",
        'spam_warning': "⏳ Don't spam! Wait a few seconds.",
        'desc_too_long': "❌ Description too long (max 500 chars).",
        'steam_invalid': "❌ Steam ID must contain only numbers (or '-' to skip).",
        'already_in_clan': "❌ You are already in a clan.",
        'age_question': "🎂 Select your age:",
        'mic_question': "🎤 Do you have a microphone?",
        'tz_question': "🕐 Select your timezone:",
        'group_question': "👥 How many people are you looking for?",
        'description_question': "📝 Tell us about yourself (max 500 chars):",
        'steam_question': "🆔 Your Steam ID (or '-' to skip):",
        'avatar_question': "📸 Send a photo or '-' to skip:",
    }
}

# ================== HELPERS ==================
def get_lang(user_id: int) -> str:
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT language FROM profiles WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return row["language"] if row else "ru"
    except Exception:
        return "ru"

def get_text(user_id: int, key: str, **kwargs) -> str:
    lang = get_lang(user_id)
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

def is_banned(user_id: int) -> str | None:
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT reason FROM bans WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return row["reason"] if row else None
    except Exception:
        return None

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def is_moderator(user_id: int) -> bool:
    if is_admin(user_id):
        return True
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM moderators WHERE user_id = ?", (user_id,))
            return cur.fetchone() is not None
    except Exception:
        return False

def check_rate_limit(user_id: int) -> bool:
    now = datetime.now()
    last = last_message_time.get(user_id)
    if last and (now - last).total_seconds() < RATE_LIMIT_SECONDS:
        return False
    last_message_time[user_id] = now
    return True

# ================== KEYBOARDS ==================
def main_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Создать анкету"), KeyboardButton(text="🔍 Искать игроков")],
            [KeyboardButton(text="🏰 Создать клан"), KeyboardButton(text="🏰 Мои кланы")],
            [KeyboardButton(text="👤 Моя анкета"), KeyboardButton(text="🗑 Удалить анкету")],
            [KeyboardButton(text="⭐ Избранное"), KeyboardButton(text="💕 Свайп")],
            [KeyboardButton(text="📊 Статистика")]
        ],
        resize_keyboard=True
    )

def age_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=a) for a in ["16+", "18+", "21+", "25+", "30+"]]],
        resize_keyboard=True
    )

def mic_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🎤 Да"), KeyboardButton(text="🔇 Нет")]],
        resize_keyboard=True
    )

def tz_keyboard() -> ReplyKeyboardMarkup:
    tzs = [f"UTC{i:+d}" for i in range(-12, 13)]
    rows = [tzs[i:i+5] for i in range(0, len(tzs), 5)]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tz) for tz in row] for row in rows],
        resize_keyboard=True
    )

def group_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=str(i)) for i in range(1, 6)]],
        resize_keyboard=True
    )

# ================== STATE ==================
user_data: dict[int, dict] = {}
clan_data: dict[int, dict] = {}
report_data: dict[int, dict] = {}

# ================== COMMANDS ==================
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    user_id = msg.from_user.id
    lang = msg.from_user.language_code if msg.from_user.language_code in ("ru", "en") else "ru"

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO profiles (user_id, username, language) VALUES (?, ?, ?)",
            (user_id, msg.from_user.username or "Unknown", lang)
        )
        cur.execute(
            "INSERT OR IGNORE INTO notifications (user_id, enabled) VALUES (?, 1)",
            (user_id,)
        )
        conn.commit()

    await msg.answer(get_text(user_id, "start"), reply_markup=main_menu(lang))

@dp.message(Command("cancel"))
async def cmd_cancel(msg: types.Message):
    user_id = msg.from_user.id
    user_data.pop(user_id, None)
    clan_data.pop(user_id, None)
    report_data.pop(user_id, None)
    await msg.answer(get_text(user_id, "cancel"), reply_markup=main_menu(get_lang(user_id)))

# ================== PROFILE CREATION ==================
@dp.message(F.text.in_(["📝 Создать анкету", "📝 Create profile"]))
async def create_profile_start(msg: types.Message):
    user_id = msg.from_user.id

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM profiles WHERE user_id = ? AND active = 1 AND looking_for IS NOT NULL", (user_id,))
        if cur.fetchone():
            await msg.answer(get_text(user_id, "profile_already_exists"))
            return

    user_data[user_id] = {"step": "age"}
    await msg.answer(get_text(user_id, "age_question"), reply_markup=age_keyboard())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "age")
async def profile_age(msg: types.Message):
    if msg.text not in ["16+", "18+", "21+", "25+", "30+"]:
        await msg.answer("Выберите возраст кнопкой")
        return
    user_data[msg.from_user.id]["age"] = msg.text
    user_data[msg.from_user.id]["step"] = "mic"
    await msg.answer(get_text(msg.from_user.id, "mic_question"), reply_markup=mic_keyboard())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "mic")
async def profile_mic(msg: types.Message):
    if msg.text not in ["🎤 Да", "🔇 Нет"]:
        await msg.answer("Выберите кнопкой")
        return
    user_data[msg.from_user.id]["mic"] = "Да" if "Да" in msg.text else "Нет"
    user_data[msg.from_user.id]["step"] = "tz"
    await msg.answer(get_text(msg.from_user.id, "tz_question"), reply_markup=tz_keyboard())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "tz")
async def profile_tz(msg: types.Message):
    if not msg.text.startswith("UTC"):
        await msg.answer("Выберите часовой пояс кнопкой")
        return
    user_data[msg.from_user.id]["tz"] = msg.text
    user_data[msg.from_user.id]["step"] = "group"
    await msg.answer(get_text(msg.from_user.id, "group_question"), reply_markup=group_keyboard())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "group")
async def profile_group(msg: types.Message):
    if msg.text not in ["1", "2", "3", "4", "5"]:
        await msg.answer("Выберите число кнопкой")
        return
    user_data[msg.from_user.id]["max_players"] = int(msg.text)
    user_data[msg.from_user.id]["step"] = "looking"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🤝 Ищу тиммейта")],
            [KeyboardButton(text="🔍 Ищу клан")],
            [KeyboardButton(text="🏰 Ищем игроков в клан")],
            [KeyboardButton(text="🎯 Любая команда")]
        ],
        resize_keyboard=True
    )
    await msg.answer("👥 Кого вы ищете?", reply_markup=kb)

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "looking")
async def profile_looking(msg: types.Message):
    user_data[msg.from_user.id]["looking"] = msg.text
    user_data[msg.from_user.id]["step"] = "description"
    await msg.answer(get_text(msg.from_user.id, "description_question"), reply_markup=types.ReplyKeyboardRemove())

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "description")
async def profile_description(msg: types.Message):
    if len(msg.text) > 500:
        await msg.answer(get_text(msg.from_user.id, "desc_too_long"))
        return
    user_data[msg.from_user.id]["description"] = msg.text
    user_data[msg.from_user.id]["step"] = "steam"
    await msg.answer(get_text(msg.from_user.id, "steam_question"))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "steam")
async def profile_steam(msg: types.Message):
    steam = msg.text.strip()
    if steam != "-" and not steam.isdigit():
        await msg.answer(get_text(msg.from_user.id, "steam_invalid"))
        return
    user_data[msg.from_user.id]["steam"] = steam if steam != "-" else "Не указан"
    user_data[msg.from_user.id]["step"] = "avatar"
    await msg.answer(get_text(msg.from_user.id, "avatar_question"))

@dp.message(lambda m: m.from_user.id in user_data and user_data[m.from_user.id].get("step") == "avatar")
async def profile_avatar(msg: types.Message):
    user_id = msg.from_user.id
    data = user_data.get(user_id)
    if not data:
        return

    if msg.text == "-":
        data["avatar_path"] = None
        await save_profile(msg)
        return

    if not msg.photo:
        await msg.answer("Отправьте фото или '-'")
        return

    # Ограничение размера (последнее фото обычно самое большое)
    photo = msg.photo[-1]
    if photo.file_size and photo.file_size > 5 * 1024 * 1024:  # 5 MB
        await msg.answer("❌ Фото слишком большое (макс. 5 МБ)")
        return

    try:
        file = await bot.get_file(photo.file_id)
        os.makedirs("avatars", exist_ok=True)
        path = f"avatars/{user_id}.jpg"
        await bot.download_file(file.file_path, path)
        data["avatar_path"] = path
        await save_profile(msg)
    except Exception as e:
        await msg.answer(f"❌ Ошибка загрузки фото: {e}")

async def save_profile(msg: types.Message):
    user_id = msg.from_user.id
    data = user_data.get(user_id)
    if not data:
        await msg.answer("❌ Данные анкеты потеряны. Начните заново.")
        return

    lang = get_lang(user_id)

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO profiles
                (user_id, username, looking_for, description, age, steam_id,
                 microphone, timezone, max_players, avatar_path, date, language, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                user_id,
                msg.from_user.username or "Unknown",
                data.get("looking", "Не указано"),
                data.get("description", "Не указано"),
                data.get("age", "Не указан"),
                data.get("steam", "Не указан"),
                data.get("mic", "Нет"),
                data.get("tz", "UTC+3"),
                data.get("max_players", 1),
                data.get("avatar_path"),
                datetime.now().isoformat(),
                lang
            ))
            conn.commit()
    except Exception as e:
        await msg.answer(f"❌ Ошибка сохранения: {e}")
        user_data.pop(user_id, None)
        return

    avatar_text = "✅ Есть" if data.get("avatar_path") else "❌ Нет"
    await msg.answer(
        get_text(user_id, "profile_created",
                 looking=data.get("looking"),
                 age=data.get("age"),
                 desc=data.get("description"),
                 mic=data.get("mic"),
                 tz=data.get("tz"),
                 max=data.get("max_players"),
                 steam=data.get("steam"),
                 avatar=avatar_text),
        reply_markup=main_menu(lang)
    )

    if data.get("avatar_path") and os.path.exists(data["avatar_path"]):
        try:
            await msg.answer_photo(FSInputFile(data["avatar_path"]), caption="📸 Ваша аватарка")
        except Exception:
            pass

    user_data.pop(user_id, None)

# ================== PROFILE MANAGEMENT ==================
@dp.message(F.text.in_(["👤 Моя анкета", "👤 My profile"]))
async def my_profile(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT looking_for, description, age, microphone, timezone,
                   max_players, steam_id, avatar_path
            FROM profiles WHERE user_id = ? AND active = 1
        ''', (user_id,))
        r = cur.fetchone()

    if not r:
        await msg.answer("❌ У вас нет анкеты.")
        return

    text = (
        f"👤 **Ваша анкета**\n\n"
        f"👥 Ищет: {r['looking_for']}\n"
        f"🎂 Возраст: {r['age']}\n"
        f"🎤 Микрофон: {r['microphone']}\n"
        f"🕐 Часовой пояс: {r['timezone']}\n"
        f"👥 Группа: {r['max_players']} чел.\n"
        f"🆔 Steam: {r['steam_id']}\n"
        f"📝 {r['description']}"
    )

    if r["avatar_path"] and os.path.exists(r["avatar_path"]):
        try:
            await msg.answer_photo(FSInputFile(r["avatar_path"]), caption=text)
            return
        except Exception:
            pass
    await msg.answer(text)

@dp.message(F.text.in_(["🗑 Удалить анкету", "🗑 Delete profile"]))
async def delete_profile_confirm(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="delete_yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="delete_no")]
    ])
    await msg.answer(get_text(msg.from_user.id, "confirm_delete"), reply_markup=kb)

@dp.callback_query(F.data.in_(["delete_yes", "delete_no"]))
async def delete_profile_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    if call.data == "delete_yes":
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE profiles SET active = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
        await call.message.edit_text(get_text(user_id, "deleted"))
    else:
        await call.message.edit_text("❌ Удаление отменено")
    await call.answer()

# ================== SEARCH ==================
@dp.message(F.text.in_(["🔍 Искать игроков", "🔍 Find players"]))
async def search_players(msg: types.Message):
    user_id = msg.from_user.id
    if not check_rate_limit(user_id):
        await msg.answer(get_text(user_id, "spam_warning"))
        return

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM profiles WHERE active = 1")
        total = cur.fetchone()["cnt"]

        if total == 0:
            await msg.answer(get_text(user_id, "no_profiles"))
            return

        cur.execute('''
            SELECT user_id, username, looking_for, description, age,
                   microphone, timezone, max_players, steam_id, avatar_path
            FROM profiles WHERE active = 1
            ORDER BY id DESC LIMIT 15
        ''')
        results = cur.fetchall()

    for r in results:
        text = (
            f"👤 @{r['username'] or 'Unknown'}\n"
            f"👥 Ищет: {r['looking_for']}\n"
            f"🎂 Возраст: {r['age']}\n"
            f"🎤 Микрофон: {r['microphone']}\n"
            f"🕐 {r['timezone']} | 👥 {r['max_players']} чел.\n"
            f"🆔 Steam: {r['steam_id']}\n"
            f"📝 {r['description'][:120]}{'...' if len(r['description'] or '') > 120 else ''}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать", url=f"tg://user?id={r['user_id']}")],
            [
                InlineKeyboardButton(text="⭐", callback_data=f"fav_{r['user_id']}"),
                InlineKeyboardButton(text="⚠️ Жалоба", callback_data=f"report_{r['user_id']}")
            ]
        ])

        if r["avatar_path"] and os.path.exists(r["avatar_path"]):
            try:
                await msg.answer_photo(FSInputFile(r["avatar_path"]), caption=text, reply_markup=kb)
            except Exception:
                await msg.answer(text, reply_markup=kb)
        else:
            await msg.answer(text, reply_markup=kb)
        await asyncio.sleep(0.25)

    await msg.answer(f"📊 Показано {len(results)} из {total}")

# ================== FAVORITES ==================
@dp.callback_query(F.data.startswith("fav_"))
async def toggle_favorite(call: types.CallbackQuery):
    user_id = call.from_user.id
    target_id = int(call.data.split("_")[1])

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM favorites WHERE user_id = ? AND favorite_id = ?", (user_id, target_id))
        exists = cur.fetchone()

        if exists:
            cur.execute("DELETE FROM favorites WHERE user_id = ? AND favorite_id = ?", (user_id, target_id))
            await call.answer("❌ Удалено из избранного")
        else:
            cur.execute(
                "INSERT OR IGNORE INTO favorites (user_id, favorite_id, date) VALUES (?, ?, ?)",
                (user_id, target_id, datetime.now().isoformat())
            )
            await call.answer("✅ Добавлено в избранное")
        conn.commit()

@dp.message(F.text.in_(["⭐ Избранное", "⭐ Favorites"]))
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
        await msg.answer("⭐ У вас пока нет избранных")
        return

    text = "⭐ **Избранное:**\n\n"
    for r in rows:
        text += f"👤 @{r['username'] or 'Unknown'}\n👥 {r['looking_for']}\n🎂 {r['age']} | 🎤 {r['microphone']}\n➖➖➖\n"
    await msg.answer(text)

# ================== SWIPE ==================
@dp.message(F.text.in_(["💕 Свайп", "💕 Swipe"]))
async def swipe_start(msg: types.Message):
    user_id = msg.from_user.id
    if not check_rate_limit(user_id):
        await msg.answer(get_text(user_id, "spam_warning"))
        return

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT user_id, username, looking_for, age, description, microphone, avatar_path
            FROM profiles
            WHERE active = 1
              AND user_id != ?
              AND user_id NOT IN (SELECT target_id FROM swipes WHERE user_id = ?)
            ORDER BY RANDOM() LIMIT 1
        ''', (user_id, user_id))
        r = cur.fetchone()

    if not r:
        # Сбрасываем историю свайпов
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM swipes WHERE user_id = ?", (user_id,))
            conn.commit()
        await msg.answer("💕 Вы просмотрели всех. Начинаем заново!")
        return await swipe_start(msg)

    text = (
        f"👤 @{r['username'] or 'Unknown'}\n"
        f"👥 {r['looking_for']}\n"
        f"🎂 {r['age']} | 🎤 {r['microphone']}\n"
        f"📝 {r['description'][:100]}{'...' if len(r['description'] or '') > 100 else ''}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❤️", callback_data=f"swipe_like_{r['user_id']}"),
        InlineKeyboardButton(text="⛔", callback_data=f"swipe_dislike_{r['user_id']}")
    ]])

    if r["avatar_path"] and os.path.exists(r["avatar_path"]):
        try:
            await msg.answer_photo(FSInputFile(r["avatar_path"]), caption=text, reply_markup=kb)
            return
        except Exception:
            pass
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
                await call.message.answer(f"💕 **Взаимный лайк!**\nНапишите: @{username}")

    await call.answer("❤️" if action == "like" else "⛔")
    try:
        await call.message.delete()
    except Exception:
        pass
    # Можно сразу показать следующую анкету
    # await swipe_start(call.message)

# ================== CLANS (базово) ==================
@dp.message(F.text.in_(["🏰 Создать клан", "🏰 Create clan"]))
async def create_clan_start(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM clan_members WHERE user_id = ?", (user_id,))
        if cur.fetchone():
            await msg.answer(get_text(user_id, "already_in_clan"))
            return

    clan_data[user_id] = {"step": "name"}
    await msg.answer("🏷️ Введите название клана:")

@dp.message(lambda m: m.from_user.id in clan_data and clan_data[m.from_user.id].get("step") == "name")
async def clan_name(msg: types.Message):
    clan_data[msg.from_user.id]["name"] = msg.text[:50]
    clan_data[msg.from_user.id]["step"] = "tag"
    await msg.answer("🏷️ Введите тег (2-4 символа):")

@dp.message(lambda m: m.from_user.id in clan_data and clan_data[m.from_user.id].get("step") == "tag")
async def clan_tag(msg: types.Message):
    tag = msg.text.strip().upper()
    if not (2 <= len(tag) <= 4):
        await msg.answer("Тег должен быть 2-4 символа")
        return
    clan_data[msg.from_user.id]["tag"] = tag
    clan_data[msg.from_user.id]["step"] = "desc"
    await msg.answer("📝 Опишите клан:")

@dp.message(lambda m: m.from_user.id in clan_data and clan_data[m.from_user.id].get("step") == "desc")
async def clan_desc(msg: types.Message):
    clan_data[msg.from_user.id]["desc"] = msg.text[:500]
    clan_data[msg.from_user.id]["step"] = "server"
    await msg.answer("🌐 На каком сервере играет клан?")

@dp.message(lambda m: m.from_user.id in clan_data and clan_data[m.from_user.id].get("step") == "server")
async def clan_server(msg: types.Message):
    user_id = msg.from_user.id
    data = clan_data[user_id]
    data["server"] = msg.text[:100]

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO clans (creator_id, name, tag, description, server, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, data["name"], data["tag"], data["desc"], data["server"], datetime.now().isoformat()))
            clan_id = cur.lastrowid
            cur.execute(
                "INSERT INTO clan_members (clan_id, user_id, role, joined_date) VALUES (?, ?, 'leader', ?)",
                (clan_id, user_id, datetime.now().isoformat())
            )
            conn.commit()
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")
        clan_data.pop(user_id, None)
        return

    await msg.answer(
        f"✅ Клан создан!\n\n🏷️ {data['name']} [{data['tag']}]\n"
        f"📝 {data['desc']}\n🌐 {data['server']}",
        reply_markup=main_menu(get_lang(user_id))
    )
    clan_data.pop(user_id, None)

@dp.message(F.text.in_(["🏰 Мои кланы", "🏰 My clans"]))
async def my_clans(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT c.name, c.tag, c.description, c.server, c.members, c.max_members
            FROM clans c
            JOIN clan_members cm ON c.id = cm.clan_id
            WHERE cm.user_id = ? AND c.active = 1
        ''', (user_id,))
        rows = cur.fetchall()

    if not rows:
        await msg.answer("🏰 Вы не состоите ни в одном клане")
        return

    text = "🏰 **Ваши кланы:**\n\n"
    for r in rows:
        text += f"🏷️ {r['name']} [{r['tag']}]\n📝 {r['description'][:80]}...\n🌐 {r['server']}\n👥 {r['members']}/{r['max_members']}\n➖➖➖\n"
    await msg.answer(text)

# ================== STATS ==================
@dp.message(F.text.in_(["📊 Статистика", "📊 Total players", "📊 Всего игроков"]))
async def stats(msg: types.Message):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM profiles WHERE active = 1")
        count = cur.fetchone()["cnt"]
    await msg.answer(get_text(msg.from_user.id, "stats", count=count))

# ================== REPORTS ==================
@dp.callback_query(F.data.startswith("report_"))
async def report_start(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    report_data[call.from_user.id] = {"target": target_id}
    await call.message.answer("📝 Кратко опишите причину жалобы:")
    await call.answer()

@dp.message(lambda m: m.from_user.id in report_data)
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

    await msg.answer("📩 Жалоба отправлена модераторам")
    report_data.pop(user_id, None)

    # Уведомление админам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"⚠️ Новая жалоба\nОт: {user_id}\nНа: {target_id}\nПричина: {reason}"
            )
        except Exception:
            pass

# ================== ADMIN ==================
@dp.message(Command("admin"))
async def admin_panel(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("🚫 Нет доступа")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📩 Жалобы", callback_data="admin_reports")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")]
    ])
    await msg.answer("🔐 Админ-панель", reply_markup=kb)

@dp.callback_query(F.data.startswith("admin_"))
async def admin_actions(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    action = call.data.split("_")[1]

    if action == "stats":
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as c FROM profiles WHERE active = 1")
            profiles = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM clans WHERE active = 1")
            clans = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM reports WHERE resolved = 0")
            reports = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM bans")
            bans = cur.fetchone()["c"]

        await call.message.edit_text(
            f"📊 **Статистика**\n\n"
            f"👥 Анкет: {profiles}\n"
            f"🏰 Кланов: {clans}\n"
            f"📩 Жалоб: {reports}\n"
            f"🚫 Банов: {bans}"
        )
    elif action == "reports":
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, reporter_id, reported_id, reason FROM reports WHERE resolved = 0 ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()

        if not rows:
            await call.message.edit_text("📩 Нет новых жалоб")
        else:
            text = "📩 **Жалобы:**\n\n"
            for r in rows:
                text += f"#{r['id']} | {r['reporter_id']} → {r['reported_id']}\n{r['reason']}\n➖\n"
            text += "\nЗакрыть: /resolve <id>"
            await call.message.edit_text(text)
    elif action == "close":
        await call.message.delete()

    await call.answer()

@dp.message(Command("ban"))
async def cmd_ban(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    args = msg.text.split(maxsplit=2)
    if len(args) < 3:
        await msg.answer("Использование: /ban <user_id> <причина>")
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
        await msg.answer(f"✅ Пользователь {target} забанен")
        try:
            await bot.send_message(target, f"🚫 Вы забанены.\nПричина: {reason}")
        except Exception:
            pass
    except Exception as e:
        await msg.answer(f"Ошибка: {e}")

@dp.message(Command("unban"))
async def cmd_unban(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /unban <user_id>")
        return
    try:
        target = int(args[1])
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM bans WHERE user_id = ?", (target,))
            conn.commit()
        await msg.answer(f"✅ Пользователь {target} разбанен")
    except Exception as e:
        await msg.answer(f"Ошибка: {e}")

@dp.message(Command("resolve"))
async def cmd_resolve(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /resolve <report_id>")
        return
    try:
        rid = int(args[1])
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE reports SET resolved = 1 WHERE id = ?", (rid,))
            conn.commit()
        await msg.answer(f"✅ Жалоба #{rid} закрыта")
    except Exception as e:
        await msg.answer(f"Ошибка: {e}")

# ================== MAIN ==================
async def main():
    os.makedirs("avatars", exist_ok=True)
    print("🤖 Rust LFG Bot v8.5 запущен")
    print(f"👑 Owner ID: {OWNER_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
