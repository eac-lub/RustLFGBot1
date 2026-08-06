# FORCE_REDEPLOY_3 - новая структура анкеты

import os
import asyncio
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram import F

# ===== ТОКЕН =====
TOKEN = "8804113008:AAGgdo_FZMDoWr2C0SBChjo4-HMRiEog-D4"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            looking_for TEXT,
            description TEXT,
            steam_id TEXT,
            avatar_path TEXT,
            date TEXT,
            active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ===== КЛАВИАТУРА ГЛАВНОГО МЕНЮ =====
def main_menu():
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="📝 Создать анкету"),
                types.KeyboardButton(text="🔍 Искать игроков")
            ],
            [
                types.KeyboardButton(text="👤 Моя анкета"),
                types.KeyboardButton(text="🗑 Удалить анкету")
            ],
            [
                types.KeyboardButton(text="📊 Всего игроков")
            ]
        ],
        resize_keyboard=True
    )
    return kb

# ===== INLINE-КНОПКИ: ВЫБОР ЦЕЛИ =====
def looking_buttons():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤝 Ищу тиммейта(ов)", callback_data="looking_timmeit"),
            InlineKeyboardButton(text="🔍 Ищу клан", callback_data="looking_clan")
        ],
        [
            InlineKeyboardButton(text="🏰 Ищем игроков в клан", callback_data="looking_clan_search")
        ]
    ])
    return kb

# ===== ХРАНИЛИЩЕ ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ =====
user_data = {}

# ===== КОМАНДА START =====
@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer(
        "🦀 Добро пожаловать в бот для поиска кланов в RUST!\n\n"
        "Здесь вы можете:\n"
        "✅ Создать анкету\n"
        "✅ Найти тиммейтов и кланы\n"
        "✅ Просматривать анкеты других игроков\n\n"
        "Выберите действие:",
        reply_markup=main_menu()
    )

# ===== СОЗДАНИЕ АНКЕТЫ - ШАГ 1 =====
@dp.message(F.text == "📝 Создать анкету")
async def create_start(msg: types.Message):
    await msg.answer(
        "👥 **Кого вы ищете?**\n\n"
        "Выберите один из вариантов:",
        reply_markup=looking_buttons()
    )

# ===== ОБРАБОТЧИК INLINE-КНОПОК =====
@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    data = call.data
    
    # Инициализируем данные пользователя, если их нет
    if user_id not in user_data:
        user_data[user_id] = {}
    
    if data == "looking_timmeit":
        user_data[user_id]['looking_for'] = "тиммейта(ов)"
        await call.message.edit_text(
            "🤝 **Вы ищете тиммейта(ов)**\n\n"
            "📝 **Расскажи о себе:**\n"
            "— Какой у тебя стиль игры?\n"
            "— Сколько часов в RUST?\n"
            "— Есть ли микрофон?\n"
            "— Когда обычно играешь?\n\n"
            "Напиши подробно:"
        )
        
    elif data == "looking_clan":
        user_data[user_id]['looking_for'] = "клан"
        await call.message.edit_text(
            "🔍 **Вы ищете клан**\n\n"
            "📝 **Расскажи о себе:**\n"
            "— Сколько часов в RUST?\n"
            "— Что умеешь (строить/фармить/ПВП)?\n"
            "— Что ищешь в клане?\n\n"
            "Напиши подробно:"
        )
        
    elif data == "looking_clan_search":
        user_data[user_id]['looking_for'] = "игроков в клан"
        await call.message.edit_text(
            "🏰 **Вы ищете игроков в клан**\n\n"
            "📝 **Расскажи о своём клане:**\n"
            "— Название клана?\n"
            "— Сколько человек в клане?\n"
            "— На каком сервере играете?\n"
            "— Какие требования к игрокам?\n\n"
            "Напиши подробно:"
        )
    
    # Устанавливаем следующий шаг
    user_data[user_id]['step'] = 'description'
    await call.answer()

# ===== ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ =====
@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get('step') == 'description')
async def handle_description(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]['description'] = msg.text
    user_data[user_id]['step'] = 'steam'
    
    await msg.answer(
        "🆔 **Теперь укажи свой Steam ID**\n\n"
        "Введи свой Steam ID или код дружбы.\n"
        "Если нет — напиши '-'",
        reply_markup=main_menu()
    )

# ===== ОБРАБОТЧИК STEAM ID =====
@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get('step') == 'steam')
async def handle_steam(msg: types.Message):
    user_id = msg.from_user.id
    user_data[user_id]['steam_id'] = msg.text
    user_data[user_id]['step'] = 'avatar'
    
    await msg.answer(
        "📸 **Отправь своё ФОТО** (аватарку)\n\n"
        "Просто отправь фото.\n"
        "Или нажми '-' чтобы пропустить:",
        reply_markup=main_menu()
    )

