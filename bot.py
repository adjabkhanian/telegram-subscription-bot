import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
import aiosqlite
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, FSInputFile

TOKEN = "7018906512:AAGkf9ugaxGh8qS18QBhpV-BP47aPqrnt9A"
ADMIN_ID = 7029037184
GROUP_ID = -1002858230612
ADMINS = [7029037184, 1391901108]  # список Telegram ID админов

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

class SubscribeSteps(StatesGroup):
    choosing_period = State()
    getting_email = State()
    getting_fullname = State()
    getting_phone = State()
    getting_city = State()
    waiting_payment = State()
    admin_cancel = State()
    admin_search = State()
    admin_broadcast = State()
    admin_manual_add_id = State()
    admin_manual_add_username = State()
    admin_manual_add_days = State()

async def get_main_menu_kb(user_id: int):
    buttons = [
        [KeyboardButton(text="ℹ️ Информация о курсе")],
        [KeyboardButton(text="💳 Оформить подписку")],
        [KeyboardButton(text="👤 Личный кабинет")]
    ]
    if user_id in ADMINS:
        buttons.append([KeyboardButton(text="🛠️ Админ-меню")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

period_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 мес 1.344 руб."),
         KeyboardButton(text="3 мес 3.744 руб.")],
        [KeyboardButton(text="6 мес 6.994 руб."),
         KeyboardButton(text="12 мес +мес. подарок 13.444 руб.")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⬅️ Назад")]],
    resize_keyboard=True
)

admin_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Список подписчиков")],
        [KeyboardButton(text="🔄 Аннулировать подписку")],
        [KeyboardButton(text="🔍 Найти подписчика по username")],
        [KeyboardButton(text="📤 Уведомить всех подписчиков")],
        [KeyboardButton(text="➕ Добавить подписчика вручную")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)
@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    video_note = FSInputFile("video_note.mp4")  # Укажи путь к видео файлу

    # Отправляем video_note (круглое видео-сообщение)
    await bot.send_video_note(chat_id=message.chat.id, video_note=video_note)

    # Отправляем кнопку "Далее"
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Далее ➡️")]], resize_keyboard=True)
    await message.answer("Нажмите 'Далее', чтобы продолжить.", reply_markup=kb)

@dp.message(F.text == "Далее ➡️")
async def send_intro(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подробнее об обучении")],
            [KeyboardButton(text="Хочу в клуб")]
        ],
        resize_keyboard=True
    )

    photo = FSInputFile("aysha_photo.jpg")  # Укажи путь к фото

    text = (
        "Айша Эскерханова - Религиозный учитель\n\n"
        "✅ 15 лет преподавания ислама: Санкт-Петербург, Ярославль, Грозный, Ингушетия, Дагестан и другие;\n"
        "✅ Окончила Исламский техникум, обучаюсь в Исламском университете имени Кунта-Хаджи (Грозный), обучалась у шейхов\n"
        "✅ Обучила более 10.000 женщин и детей из разных стран, 100+ приняли Ислам\n\n"
        "Клуб «Диалог Истины» — место, где вы получите полноценное обучение во всех сферах необходимых для жизни:\n"
        "✅ Фард знания\n"
        "✅ Семья. Обязанности мужа и жены.\n"
        "✅ Воспитание детей;\n"
        "✅ Женские темы: месячные, роды и после родов, хиджаб, косметика;\n"
        "✅ Торговые отношения, закят;\n"
        "✅ Хадж\n\n"
        "Формат обучения:\n"
        "📍 После подписки вам открывается доступ на GetCourse, где в свободном доступе сразу начинаете самостоятельно учиться.\n"
        "📍 Попадаете на канал в телеграмме, где можно общаться со всеми учениками;\n"
        "📍 В течение месяца проводятся прямые эфиры на самые актуальные темы\n\n"
        "🕌 С каждой подписки мы откладываем 30% в копилку на строительство мечети. Каждый из вас может стать частью этого благого дела!"
    )

    await message.answer_photo(photo=photo, caption=text, reply_markup=kb)

