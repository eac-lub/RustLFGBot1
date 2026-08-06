# ===== RUST LFG BOT v7.0 =====
# Full-featured bot with admin panel, moderation, clans, favorites, swipe system, chat, and more

import os
import asyncio
import sqlite3
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram import F

# ===== TOKEN =====
TOKEN = "8804113008:AAGgdo_FZMDoWr2C0SBChjo4-HMRiEog-D4"

# ===== ADMIN =====
OWNER_ID = 6276697402
ADMIN_IDS = [OWNER_ID]  # Можно добавить других админов

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== DATABASE =====
def init_db():
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()

    # Users / Profiles
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

    # Favorites
    cur.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            favorite_id INTEGER,
            date TEXT
        )
    ''')

    # Clans
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

    # Clan members
    cur.execute('''
        CREATE TABLE IF NOT EXISTS clan_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clan_id INTEGER,
            user_id INTEGER,
            role TEXT DEFAULT 'member',
            joined_date TEXT
        )
    ''')

    # Chat messages
    cur.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message TEXT,
            date TEXT
        )
    ''')

    # Bans
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            reason TEXT,
            banned_by INTEGER,
            date TEXT
        )
    ''')

    # Reports
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

    # Notifications
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            enabled INTEGER DEFAULT 1
        )
    ''')

    # Swipes
    cur.execute('''
        CREATE TABLE IF NOT EXISTS swipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            target_id INTEGER,
            action TEXT,
            date TEXT
        )
    ''')

    # Moderators
    cur.execute('''
        CREATE TABLE IF NOT EXISTS moderators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            assigned_by INTEGER,
            date TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ===== TEXTS =====
TEXTS = {
    'ru': {
        'start': "🦀 Добро пожаловать в RustLFG Bot!\n\nЗдесь ты можешь:\n✅ Создать анкету\n✅ Найти команду\n✅ Создать клан\n✅ Общаться в чате\n\nВыберите действие:",
        'profile_created': "✅ Анкета создана!\n\n👥 Ищет: {looking}\n🎂 Возраст: {age}\n📝 {desc}\n🎤 Микрофон: {mic}\n🕐 Часовой пояс: {tz}\n👥 Группа: {max} чел.\n🆔 Steam: {steam}\n📸 Аватар: {avatar}\n\nТеперь вас могут найти!",
        'no_profiles': "😕 Нет активных анкет. Создайте свою первую!",
        'deleted': "✅ Анкета удалена",
        'stats': "📊 Всего активных игроков: **{count}**",
        'looking_for': "Ищет:",
        'about_me': "О себе:",
        'write_button': "💬 Написать",
        'search_players': "🔍 Искать игроков",
        'create_profile': "📝 Создать анкету",
        'my_profile_btn': "👤 Моя анкета",
        'delete_profile': "🗑 Удалить анкету",
        'stats_btn': "📊 Всего игроков",
        'create_clan': "🏰 Создать клан",
        'clan_name': "🏷️ Введите название клана:",
        'clan_tag': "🏷️ Введите тег клана (2-4 символа):",
        'clan_desc': "📝 Опишите ваш клан (цели, стиль игры, требования):",
        'clan_server': "🌐 На каком сервере играет клан?",
        'clan_created': "✅ Клан создан!\n\n🏷️ {name} [{tag}]\n📝 {desc}\n🌐 Сервер: {server}\n👥 Участников: {members}/{max}",
        'clan_list': "🏰 **Список кланов:**\n\n{clans}",
        'join_clan': "🤝 Вступить в клан",
        'clan_request_sent': "✅ Заявка на вступление отправлена!",
        'favorite_added': "✅ Добавлен в избранное!",
        'favorite_removed': "❌ Удалён из избранного!",
        'favorites_list': "⭐ **Избранное:**\n\n{favorites}",
        'swipe_intro': "💕 **Свайп-система**\n\nВот анкета игрока. Нажми ❤️ если нравится, ⛔ если нет.",
        'swipe_like': "❤️ Вы поставили лайк!",
        'swipe_dislike': "⛔ Вы пропустили анкету.",
        'swipe_match': "💕 **Взаимный интерес!**\n\nВы оба понравились друг другу. Напишите игроку: @{username}",
        'chat_welcome': "💬 **Общий чат**\n\nПиши сообщения — их увидят все. Общайся, ищи команду, делись опытом.",
        'report_sent': "📩 Жалоба отправлена модератору.",
        'banned': "🚫 Вы забанены. Причина: {reason}",
        'age_question': "🎂 Выберите возраст:",
        'mic_question': "🎤 Есть ли у вас микрофон?",
        'tz_question': "🕐 Выберите часовой пояс:",
        'group_question': "👥 Сколько человек вы ищете в команду?",
        'description_question': "📝 Расскажите о себе:",
        'steam_question': "🆔 Ваш Steam ID:",
        'avatar_question': "📸 Отправьте фото (или '-' пропустить):",
        'profile_already_exists': "У вас уже есть анкета. Обновите её или удалите."
    },
    'en': {
        'start': "🦀 Welcome to RustLFG Bot!\n\nHere you can:\n✅ Create a profile\n✅ Find a team\n✅ Create a clan\n✅ Chat with others\n\nChoose an action:",
        'profile_created': "✅ Profile created!\n\n👥 Looking for: {looking}\n🎂 Age: {age}\n📝 {desc}\n🎤 Microphone: {mic}\n🕐 Timezone: {tz}\n👥 Group: {max} people\n🆔 Steam: {steam}\n📸 Avatar: {avatar}\n\nNow you can be found!",
        'no_profiles': "😕 No active profiles. Create your first one!",
        'deleted': "✅ Profile deleted",
        'stats': "📊 Total active players: **{count}**",
        'looking_for': "Looking for:",
        'about_me': "About me:",
        'write_button': "💬 Write",
        'search_players': "🔍 Find players",
        'create_profile': "📝 Create profile",
        'my_profile_btn': "👤 My profile",
        'delete_profile': "🗑 Delete profile",
        'stats_btn': "📊 Total players",
        'create_clan': "🏰 Create clan",
        'clan_name': "🏷️ Enter clan name:",
        'clan_tag': "🏷️ Enter clan tag (2-4 chars):",
        'clan_desc': "📝 Describe your clan (goals, playstyle, requirements):",
        'clan_server': "🌐 Which server does the clan play on?",
        'clan_created': "✅ Clan created!\n\n🏷️ {name} [{tag}]\n📝 {desc}\n🌐 Server: {server}\n👥 Members: {members}/{max}",
        'clan_list': "🏰 **Clan list:**\n\n{clans}",
        'join_clan': "🤝 Join clan",
        'clan_request_sent': "✅ Join request sent!",
        'favorite_added': "✅ Added to favorites!",
        'favorite_removed': "❌ Removed from favorites!",
        'favorites_list': "⭐ **Favorites:**\n\n{favorites}",
        'swipe_intro': "💕 **Swipe system**\n\nHere is a player's profile. Press ❤️ if you like it, ⛔ if not.",
        'swipe_like': "❤️ You liked this player!",
        'swipe_dislike': "⛔ You skipped this profile.",
        'swipe_match': "💕 **Mutual interest!**\n\nYou both liked each other. Write to @{username}",
        'chat_welcome': "💬 **General chat**\n\nSend messages that everyone will see. Chat, find a team, share experience.",
        'report_sent': "📩 Report sent to moderator.",
        'banned': "🚫 You are banned. Reason: {reason}",
        'age_question': "🎂 Select your age:",
        'mic_question': "🎤 Do you have a microphone?",
        'tz_question': "🕐 Select your timezone:",
        'group_question': "👥 How many people are you looking for?",
        'description_question': "📝 Tell us about yourself:",
        'steam_question': "🆔 Your Steam ID:",
        'avatar_question': "📸 Send a photo (or '-' to skip):",
        'profile_already_exists': "You already have a profile. Update it or delete it."
    }
}

# ===== HELPERS =====
def get_lang(user_id):
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT language FROM profiles WHERE user_id = ?', (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 'ru'

def get_text(user_id, key, **kwargs):
    lang = get_lang(user_id)
    text = TEXTS.get(lang, TEXTS['ru']).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

def is_banned(user_id):
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT reason FROM bans WHERE user_id = ?', (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_moderator(user_id):
    if is_admin(user_id):
        return True
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT id FROM moderators WHERE user_id = ?', (user_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None

def main_menu(lang='ru'):
    t = TEXTS.get(lang, TEXTS['ru'])
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text=t['create_profile']),
                types.KeyboardButton(text=t['search_players'])
            ],
            [
                types.KeyboardButton(text=t['create_clan']),
                types.KeyboardButton(text="🏰 Мои кланы / My clans")
            ],
            [
                types.KeyboardButton(text=t['my_profile_btn']),
                types.KeyboardButton(text=t['delete_profile'])
            ],
            [
                types.KeyboardButton(text="💬 Чат / Chat"),
                types.KeyboardButton(text="⭐ Избранное / Favorites")
            ],
            [
                types.KeyboardButton(text="💕 Свайп / Swipe"),
                types.KeyboardButton(text=t['stats_btn'])
            ]
        ],
        resize_keyboard=True
    )
    return kb

def age_buttons(lang='ru'):
    buttons = ['16+', '18+', '21+', '25+', '30+']
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=age) for age in buttons[i:i+3]] for i in range(0, len(buttons), 3)],
        resize_keyboard=True
    )
    return kb

def mic_buttons(lang='ru'):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🎤 Да / Yes"), types.KeyboardButton(text="🔇 Нет / No")]
        ],
        resize_keyboard=True
    )
    return kb

def tz_buttons(lang='ru'):
    tzs = ['UTC-12', 'UTC-11', 'UTC-10', 'UTC-9', 'UTC-8', 'UTC-7', 'UTC-6', 'UTC-5',
           'UTC-4', 'UTC-3', 'UTC-2', 'UTC-1', 'UTC+0', 'UTC+1', 'UTC+2', 'UTC+3',
           'UTC+4', 'UTC+5', 'UTC+6', 'UTC+7', 'UTC+8', 'UTC+9', 'UTC+10', 'UTC+11', 'UTC+12']
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=tz) for tz in tzs[i:i+5]] for i in range(0, len(tzs), 5)],
        resize_keyboard=True
    )
    return kb

def group_buttons(lang='ru'):
    buttons = ['1', '2', '3', '4', '5']
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=n) for n in buttons[i:i+3]] for i in range(0, len(buttons), 3)],
        resize_keyboard=True
    )
    return kb

def admin_panel():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Полная статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📩 Жалобы", callback_data="admin_reports")],
        [InlineKeyboardButton(text="👥 Модераторы", callback_data="admin_moderators")],
        [InlineKeyboardButton(text="📢 Сделать объявление", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")]
    ])
    return kb

# ===== MIDDLEWARE - BAN CHECK =====
@dp.message()
async def check_bans(msg: types.Message):
    if msg.text and msg.text.startswith('/'):
        return
    ban_reason = is_banned(msg.from_user.id)
    if ban_reason:
        await msg.answer(f"🚫 Вы забанены. Причина: {ban_reason}")
        return
    await dp.message_handlers.handle(msg)

# ============================================
# ========== USER COMMANDS ==========
# ============================================

@dp.message(Command("start"))
async def start(msg: types.Message):
    user_id = msg.from_user.id
    lang = msg.from_user.language_code if msg.from_user.language_code in ['ru', 'en'] else 'ru'
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT OR REPLACE INTO profiles (user_id, username, language)
        VALUES (?, ?, ?)
    ''', (user_id, msg.from_user.username or "Не указан", lang))
    cur.execute('INSERT OR IGNORE INTO notifications (user_id, enabled) VALUES (?, 1)', (user_id,))
    conn.commit()
    conn.close()
    
    t = TEXTS.get(lang, TEXTS['ru'])
    await msg.answer(t['start'], reply_markup=main_menu(lang))

