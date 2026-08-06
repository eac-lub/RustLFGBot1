# ================== PROFILE CREATION ==================
@dp.message(F.text == "📝 Создать анкету")
async def create_profile_start(msg: types.Message):
    user_id = msg.from_user.id
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM profiles WHERE user_id = ? AND active = 1 AND looking_for IS NOT NULL", (user_id,))
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

    # ========== 1. Ищу тиммейта ==========
    if path == "teammate":
        user_data[user_id]["step"] = "tm_experience"
        await msg.answer(
            "⚔️ <b>Ищешь тиммейта</b>\n\n"
            "Сколько примерно часов у тебя в Rust?\n"
            "(или сколько вайпов отыграл)",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

    # ========== 2. Ищу клан ==========
    elif path == "looking_clan":
        user_data[user_id]["step"] = "lc_experience"
        await msg.answer(
            "🏰 <b>Ищешь клан</b>\n\n"
            "Сколько примерно часов / вайпов у тебя в игре?",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

    # ========== 3. Набираю в клан ==========
    elif path == "recruiting":
        user_data[user_id]["step"] = "rec_name"
        await msg.answer(
            "📢 <b>Набираешь игроков в клан</b>\n\n"
            "Напиши <b>название клана</b>:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

    # ========== 4. Просто поиграть ==========
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


# ================== ПУТЬ 1: Ищу тиммейта ==================
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


# ================== ПУТЬ 2: Ищу клан ==================
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


# ================== ПУТЬ 3: Набираю в клан ==================
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


# ================== ПУТЬ 4: Просто поиграть ==================
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