@dp.message(F.text == "Подробнее об обучении")
async def send_details_link(message: Message):
    DETAILS_URL = "https://dialogistini.ru/iclub"  # Здесь замени на свою ссылку
    await message.answer(f"Подробнее об обучении смотрите здесь:\n{DETAILS_URL}")

@dp.message(F.text == "Хочу в клуб")
async def start_subscription(message: Message, state: FSMContext):
    # Здесь вызывается твоя существующая функция для оформления подписки
    await subscribe(message, state)

@dp.message(F.text == "ℹ️ Информация о курсе")
async def info_course(message: Message):
    kb = await get_main_menu_kb(message.from_user.id)
    await message.answer("Здесь подробно рассказывается про курс...\n\nЧтобы оформить подписку нажмите кнопку 'Оформить подписку'.", reply_markup=kb)

@dp.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    kb = await get_main_menu_kb(message.from_user.id)
    await message.answer("Вы вернулись в главное меню.", reply_markup=kb)

@dp.message(F.text == "💳 Оформить подписку")
async def subscribe(message: Message, state: FSMContext):
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT end_date FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            end_date = None
            if row and row[0]:
                try:
                    end_date = datetime.fromisoformat(str(row[0]))
                except Exception:
                    pass

            if end_date and end_date > datetime.now():
                days_left = (end_date - datetime.now()).days
                kb = await get_main_menu_kb(message.from_user.id)
                await message.answer(
                    f"У вас уже есть активная подписка, осталось {days_left} дней.\n\nВ Личном кабинете вы можете посмотреть детали.",
                    reply_markup=kb
                )
                return

    await message.answer("⏳ На сколько месяцев оформить подписку?", reply_markup=period_kb)
    await state.set_state(SubscribeSteps.choosing_period)

@dp.message(SubscribeSteps.choosing_period)
async def get_period(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        kb = await get_main_menu_kb(message.from_user.id)
        await message.answer("Отменено. Возврат в главное меню.", reply_markup=kb)
        return
    period = message.text
    if period not in ["1 мес 1.344 руб.", "3 мес 3.744 руб.", "6 мес 6.994 руб.", "12 мес +мес. подарок 13.444 руб."]:
        await message.answer("Пожалуйста, выберите период из кнопок.", reply_markup=period_kb)
        return
    await state.update_data(period=period)
    await message.answer("📧 Введите ваш email:", reply_markup=cancel_kb)
    await state.set_state(SubscribeSteps.getting_email)

@dp.message(SubscribeSteps.getting_email)
async def get_email(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        kb = await get_main_menu_kb(message.from_user.id)
        await message.answer("Отменено. Возврат в главное меню.", reply_markup=kb)
        return
    email = message.text.strip()
    await state.update_data(email=email)
    await message.answer("✍️ Введите ваше <b>ФИО</b>:", reply_markup=cancel_kb)
    await state.set_state(SubscribeSteps.getting_fullname)

@dp.message(SubscribeSteps.getting_fullname)
async def get_fullname(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        kb = await get_main_menu_kb(message.from_user.id)
        await message.answer("Отменено. Возврат в главное меню.", reply_markup=kb)
        return
    fullname = message.text.strip()
    await state.update_data(fullname=fullname)
    await message.answer("📱 Введите ваш <b>номер телефона</b>:", reply_markup=cancel_kb)
    await state.set_state(SubscribeSteps.getting_phone)

@dp.message(SubscribeSteps.getting_phone)
async def get_phone(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        kb = await get_main_menu_kb(message.from_user.id)
        await message.answer("Отменено. Возврат в главное меню.", reply_markup=kb)
        return
    phone = message.text.strip()
    await state.update_data(phone=phone)
    data = await state.get_data()
    period = data["period"]
    await state.update_data(phone=phone)
    await message.answer("🏙️ Введите ваш <b>город</b>:", reply_markup=cancel_kb)
    await state.set_state(SubscribeSteps.getting_city)

@dp.message(SubscribeSteps.getting_city)
async def get_city(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        kb = await get_main_menu_kb(message.from_user.id)
        await message.answer("Отменено. Возврат в главное меню.", reply_markup=kb)
        return
    city = message.text.strip()
    await state.update_data(city=city)

    data = await state.get_data()
    period = data["period"]
    await message.answer(f"""✅ Отлично!
Переведите <b>{get_price(period)}₽</b> на карту:

<code>2204 3203 6606 1564 (Озон банк, Алёна Александровна Добыко)</code>

После оплаты пришлите сюда скриншот чека.
""", reply_markup=cancel_kb)
    await state.set_state(SubscribeSteps.waiting_payment)

@dp.message(SubscribeSteps.waiting_payment, F.photo)
async def handle_payment(message: Message, state: FSMContext):
    data = await state.get_data()
    username = message.from_user.username or message.from_user.full_name
    kb = await get_main_menu_kb(message.from_user.id)
    await message.answer("⏳ Ожидайте подтверждение от администратора.", reply_markup=kb)
    for admin_id in ADMINS:
        try:
            await bot.send_photo(
    admin_id,
    photo=message.photo[-1].file_id,
    caption=f"""💸 Новый платёж:

👤 @{username}
🆔 {message.from_user.id}
📧 {data['email']}
🪪 ФИО: {data['fullname']}
📞 Телефон: {data['phone']}
🏙️ Город: {data['city']}
📆 Подписка: {data['period']}
""",
    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Одобрить",
                callback_data=f"approve:{message.from_user.id}|{data['period']}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"deny:{message.from_user.id}"
            )
        ]
    ])
)
        except Exception as e:
            print(f"Ошибка отправки админу {admin_id}: {e}")

        # Сохраняем введённые данные временно в БД до подтверждения
    async with aiosqlite.connect("users.db") as db:
        await db.execute(
            "REPLACE INTO users (user_id, end_date, username, email, fullname, phone, city) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                message.from_user.id,
                "",  # пустой срок окончания — пока не подтверждено
                username,
                data['email'],
                data['fullname'],
                data['phone'],
                data['city']
            )
        )
        await db.commit()

    await state.clear()