# ===== CREATE PROFILE =====
user_data = {}

@dp.message(lambda msg: msg.text in ["📝 Создать анкету", "📝 Create profile"])
async def create_profile_start(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT id FROM profiles WHERE user_id = ? AND active = 1', (user_id,))
    if cur.fetchone():
        await msg.answer(t['profile_already_exists'])
        conn.close()
        return
    conn.close()
    
    user_data[user_id] = {'step': 'age'}
    await msg.answer(t['age_question'], reply_markup=age_buttons(lang))

@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get('step') == 'age')
async def profile_age(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if msg.text not in ['16+', '18+', '21+', '25+', '30+']:
        await msg.answer("Выберите возраст из кнопок / Choose age from buttons")
        return
    
    user_data[user_id]['age'] = msg.text
    user_data[user_id]['step'] = 'mic'
    await msg.answer(t['mic_question'], reply_markup=mic_buttons(lang))

@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get('step') == 'mic')
async def profile_mic(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if msg.text not in ["🎤 Да / Yes", "🔇 Нет / No"]:
        await msg.answer("Выберите из кнопок / Choose from buttons")
        return
    
    user_data[user_id]['mic'] = "Да" if "Да" in msg.text else "Нет"
    user_data[user_id]['step'] = 'tz'
    await msg.answer(t['tz_question'], reply_markup=tz_buttons(lang))

@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get('step') == 'tz')
async def profile_tz(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if not msg.text.startswith('UTC'):
        await msg.answer("Выберите часовой пояс из кнопок / Choose timezone from buttons")
        return
    
    user_data[user_id]['tz'] = msg.text
    user_data[user_id]['step'] = 'group'
    await msg.answer(t['group_question'], reply_markup=group_buttons(lang))

@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get('step') == 'group')
async def profile_group(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if msg.text not in ['1', '2', '3', '4', '5']:
        await msg.answer("Выберите количество из кнопок / Choose number from buttons")
        return
    
    user_data[user_id]['max_players'] = int(msg.text)
    user_data[user_id]['step'] = 'looking'
    
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🤝 Ищу тиммейта(ов) / Looking for teammate(s)")],
            [types.KeyboardButton(text="🔍 Ищу клан / Looking for clan")],
            [types.KeyboardButton(text="🏰 Ищем игроков в клан / Looking for players")],
            [types.KeyboardButton(text="🎯 Ищу любую команду / Any team")]
        ],
        resize_keyboard=True
    )
    await msg.answer("👥 Кого вы ищете? / Who are you looking for?", reply_markup=kb)

