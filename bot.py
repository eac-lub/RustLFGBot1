# FORCE_REDEPLOY_2 - принудительное обновление для Railway

import os
import asyncio
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram import F

# ===== ТОКЕН ВСТАВЛЕН ПРЯМО В КОД =====
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
            role TEXT,
            rank TEXT,
            looking TEXT,
            steam_id TEXT,
            avatar_path TEXT,
            description TEXT,
            date TEXT,
            active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ===== КЛАВИАТУРА (ИСПРАВЛЕННАЯ) =====
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

user_data = {}

# ===== КОМАНДА START =====
@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer(
        "🦀 Добро пожаловать в бот для поиска кланов в RUST!\n\n"
        "Здесь вы можете:\n"
        "✅ Создать анкету с фото и Steam ID\n"
        "✅ Найти тиммейтов и кланы\n"
        "✅ Просматривать анкеты других игроков\n\n"
        "Выберите действие:",
        reply_markup=main_menu()
    )

# ===== СОЗДАНИЕ АНКЕТЫ =====
@dp.message(F.text == "📝 Создать анкету")
async def create_start(msg: types.Message):
    user_data[msg.from_user.id] = {'step': 'role'}
    await msg.answer(
        "📝 **Создание анкеты**\n\n"
        "Шаг 1 из 5: Укажите вашу **РОЛЬ**\n"
        "Примеры: ПВП, Строитель, Фармер, Рейдер, Универсал"
    )

@dp.message(lambda msg: msg.from_user.id in user_data)
async def create_steps(msg: types.Message):
    user_id = msg.from_user.id
    data = user_data[user_id]
    step = data.get('step')
    
    if step == 'role':
        data['role'] = msg.text
        data['step'] = 'rank'
        await msg.answer("Шаг 2 из 5: Укажите ваш **РАНГ/ОПЫТ**\nПримеры: Новичок, Средний, Профи, Ветеран")
    
    elif step == 'rank':
        data['rank'] = msg.text
        data['step'] = 'looking'
        await msg.answer("Шаг 3 из 5: Кого вы **ИЩЕТЕ**?\nПримеры: Клан, Тиммейтов, Сквад, Пати")
    
    elif step == 'looking':
        data['looking'] = msg.text
        data['step'] = 'steam'
        await msg.answer("Шаг 4 из 5: Ваш **STEAM ID** (или '-' если нет)")
    
    elif step == 'steam':
        data['steam'] = msg.text
        data['step'] = 'avatar'
        await msg.answer("Шаг 5 из 5: Отправьте **ФОТО** (или '-' чтобы пропустить)")
    
    elif step == 'avatar':
        if msg.text and msg.text == '-':
            data['avatar'] = None
            await save_profile(msg)
        elif msg.photo:
            file = await bot.get_file(msg.photo[-1].file_id)
            file_path = f"avatars/{user_id}.jpg"
            os.makedirs("avatars", exist_ok=True)
            await bot.download_file(file.file_path, file_path)
            data['avatar'] = file_path
            await save_profile(msg)
        else:
            await msg.answer("❌ Отправьте фото или нажмите '-'")

async def save_profile(msg: types.Message):
    user_id = msg.from_user.id
    data = user_data[user_id]
    
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO profiles 
        (user_id, username, role, rank, looking, steam_id, avatar_path, description, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, msg.from_user.username or "Не указан", 
          data['role'], data['rank'], data['looking'], 
          data['steam'], data.get('avatar'), "Игрок RUST", datetime.now()))
    conn.commit()
    conn.close()
    
    avatar_text = "✅ Есть" if data.get('avatar') else "❌ Нет"
    
    await msg.answer(
        f"✅ **Анкета создана!**\n\n"
        f"🎯 Роль: {data['role']}\n"
        f"⭐ Ранг: {data['rank']}\n"
        f"🔎 Ищет: {data['looking']}\n"
        f"🆔 Steam: {data['steam']}\n"
        f"📸 Аватар: {avatar_text}\n\n"
        "Теперь вас могут найти!",
        reply_markup=main_menu()
    )
    
    if data.get('avatar'):
        photo = FSInputFile(data['avatar'])
        await msg.answer_photo(photo, caption="📸 Ваша аватарка")
    
    del user_data[user_id]

# ===== ПОИСК ИГРОКОВ =====
@dp.message(F.text == "🔍 Искать игроков")
async def search(msg: types.Message):
    conn = sqlite3.connect('rust_clan.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT user_id, username, role, rank, looking, steam_id, avatar_path 
        FROM profiles WHERE active = 1 LIMIT 20
    ''')
    results = cur.fetchall()
    conn.close()
    
    if not results:
        await msg.answer("😕 Пока никого нет. Создайте анкету!")
        return
    
    for r in results:
        user_id, username, role, rank, looking, steam, avatar = r
        
        text = (
            f"👤 @{username}\n"
            f"🎯 Роль: {role}\n"
            f"⭐ Ранг: {rank}\n"
            f"🔎 Ищет: {looking}\n"
            f"🆔 Steam: {steam}\n"
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
        SELECT role, rank, looking, steam_id, avatar_path 
        FROM profiles WHERE user_id = ? AND active = 1
    ''', (msg.from_user.id,))
    r = cur.fetchone()
    conn.close()
    
    if not r:
        await msg.answer("❌ У вас нет анкеты. Создайте её!")
        return
    
    text = (
        f"👤 **Ваша анкета:**\n\n"
        f"🎯 Роль: {r[0]}\n"
        f"⭐ Ранг: {r[1]}\n"
        f"🔎 Ищет: {r[2]}\n"
        f"🆔 Steam: {r[3]}\n"
    )
    
    if r[4] and os.path.exists(r[4]):
        photo = FSInputFile(r[4])
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