# ===== ОБРАБОТЧИК ФОТО =====
@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get('step') == 'avatar')
async def handle_avatar(msg: types.Message):
    user_id = msg.from_user.id
    data = user_data[user_id]
    
    # Проверяем, что это фото или команда пропуска
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
        await msg.answer("❌ Отправь фото или нажми '-' чтобы пропустить")

# ===== СОХРАНЕНИЕ АНКЕТЫ =====
async def save_profile(msg: types.Message):
    user_id = msg.from_user.id
    data = user_data[user_id]
    
    # Проверяем, что все данные есть
    if 'looking_for' not in data or 'description' not in data:
        await msg.answer("❌ Ошибка! Попробуй создать анкету заново.")
        del user_data[user_id]
        return
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO profiles 
        (user_id, username, looking_for, description, steam_id, avatar_path, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, 
        msg.from_user.username or "Не указан",
        data['looking_for'],
        data['description'],
        data.get('steam_id', 'Не указан'),
        data.get('avatar_path'),
        datetime.now()
    ))
    conn.commit()
    conn.close()
    
    # Показываем готовую анкету
    avatar_text = "✅ Есть" if data.get('avatar_path') else "❌ Нет"
    
    await msg.answer(
        f"✅ **Анкета создана!**\n\n"
        f"👥 Ищет: {data['looking_for']}\n"
        f"📝 О себе: {data['description']}\n"
        f"🆔 Steam ID: {data.get('steam_id', 'Не указан')}\n"
        f"📸 Аватар: {avatar_text}\n\n"
        "Теперь вас могут найти!",
        reply_markup=main_menu()
    )
    
    # Отправляем фото если есть
    if data.get('avatar_path'):
        photo = FSInputFile(data['avatar_path'])
        await msg.answer_photo(photo, caption="📸 Ваша аватарка")
    
    # Удаляем данные пользователя
    del user_data[user_id]

# ===== ПОИСК ИГРОКОВ =====
@dp.message(F.text == "🔍 Искать игроков")
async def search(msg: types.Message):
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT user_id, username, looking_for, description, steam_id, avatar_path 
        FROM profiles WHERE active = 1 LIMIT 20
    ''')
    results = cur.fetchall()
    conn.close()
    
    if not results:
        await msg.answer("😕 Пока никого нет. Создайте анкету!")
        return
    
    for r in results:
        user_id, username, looking_for, description, steam_id, avatar = r
        
        text = (
            f"👤 @{username}\n"
            f"👥 Ищет: {looking_for}\n"
            f"📝 {description}\n"
            f"🆔 Steam: {steam_id}\n"
            f"➖➖➖➖➖"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("💬 Написать", url=f"tg://user?id={user_id}")]
        ])
        
        if avatar and os.path.exists(avatar):
            photo = FSInputFile(avatar)
            await msg.answer_photo(photo, caption=text, reply_markup=kb)
        else:
            await msg.answer(text, reply_markup=kb)

# ===== МОЯ АНКЕТА =====
@dp.message(F.text == "👤 Моя анкета")
async def my(msg: types.Message):
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT looking_for, description, steam_id, avatar_path 
        FROM profiles WHERE user_id = ? AND active = 1
    ''', (msg.from_user.id,))
    r = cur.fetchone()
    conn.close()
    
    if not r:
        await msg.answer("❌ У вас нет анкеты. Создайте её!")
        return
    
    text = (
        f"👤 **Ваша анкета:**\n\n"
        f"👥 Ищет: {r[0]}\n"
        f"📝 {r[1]}\n"
        f"🆔 Steam: {r[2]}\n"
    )
    
    if r[3] and os.path.exists(r[3]):
        photo = FSInputFile(r[3])
        await msg.answer_photo(photo, caption=text)
    else:
        await msg.answer(text)

# ===== УДАЛИТЬ АНКЕТУ =====
@dp.message(F.text == "🗑 Удалить анкету")
async def delete(msg: types.Message):
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('UPDATE profiles SET active = 0 WHERE user_id = ?', (msg.from_user.id,))
    conn.commit()
    conn.close()
    await msg.answer("✅ Анкета удалена", reply_markup=main_menu())

# ===== СТАТИСТИКА =====
@dp.message(F.text == "📊 Всего игроков")
async def stats(msg: types.Message):
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM profiles WHERE active = 1')
    count = cur.fetchone()[0]
    conn.close()
    await msg.answer(f"📊 Всего активных игроков: **{count}**")

# ===== ЗАПУСК =====
async def main():
    os.makedirs("avatars", exist_ok=True)
    print("🤖 Бот RUST Clan Finder запущен!")
    print("📱 Напишите /start в Telegram")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