@dp.message(F.text.startswith("/approve_"))
async def approve_payment(message: Message):
    if message.from_user.id not in ADMINS:
        return

    parts = message.text.split("_")
    user_id = int(parts[1])
    period_text = "_".join(parts[2:])
    months = get_months_by_text(period_text)

    approver_name = message.from_user.full_name

    try:
        user = await bot.get_chat(user_id)
        username = user.username or user.full_name
    except Exception:
        username = ""

    now = datetime.now()

    async with aiosqlite.connect("users.db") as db:
        # Безопасно получаем end_date
        async with db.execute("SELECT end_date FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:  # Проверяем, что строка не пустая
                try:
                    current_end = datetime.fromisoformat(row[0])
                except ValueError:
                    current_end = None
            else:
                current_end = None

        # Рассчитываем новую дату окончания
        if current_end > now:
            new_end = current_end + timedelta(days=30 * months)
        else:
            new_end = now + timedelta(days=30 * months)

        # Обновляем или добавляем пользователя
        await db.execute(
            "REPLACE INTO users (user_id, end_date, username) VALUES (?, ?, ?)",
            (user_id, new_end.isoformat(), username)
        )
        await db.commit()

    # Разбан
    try:
        await bot.unban_chat_member(GROUP_ID, user_id)
    except Exception as e:
        print(f"⚠️ Не удалось разбанить пользователя {user_id}: {e}")

    # Ссылка-приглашение
    try:
        invite_link = await bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            name=f"Link for {user_id}",
            expire_date=datetime.now() + timedelta(days=1),
            member_limit=1
        )
    except Exception as e:
        await bot.send_message(user_id, "❗ Ошибка при создании ссылки. Обратитесь к администратору.")
        await bot.send_message(ADMIN_ID, f"Ошибка при создании ссылки для пользователя {user_id}: {e}")
        return

    # Отправка пользователю
    try:
        await bot.send_message(
            user_id,
            f"✅ Оплата подтверждена администратором <b>{approver_name}</b>!\n"
            f"Вот ваша ссылка на группу:\n{invite_link.invite_link}",
            parse_mode="HTML"
        )
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"Ошибка при отправке ссылки пользователю {user_id}: {e}")

    # Уведомление другим админам
    for admin_id in ADMINS:
        if admin_id != message.from_user.id:
            try:
                await bot.send_message(
                    admin_id,
                    f"✅ Подписка подтверждена админом <b>{approver_name}</b> для ID {user_id}",
                    parse_mode="HTML"
                )
            except Exception:
                pass