@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get('step') == 'looking')
async def profile_looking(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    user_data[user_id]['looking'] = msg.text
    user_data[user_id]['step'] = 'description'
    await msg.answer(t['description_question'])

@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get('step') == 'description')
async def profile_description(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    user_data[user_id]['description'] = msg.text
    user_data[user_id]['step'] = 'steam'
    await msg.answer(t['steam_question'])

@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get('step') == 'steam')
async def profile_steam(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    user_data[user_id]['steam'] = msg.text
    user_data[user_id]['step'] = 'avatar'
    await msg.answer(t['avatar_question'])

@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get('step') == 'avatar')
async def profile_avatar(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    data = user_data[user_id]
    
    if msg.text and msg.text == '-':
        data['avatar_path'] = None
        await save_profile(msg)
        return
    
    if msg.photo:
        file = await bot.get_file(msg.photo[-1].file_id)
        file_path = f"avatars/{user_id}.jpg"
        os.makedirs("avatars", exist_ok=True)
        await bot.download_file(file.file_path, file_path)
        data['avatar_path'] = file_path
        await save_profile(msg)
    else:
        await msg.answer("Отправьте фото или '-' чтобы пропустить / Send photo or '-' to skip")

async def save_profile(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    data = user_data.get(user_id, {})
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT OR REPLACE INTO profiles 
        (user_id, username, looking_for, description, age, steam_id, microphone, timezone, max_players, avatar_path, date, language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        msg.from_user.username or "Не указан",
        data.get('looking', 'Не указано'),
        data.get('description', 'Не указано'),
        data.get('age', 'Не указан'),
        data.get('steam', 'Не указан'),
        data.get('mic', 'Нет'),
        data.get('tz', 'UTC+3'),
        data.get('max_players', 1),
        data.get('avatar_path'),
        datetime.now(),
        lang
    ))
    conn.commit()
    conn.close()
    
    avatar_text = "✅ Есть" if data.get('avatar_path') else "❌ Нет"
    
    await msg.answer(
        t['profile_created'].format(
            looking=data.get('looking', 'Не указано'),
            age=data.get('age', 'Не указан'),
            desc=data.get('description', 'Не указано'),
            mic=data.get('mic', 'Нет'),
            tz=data.get('tz', 'UTC+3'),
            max=data.get('max_players', 1),
            steam=data.get('steam', 'Не указан'),
            avatar=avatar_text
        ),
        reply_markup=main_menu(lang)
    )
    
    if data.get('avatar_path'):
        photo = FSInputFile(data['avatar_path'])
        await msg.answer_photo(photo, caption="📸 Ваша аватарка / Your avatar")
    
    if user_id in user_data:
        del user_data[user_id]
    
    # Уведомления другим пользователям
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM notifications WHERE enabled = 1')
    users = cur.fetchall()
    conn.close()
    
    for u in users:
        if u[0] != user_id:
            try:
                await bot.send_message(u[0], f"🦀 Новый игрок в поиске! / New player in search!\n👤 @{msg.from_user.username or 'Игрок'}")
            except:
                pass

# ============================================
# ========== SEARCH ==========
# ============================================

@dp.message(lambda msg: msg.text in ["🔍 Искать игроков", "🔍 Find players"])
async def search(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM profiles WHERE active = 1')
    count = cur.fetchone()[0]
    
    if count == 0:
        await msg.answer(t['no_profiles'])
        conn.close()
        return
    
    cur.execute('''
        SELECT user_id, username, looking_for, description, age, microphone, timezone, max_players, steam_id, avatar_path 
        FROM profiles WHERE active = 1 ORDER BY id DESC LIMIT 20
    ''')
    results = cur.fetchall()
    conn.close()
    
    sent_count = 0
    for r in results:
        user_id, username, looking_for, description, age, mic, tz, max_players, steam, avatar = r
        
        text = (
            f"👤 @{username or 'Не указан / Unknown'}\n"
            f"👥 Ищет: {looking_for}\n"
            f"🎂 Возраст: {age}\n"
            f"🎤 Микрофон: {mic}\n"
            f"🕐 Часовой пояс: {tz}\n"
            f"👥 Группа: {max_players} чел.\n"
            f"🆔 Steam: {steam}\n"
            f"📝 {description[:150]}{'...' if len(description) > 150 else ''}\n"
            f"➖➖➖➖➖"
        )
        
        fav_btn = InlineKeyboardButton(text="⭐ Избранное / Favorites", callback_data=f"fav_add_{user_id}")
        report_btn = InlineKeyboardButton(text="⚠️ Жалоба / Report", callback_data=f"report_{user_id}")
        write_btn = InlineKeyboardButton(text="💬 Написать / Write", url=f"tg://user?id={user_id}")
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [write_btn],
            [fav_btn, report_btn]
        ])
        
        if avatar and os.path.exists(avatar):
            photo = FSInputFile(avatar)
            await msg.answer_photo(photo, caption=text, reply_markup=kb)
        else:
            await msg.answer(text, reply_markup=kb)
        
        sent_count += 1
        await asyncio.sleep(0.3)
    
    await msg.answer(f"📊 Показано {sent_count} из {count} анкет / Showing {sent_count} of {count} profiles")

# ============================================
# ========== FAVORITES ==========
# ============================================

@dp.callback_query(lambda c: c.data.startswith('fav_add_'))
async def add_favorite(call: types.CallbackQuery):
    user_id = call.from_user.id
    target_id = int(call.data.split('_')[2])
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        await call.answer("Вы забанены / You are banned")
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT id FROM favorites WHERE user_id = ? AND favorite_id = ?', (user_id, target_id))
    if cur.fetchone():
        cur.execute('DELETE FROM favorites WHERE user_id = ? AND favorite_id = ?', (user_id, target_id))
        conn.commit()
        conn.close()
        await call.answer(t['favorite_removed'])
        await call.message.edit_reply_markup(reply_markup=None)
    else:
        cur.execute('INSERT INTO favorites (user_id, favorite_id, date) VALUES (?, ?, ?)',
                   (user_id, target_id, datetime.now()))
        conn.commit()
        conn.close()
        await call.answer(t['favorite_added'])

@dp.message(lambda msg: msg.text in ["⭐ Избранное / Favorites", "⭐ Избранное"])
async def show_favorites(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT p.user_id, p.username, p.looking_for, p.age, p.microphone
        FROM favorites f
        JOIN profiles p ON f.favorite_id = p.user_id
        WHERE f.user_id = ? AND p.active = 1
    ''', (user_id,))
    results = cur.fetchall()
    conn.close()
    
    if not results:
        await msg.answer("⭐ У вас нет избранных / No favorites")
        return
    
    text = "⭐ **Избранное / Favorites:**\n\n"
    for r in results:
        text += f"👤 @{r[1] or 'Unknown'}\n"
        text += f"👥 Ищет: {r[2]}\n"
        text += f"🎂 Возраст: {r[3]}\n"
        text += f"🎤 Микрофон: {r[4]}\n"
        text += f"➖➖➖➖➖\n"
    
    await msg.answer(text)

# ============================================
# ========== SWIPE SYSTEM ==========
# ============================================

@dp.message(lambda msg: msg.text in ["💕 Свайп / Swipe", "💕 Свайп"])
async def swipe_start(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT user_id, username, looking_for, age, description, microphone, avatar_path 
        FROM profiles 
        WHERE active = 1 AND user_id != ? 
        ORDER BY RANDOM() LIMIT 1
    ''', (user_id,))
    result = cur.fetchone()
    conn.close()
    
    if not result:
        await msg.answer("😕 Нет доступных анкет / No profiles available")
        return
    
    target_id, username, looking_for, age, desc, mic, avatar = result
    
    text = (
        f"👤 @{username or 'Unknown'}\n"
        f"👥 Ищет: {looking_for}\n"
        f"🎂 Возраст: {age}\n"
        f"🎤 Микрофон: {mic}\n"
        f"📝 {desc[:100]}{'...' if len(desc) > 100 else ''}\n"
        f"➖➖➖➖➖\n\n"
        f"{t['swipe_intro']}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️", callback_data=f"swipe_like_{target_id}"),
            InlineKeyboardButton(text="⛔", callback_data=f"swipe_dislike_{target_id}")
        ]
    ])
    
    if avatar and os.path.exists(avatar):
        photo = FSInputFile(avatar)
        await msg.answer_photo(photo, caption=text, reply_markup=kb)
    else:
        await msg.answer(text, reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith('swipe_'))