@dp.message(F.text.startswith("/deny_"))
async def deny_payment(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_id = int(message.text.split("_")[1])
    kb = await get_main_menu_kb(user_id)
    await bot.send_message(user_id, "❌ Оплата не подтверждена. Попробуйте снова.", reply_markup=kb)

@dp.message(F.text == "👤 Личный кабинет")
async def profile(message: Message):
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT end_date FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            kb = await get_main_menu_kb(message.from_user.id)
            if row:
                end_date = datetime.fromisoformat(row[0])
                now = datetime.now()
                if end_date > now:
                    days_left = (end_date - now).days
                    await message.answer(f"👤 <b>Ваш профиль</b>\nПодписка до: {end_date.strftime('%d.%m.%Y')}\nОсталось дней: {days_left}", reply_markup=kb)
                else:
                    await message.answer("Ваша подписка истекла. Оформите новую подписку.", reply_markup=kb)
            else:
                await message.answer("У вас нет активной подписки. Оформите подписку.", reply_markup=kb)

@dp.message(F.text == "🛠️ Админ-меню")
async def admin_menu(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await state.clear()
    await message.answer("Вы в админ-меню. Выберите действие.", reply_markup=admin_menu_kb)

@dp.message(F.text == "📋 Список подписчиков")
async def list_subscribers(message: Message):
    if message.from_user.id not in ADMINS:
        return
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT user_id, end_date, username, email, fullname, phone, city FROM users ORDER BY end_date DESC") as cursor:
            rows = await cursor.fetchall()
            if not rows:
                await message.answer("Подписчиков пока нет.", reply_markup=admin_menu_kb)
                return
            text = "<b>Список подписчиков:</b>\n\n"
            for user_id, end_date_str, username, email, fullname, phone, city in rows:
                username_display = f"@{username}" if username else "(без username)"
                text += (
                    f"<b>{username_display}</b> — ID: <code>{user_id}</code>\n"
                    f"📧 Email: {email or '-'}\n"
                    f"🪪 ФИО: {fullname or '-'}\n"
                    f"📞 Телефон: {phone or '-'}\n"
                    f"🏙️ Город: {city or '-'}\n"
                    f"📆 До: {datetime.fromisoformat(end_date_str).strftime('%d.%m.%Y')}\n\n"
                )
                if len(text) > 3500:
                    await message.answer(text, parse_mode="HTML")
                    text = ""
            if text:
                await message.answer(text, reply_markup=admin_menu_kb, parse_mode="HTML")

@dp.message(F.text == "🔄 Аннулировать подписку")
async def cancel_subscribe_start(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await state.set_state(SubscribeSteps.admin_cancel)
    await message.answer("Введите ID пользователя для аннулирования подписки.\nДля отмены введите 'отмена'.")

@dp.message(SubscribeSteps.admin_cancel)
async def cancel_subscribe_process(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Отмена аннулирования.", reply_markup=admin_menu_kb)
        return
    try:
        user_id = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный числовой ID или 'отмена'.")
        return
    async with aiosqlite.connect("users.db") as db:
        await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await db.commit()
    await bot.ban_chat_member(GROUP_ID, user_id)
    await message.answer(f"Подписка пользователя {user_id} аннулирована и он исключён из группы.", reply_markup=admin_menu_kb)
    await state.clear()

@dp.message(F.text == "📤 Уведомить всех подписчиков")
async def notify_all_subscribers(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("Напишите текст сообщения, которое будет отправлено всем подписчикам:")
    await state.set_state(SubscribeSteps.admin_broadcast)

@dp.message(SubscribeSteps.admin_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    text = message.text
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            success, failed = 0, 0
            for (user_id,) in rows:
                try:
                    await bot.send_message(user_id, f"📢 {text}")
                    success += 1
                except:
                    failed += 1
    await message.answer(f"📬 Рассылка завершена.\n✅ Успешно: {success}\n❌ Ошибок: {failed}")
    await state.clear()

@dp.message(F.text == "🔍 Найти подписчика по username")
async def start_search_username(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("Введите username пользователя без @:")
    await state.set_state(SubscribeSteps.admin_search)

@dp.message(SubscribeSteps.admin_search)
async def process_search_username(message: Message, state: FSMContext):
    username_to_find = message.text.lower().strip().lstrip("@")
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT user_id, end_date, username FROM users WHERE LOWER(username) = ?", (username_to_find,)) as cursor:
            row = await cursor.fetchone()
            if row:
                user_id, end_date, username = row
                await message.answer(f"👤 Найден пользователь @{username}:\nID: {user_id}\nПодписка до: {end_date}")
            else:
                await message.answer("Пользователь не найден.")
    await state.clear()

@dp.message(F.text == "➕ Добавить подписчика вручную")
async def admin_manual_add_start(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await state.set_state(SubscribeSteps.admin_manual_add_id)
    await message.answer("Введите Telegram ID пользователя для добавления подписки.\nДля отмены введите 'отмена'.")

@dp.message(SubscribeSteps.admin_manual_add_id)
async def manual_add_id(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Добавление отменено.", reply_markup=admin_menu_kb)
        return
    try:
        user_id = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный числовой Telegram ID.")
        return
    await state.update_data(manual_user_id=user_id)
    await state.set_state(SubscribeSteps.admin_manual_add_username)
    await message.answer("Введите username пользователя (без @) или 'нет', если его нет.")

@dp.message(SubscribeSteps.admin_manual_add_username)
async def manual_add_username(message: Message, state: FSMContext):
    username = message.text.strip().lower()
    if username == "отмена":
        await state.clear()
        await message.answer("Добавление отменено.", reply_markup=admin_menu_kb)
        return
    if username == "нет":
        username = ""
    await state.update_data(manual_username=username)
    await state.set_state(SubscribeSteps.admin_manual_add_days)
    await message.answer("Введите период подписки в днях (целое число, например, 28).")

@dp.message(SubscribeSteps.admin_manual_add_days)
async def manual_add_days(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Добавление отменено.", reply_markup=admin_menu_kb)
        return
    try:
        days = int(message.text)
        if days <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число дней (целое положительное число).")
        return

    data = await state.get_data()
    user_id = data.get("manual_user_id")
    username = data.get("manual_username")
    now = datetime.now()
    new_end = now + timedelta(days=days)

    # Загружаем старые данные, если они есть
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT email, fullname, phone, city FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            email, fullname, phone, city = ("", "", "", "")
            if row:
                email, fullname, phone, city = row

        await db.execute(
            "REPLACE INTO users (user_id, end_date, username, email, fullname, phone, city) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                new_end.isoformat(),
                username,
                email,
                fullname,
                phone,
                city
            )
        )
        await db.commit()

    try:
        await bot.unban_chat_member(GROUP_ID, user_id)
    except Exception as e:
        print(f"unban error: {e}")

    try:
        invite_link = await bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            name=f"Manual link for {user_id}",
            expire_date=int((datetime.now() + timedelta(days=days)).timestamp()),
            member_limit=1
        )
        await bot.send_message(
            user_id,
            f"✅ Ваша подписка добавлена вручную.\n"
            f"Подписка активна до {new_end.strftime('%d.%m.%Y')}.\n"
            f"Вот ваша одноразовая ссылка на группу (истекает через {days} дней):\n{invite_link.invite_link}"
        )
    except Exception as e:
        await message.answer(f"Ошибка при выдаче ссылки пользователю: {e}")

    await message.answer(f"Пользователь {user_id} ({username if username else 'без username'}) добавлен с подпиской на {days} дней до {new_end.strftime('%d.%m.%Y')}.", reply_markup=admin_menu_kb)
    await state.clear()

def get_price(period_text: str) -> int:
    prices = {
        "1 мес 1.344 руб.": 1344,
        "3 мес 3.744 руб.": 3744,
        "6 мес 6.994 руб.": 6994,
        "12 мес +мес. подарок 13.444 руб.": 13444,
    }
    return prices.get(period_text, 0)

def get_months_by_text(period_text: str) -> int:
    mapping = {
        "1 мес 1.344 руб.": 1,
        "3 мес 3.744 руб.": 3,
        "6 мес 6.994 руб.": 6,
        "12 мес +мес. подарок 13.444 руб.": 13,
    }
    return mapping.get(period_text, 0)

@dp.callback_query(F.data.startswith("approve:"))
async def approve_callback(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return await call.answer("У вас нет доступа.", show_alert=True)

    data = call.data.split(":")[1]  # формат: approve:user_id|period
    try:
        user_id_str, period = data.split("|")
        user_id = int(user_id_str)
    except Exception:
        return await call.answer("Некорректные данные.", show_alert=True)

    months = get_months_by_text(period)
    now = datetime.now()

    async with aiosqlite.connect("users.db") as db:
        # Получаем текущую дату окончания, если есть
        async with db.execute("SELECT end_date FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            now = datetime.now()
            if row and row[0]:
                try:
                    current_end = datetime.fromisoformat(row[0])
                except Exception:
                    current_end = now
            else:
                current_end = now

            if current_end > now:
                new_end = current_end + timedelta(days=30 * months)
            else:
                new_end = now + timedelta(days=30 * months)

        # Получаем все остальные поля (если есть)
        async with db.execute("SELECT email, fullname, phone, city FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                email, fullname, phone, city = row
            else:
                email = fullname = phone = city = ""

        # Получаем username
        try:
            user = await bot.get_chat(user_id)
            username = user.username or user.full_name
        except:
            username = ""

        # Обновляем или добавляем запись
        await db.execute(
            "REPLACE INTO users (user_id, end_date, username, email, fullname, phone, city) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, new_end.isoformat(), username, email, fullname, phone, city)
        )
        await db.commit()

    # Теперь продолжаем с логикой: разбан, ссылка и отправка
    try:
        await bot.unban_chat_member(GROUP_ID, user_id)
        invite_link = await bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            name=f"Link for {user_id}",
            expire_date=datetime.now() + timedelta(days=1),
            member_limit=1
        )
        await bot.send_message(
            user_id,
            f"""✅ Вы получили доступ к клубу <b>«Диалог Истины»</b>!

1. Обязательно подпишитесь на канал — <a href="{invite_link.invite_link}">вот ссылка</a>. Здесь проходят прямые эфиры, а также вы общаетесь с другими учениками и преподавателями клуба.

2. На почту вам пришёл доступ на платформу GetCourse.

3. Если возникли проблемы или сложности — сразу обратитесь в тех.поддержку: <a href="https://wa.me/79380244802">написать в WhatsApp</a>.
""",
            parse_mode="HTML"
        )
        await call.message.reply(f"✅ Подписка подтверждена для пользователя {user_id}")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"Ошибка при выдаче ссылки для {user_id}: {e}")
        await call.message.reply(f"Произошла ошибка: {e}")

    await call.answer("Подтверждено.")

@dp.callback_query(F.data.startswith("deny:"))
async def deny_callback(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return await call.answer("У вас нет доступа.", show_alert=True)

    user_id_str = call.data.split(":")[1]
    try:
        user_id = int(user_id_str)
        kb = await get_main_menu_kb(user_id)
        await bot.send_message(user_id, "❌ Оплата не подтверждена. Попробуйте снова.", reply_markup=kb)
        await call.message.reply(f"❌ Оплата отклонена для пользователя {user_id}")
    except Exception as e:
        await call.message.reply(f"Ошибка: {e}")

    await call.answer("Отклонено.")

async def on_startup():
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                end_date TEXT,
                username TEXT,
                email TEXT,
                fullname TEXT,
                phone TEXT,
                city TEXT
            )
        """)
        # Добавим недостающие колонки, если база уже существовала без них
        for column in ["email", "fullname", "phone", "city"]:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")
            except aiosqlite.OperationalError:
                # Колонка уже есть — просто пропускаем ошибку
                pass
        await db.commit()

async def main():
    import logging
    logging.basicConfig(level=logging.INFO)

    await on_startup()  # если есть функция для инициализации
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())