async def handle_swipe(call: types.CallbackQuery):
    user_id = call.from_user.id
    action, target_id = call.data.split('_')[1], int(call.data.split('_')[2])
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        await call.answer("Вы забанены / You are banned")
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO swipes (user_id, target_id, action, date) VALUES (?, ?, ?, ?)',
               (user_id, target_id, action, datetime.now()))
    conn.commit()
    conn.close()
    
    if action == 'like':
        await call.answer(t['swipe_like'])
        # Проверка взаимного лайка
        conn = sqlite3.connect('rust_clan.db')
        cur = conn.cursor()
        cur.execute('SELECT id FROM swipes WHERE user_id = ? AND target_id = ? AND action = "like"',
                   (target_id, user_id))
        mutual = cur.fetchone()
        conn.close()
        
        if mutual:
            # Получаем username
            conn = sqlite3.connect('rust_clan.db')
            cur = conn.cursor()
            cur.execute('SELECT username FROM profiles WHERE user_id = ?', (target_id,))
            result = cur.fetchone()
            conn.close()
            username = result[0] if result else "Unknown"
            
            await call.message.answer(t['swipe_match'].format(username=username))
    else:
        await call.answer(t['swipe_dislike'])
    
    await call.message.delete()
    # Показать следующую анкету
    await swipe_start(call.message)

# ============================================
# ========== CHAT ==========
# ============================================

@dp.message(lambda msg: msg.text in ["💬 Чат / Chat", "💬 Чат"])
async def chat_start(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        return
    
    await msg.answer(
        f"{t['chat_welcome']}\n\n"
        "📌 Отправляй сообщения сюда, и их увидят все.\n"
        "📌 Для ответа конкретному человеку напиши @username",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔙 Назад / Back")]],
            resize_keyboard=True
        )
    )

@dp.message(lambda msg: msg.text and not msg.text.startswith('/') and msg.text not in ["🔙 Назад / Back", "🔙 Назад"])
async def chat_message(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    
    if is_banned(user_id):
        return
    
    if msg.text in ["💬 Чат / Chat", "💬 Чат"]:
        return
    
    # Сохраняем сообщение в БД
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO chat_messages (user_id, username, message, date) VALUES (?, ?, ?, ?)',
               (user_id, msg.from_user.username or "Не указан", msg.text, datetime.now()))
    conn.commit()
    conn.close()
    
    # Отправляем сообщение всем активным пользователям
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM profiles WHERE active = 1')
    users = cur.fetchall()
    conn.close()
    
    sent_count = 0
    for u in users:
        if u[0] != user_id:
            try:
                await bot.send_message(u[0], 
                    f"💬 [{msg.from_user.username or 'Игрок'}]:\n{msg.text}\n\n"
                    f"📌 Ответить: @{msg.from_user.username or 'игрок'}")
                sent_count += 1
                await asyncio.sleep(0.05)
            except:
                pass
    
    if sent_count == 0:
        await msg.answer("💬 Сообщение сохранено, но пока никто не в сети.")

@dp.message(lambda msg: msg.text == "🔙 Назад / Back")
async def chat_back(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    await msg.answer(t['start'], reply_markup=main_menu(lang))

# ============================================
# ========== CLANS ==========
# ============================================

clan_data = {}

@dp.message(lambda msg: msg.text in ["🏰 Создать клан", "🏰 Create clan"])
async def create_clan_start(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        return
    
    # Проверяем, не состоит ли уже в клане
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT id FROM clan_members WHERE user_id = ?', (user_id,))
    if cur.fetchone():
        await msg.answer("❌ Вы уже состоите в клане. Выйдите из него, чтобы создать новый.")
        conn.close()
        return
    conn.close()
    
    clan_data[user_id] = {'step': 'name'}
    await msg.answer(t['clan_name'])

@dp.message(lambda msg: msg.from_user.id in clan_data and clan_data[msg.from_user.id].get('step') == 'name')
async def clan_name(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    clan_data[user_id]['name'] = msg.text
    clan_data[user_id]['step'] = 'tag'
    await msg.answer(t['clan_tag'])

@dp.message(lambda msg: msg.from_user.id in clan_data and clan_data[msg.from_user.id].get('step') == 'tag')
async def clan_tag(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if len(msg.text) < 2 or len(msg.text) > 4:
        await msg.answer("Тег должен быть 2-4 символа / Tag must be 2-4 characters")
        return
    
    clan_data[user_id]['tag'] = msg.text.upper()
    clan_data[user_id]['step'] = 'desc'
    await msg.answer(t['clan_desc'])

@dp.message(lambda msg: msg.from_user.id in clan_data and clan_data[msg.from_user.id].get('step') == 'desc')
async def clan_desc(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    clan_data[user_id]['desc'] = msg.text
    clan_data[user_id]['step'] = 'server'
    await msg.answer(t['clan_server'])

@dp.message(lambda msg: msg.from_user.id in clan_data and clan_data[msg.from_user.id].get('step') == 'server')
async def clan_server(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    clan_data[user_id]['server'] = msg.text
    
    # Сохраняем клан
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO clans (creator_id, name, tag, description, server, date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, clan_data[user_id]['name'], clan_data[user_id]['tag'],
          clan_data[user_id]['desc'], clan_data[user_id]['server'], datetime.now()))
    
    clan_id = cur.lastrowid
    
    # Добавляем создателя в клан
    cur.execute('INSERT INTO clan_members (clan_id, user_id, role, joined_date) VALUES (?, ?, ?, ?)',
               (clan_id, user_id, 'leader', datetime.now()))
    conn.commit()
    conn.close()
    
    await msg.answer(
        t['clan_created'].format(
            name=clan_data[user_id]['name'],
            tag=clan_data[user_id]['tag'],
            desc=clan_data[user_id]['desc'],
            server=clan_data[user_id]['server'],
            members=1,
            max=10
        ),
        reply_markup=main_menu(lang)
    )
    
    del clan_data[user_id]

@dp.message(lambda msg: msg.text in ["🏰 Мои кланы / My clans", "🏰 Мои кланы"])
async def my_clans(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT c.id, c.name, c.tag, c.description, c.server, c.members, c.max_members
        FROM clans c
        JOIN clan_members cm ON c.id = cm.clan_id
        WHERE cm.user_id = ? AND c.active = 1
    ''', (user_id,))
    results = cur.fetchall()
    conn.close()
    
    if not results:
        await msg.answer("🏰 Вы не состоите ни в одном клане / You are not in any clan")
        return
    
    text = "🏰 **Ваши кланы:**\n\n"
    for r in results:
        text += f"🏷️ {r[1]} [{r[2]}]\n"
        text += f"📝 {r[3][:100]}...\n"
        text += f"🌐 Сервер: {r[4]}\n"
        text += f"👥 Участников: {r[5]}/{r[6]}\n"
        text += f"➖➖➖➖➖\n"
    
    await msg.answer(text)

# ============================================
# ========== PROFILE MANAGEMENT ==========
# ============================================

@dp.message(lambda msg: msg.text in ["👤 Моя анкета", "👤 My profile"])
async def my_profile(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT looking_for, description, age, microphone, timezone, max_players, steam_id, avatar_path 
        FROM profiles WHERE user_id = ? AND active = 1
    ''', (user_id,))
    r = cur.fetchone()
    conn.close()
    
    if not r:
        await msg.answer("❌ У вас нет анкеты. Создайте её!")
        return
    
    text = (
        f"👤 **Ваша анкета:**\n\n"
        f"👥 Ищет: {r[0]}\n"
        f"🎂 Возраст: {r[2]}\n"
        f"🎤 Микрофон: {r[3]}\n"
        f"🕐 Часовой пояс: {r[4]}\n"
        f"👥 Группа: {r[5]} чел.\n"
        f"🆔 Steam: {r[6]}\n"
        f"📝 {r[1]}\n"
    )
    
    if r[7] and os.path.exists(r[7]):
        photo = FSInputFile(r[7])
        await msg.answer_photo(photo, caption=text)
    else:
        await msg.answer(text)

@dp.message(lambda msg: msg.text in ["🗑 Удалить анкету", "🗑 Delete profile"])
async def delete_profile(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('UPDATE profiles SET active = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    await msg.answer(t['deleted'], reply_markup=main_menu(lang))

@dp.message(lambda msg: msg.text in ["📊 Всего игроков", "📊 Total players"])
async def stats(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM profiles WHERE active = 1')
    count = cur.fetchone()[0]
    conn.close()
    await msg.answer(t['stats'].format(count=count))

# ============================================
# ========== REPORTS ==========
# ============================================

@dp.callback_query(lambda c: c.data.startswith('report_'))
async def report_user(call: types.CallbackQuery):
    user_id = call.from_user.id
    target_id = int(call.data.split('_')[1])
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    if is_banned(user_id):
        await call.answer("Вы забанены / You are banned")
        return
    
    await call.message.answer("📝 Опишите причину жалобы (кратко):")
    await call.answer()
    
    # Сохраняем временные данные
    report_data[user_id] = {'target': target_id}

report_data = {}

@dp.message(lambda msg: msg.from_user.id in report_data)
async def handle_report_reason(msg: types.Message):
    user_id = msg.from_user.id
    target_id = report_data[user_id]['target']
    reason = msg.text
    lang = get_lang(user_id)
    t = TEXTS.get(lang, TEXTS['ru'])
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO reports (reporter_id, reported_id, reason, date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, target_id, reason, datetime.now()))
    conn.commit()
    conn.close()
    
    await msg.answer(t['report_sent'])
    del report_data[user_id]
    
    # Уведомление админам и модераторам
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM moderators')
    mods = cur.fetchall()
    conn.close()
    
    for mod in mods:
        try:
            await bot.send_message(mod[0], 
                f"⚠️ **Новая жалоба!**\n"
                f"От: @{msg.from_user.username or user_id}\n"
                f"На: @{target_id}\n"
                f"Причина: {reason}\n"
                f"Используй /reports для просмотра")
        except:
            pass
    
    # Уведомление владельцу
    try:
        await bot.send_message(OWNER_ID,
            f"⚠️ **Новая жалоба!**\n"
            f"От: @{msg.from_user.username or user_id}\n"
            f"На: @{target_id}\n"
            f"Причина: {reason}\n"
            f"Используй /reports для просмотра")
    except:
        pass

# ============================================
# ========== ADMIN PANEL ==========
# ============================================

@dp.message(Command("admin"))
async def admin_panel_cmd(msg: types.Message):
    user_id = msg.from_user.id
    lang = get_lang(user_id)
    
    if not is_admin(user_id):
        await msg.answer("🚫 У вас нет доступа к админ-панели.")
        return
    
    await msg.answer(
        "🔐 **Админ-панель**\n\n"
        "Выберите действие:",
        reply_markup=admin_panel()
    )

@dp.callback_query(lambda c: c.data.startswith('admin_'))
async def admin_actions(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = get_lang(user_id)
    
    if not is_admin(user_id):
        await call.answer("🚫 Нет доступа")
        return
    
    action = call.data.split('_')[1]
    
    if action == 'stats':
        conn = sqlite3.connect('rust_clan.db')
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM profiles WHERE active = 1')
        profiles = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM clans WHERE active = 1')
        clans = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM reports WHERE resolved = 0')
        reports = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM bans')
        bans = cur.fetchone()[0]
        conn.close()
        
        await call.message.edit_text(
            f"📊 **Полная статистика**\n\n"
            f"👥 Активных анкет: {profiles}\n"
            f"🏰 Активных кланов: {clans}\n"
            f"📩 Жалоб: {reports}\n"
            f"🚫 Забанино: {bans}",
            reply_markup=admin_panel()
        )
        await call.answer()
    
    elif action == 'reports':
        conn = sqlite3.connect('rust_clan.db')
        cur = conn.cursor()
        cur.execute('''
            SELECT id, reporter_id, reported_id, reason, date 
            FROM reports WHERE resolved = 0 ORDER BY id DESC
        ''')
        results = cur.fetchall()
        conn.close()
        
        if not results:
            await call.message.edit_text(
                "📩 Нет новых жалоб.",
                reply_markup=admin_panel()
            )
            await call.answer()
            return
        
        text = "📩 **Жалобы:**\n\n"
        for r in results[:10]:
            text += f"ID: {r[0]} | От: @{r[1]} | На: @{r[2]}\n"
            text += f"Причина: {r[3]}\n"
            text += f"➖➖➖➖➖\n"
        
        text += "\nДля закрытия жалобы: /resolve <id>"
        await call.message.edit_text(text, reply_markup=admin_panel())
        await call.answer()
    
    elif action == 'moderators':
        conn = sqlite3.connect('rust_clan.db')
        cur = conn.cursor()
        cur.execute('''
            SELECT user_id, date FROM moderators ORDER BY date DESC
        ''')
        results = cur.fetchall()
        conn.close()
        
        text = "👥 **Модераторы:**\n\n"
        if results:
            for r in results:
                text += f"🆔 {r[0]} (с {r[1][:10]})\n"
        else:
            text += "Нет модераторов.\n"
        
        text += "\nНазначить: /set_moderator <user_id>\n"
        text += "Убрать: /remove_moderator <user_id>"
        await call.message.edit_text(text, reply_markup=admin_panel())
        await call.answer()
    
    elif action == 'broadcast':
        await call.message.edit_text(
            "📢 Введите текст объявления:",
            reply_markup=admin_panel()
        )
        admin_state[call.from_user.id] = {'action': 'broadcast_waiting'}
        await call.answer()
    
    elif action == 'close':
        await call.message.delete()
        await call.answer()

admin_state = {}

@dp.message(lambda msg: msg.from_user.id in admin_state and admin_state[msg.from_user.id].get('action') == 'broadcast_waiting')
async def admin_broadcast(msg: types.Message):
    user_id = msg.from_user.id
    
    if not is_admin(user_id):
        return
    
    text = msg.text
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM profiles WHERE active = 1')
    users = cur.fetchall()
    conn.close()
    
    sent = 0
    for u in users:
        try:
            await bot.send_message(u[0], f"📢 **Объявление:**\n\n{text}")
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass
    
    await msg.answer(f"✅ Объявление отправлено {sent} пользователям.")
    del admin_state[user_id]

@dp.message(Command("ban"))
async def ban_user(msg: types.Message):
    user_id = msg.from_user.id
    
    if not is_admin(user_id):
        await msg.answer("🚫 Нет доступа")
        return
    
    args = msg.text.split(' ', 2)
    if len(args) < 3:
        await msg.answer("Использование: /ban <user_id> <причина>")
        return
    
    target_id = int(args[1])
    reason = args[2]
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO bans (user_id, reason, banned_by, date) VALUES (?, ?, ?, ?)',
               (target_id, reason, user_id, datetime.now()))
    cur.execute('UPDATE profiles SET active = 0 WHERE user_id = ?', (target_id,))
    conn.commit()
    conn.close()
    
    await msg.answer(f"✅ Пользователь {target_id} забанен. Причина: {reason}")
    
    try:
        await bot.send_message(target_id, f"🚫 Вы забанены. Причина: {reason}")
    except:
        pass

@dp.message(Command("unban"))
async def unban_user(msg: types.Message):
    user_id = msg.from_user.id
    
    if not is_admin(user_id):
        await msg.answer("🚫 Нет доступа")
        return
    
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /unban <user_id>")
        return
    
    target_id = int(args[1])
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM bans WHERE user_id = ?', (target_id,))
    conn.commit()
    conn.close()
    
    await msg.answer(f"✅ Пользователь {target_id} разбанен.")

@dp.message(Command("resolve"))
async def resolve_report(msg: types.Message):
    user_id = msg.from_user.id
    
    if not is_admin(user_id):
        await msg.answer("🚫 Нет доступа")
        return
    
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /resolve <report_id>")
        return
    
    report_id = int(args[1])
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('UPDATE reports SET resolved = 1 WHERE id = ?', (report_id,))
    conn.commit()
    conn.close()
    
    await msg.answer(f"✅ Жалоба {report_id} закрыта.")

@dp.message(Command("set_moderator"))
async def set_moderator(msg: types.Message):
    user_id = msg.from_user.id
    
    if not is_admin(user_id):
        await msg.answer("🚫 Нет доступа")
        return
    
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /set_moderator <user_id>")
        return
    
    target_id = int(args[1])
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO moderators (user_id, assigned_by, date) VALUES (?, ?, ?)',
               (target_id, user_id, datetime.now()))
    conn.commit()
    conn.close()
    
    await msg.answer(f"✅ Пользователь {target_id} назначен модератором.")
    
    try:
        await bot.send_message(target_id, "🔑 Вас назначили модератором бота!")
    except:
        pass

@dp.message(Command("remove_moderator"))
async def remove_moderator(msg: types.Message):
    user_id = msg.from_user.id
    
    if not is_admin(user_id):
        await msg.answer("🚫 Нет доступа")
        return
    
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /remove_moderator <user_id>")
        return
    
    target_id = int(args[1])
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM moderators WHERE user_id = ?', (target_id,))
    conn.commit()
    conn.close()
    
    await msg.answer(f"✅ Пользователь {target_id} убран из модераторов.")

@dp.message(Command("moderators"))
async def list_moderators(msg: types.Message):
    user_id = msg.from_user.id
    
    if not is_admin(user_id):
        await msg.answer("🚫 Нет доступа")
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT user_id, date FROM moderators')
    results = cur.fetchall()
    conn.close()
    
    if not results:
        await msg.answer("👥 Модераторов нет.")
        return
    
    text = "👥 **Список модераторов:**\n\n"
    for r in results:
        text += f"🆔 {r[0]} (с {r[1][:10]})\n"
    
    await msg.answer(text)

@dp.message(Command("delete_profile"))
async def admin_delete_profile(msg: types.Message):
    user_id = msg.from_user.id
    
    if not is_admin(user_id):
        await msg.answer("🚫 Нет доступа")
        return
    
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /delete_profile <user_id>")
        return
    
    target_id = int(args[1])
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('UPDATE profiles SET active = 0 WHERE user_id = ?', (target_id,))
    conn.commit()
    conn.close()
    
    await msg.answer(f"✅ Анкета пользователя {target_id} удалена.")

@dp.message(Command("stats_full"))
async def full_stats(msg: types.Message):
    user_id = msg.from_user.id
    
    if not is_admin(user_id):
        await msg.answer("🚫 Нет доступа")
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM profiles WHERE active = 1')
    profiles = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM profiles')
    total_profiles = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM clans WHERE active = 1')
    clans = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM reports WHERE resolved = 0')
    reports = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM bans')
    bans = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM moderators')
    moderators = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM chat_messages')
    messages = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM swipes')
    swipes = cur.fetchone()[0]
    
    conn.close()
    
    await msg.answer(
        f"📊 **Полная статистика бота**\n\n"
        f"👥 Активных анкет: {profiles}\n"
        f"📝 Всего анкет: {total_profiles}\n"
        f"🏰 Активных кланов: {clans}\n"
        f"📩 Жалоб: {reports}\n"
        f"🚫 Забанино: {bans}\n"
        f"👮 Модераторов: {moderators}\n"
        f"💬 Сообщений в чате: {messages}\n"
        f"💕 Свайпов: {swipes}"
    )

# ============================================
# ========== MAIN ==========
# ============================================

async def main():
    os.makedirs("avatars", exist_ok=True)
    print("🤖 Бот RUST LFG Bot v7.0 запущен!")
    print(f"👑 Владелец: {OWNER_ID}")
    print("📱 Напишите /start в Telegram")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
