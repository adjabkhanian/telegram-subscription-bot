import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, FSInputFile
from pyairtable import Api
from datetime import timezone

TOKEN = "7018906512:AAGIZv1bbvOdabOwimN6F7kNmwZMqPQqqJo"
ADMIN_ID = 7029037184
GROUP_ID = -1002858230612
ADMINS = [7029037184, 1391901108, 989906193]  # список Telegram ID админов

# Конфигурация Airtable
AIRTABLE_API_KEY = 'patR5ePq6DfwMWknr.798939b3dff4003934788bab3afc96caef64b951a44b82282ea38f2d85866d62'  # Найти в Airtable API docs
AIRTABLE_BASE_ID = 'app4OuxtRjXGQCNQx'  # Из URL вашей базы
AIRTABLE_TABLE_NAME = 'dialog-istini'

# Инициализация Airtable
airtable = Api(AIRTABLE_API_KEY)
users_table = airtable.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

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
    getting_email_trial = State()

async def get_user(user_id: int):
    """Получить данные пользователя из Airtable"""
    records = users_table.all(formula=f"{{user_id}} = {user_id}")
    return records[0] if records else None

async def update_user(user_id: int, fields: dict):
    """Обновить или создать запись пользователя"""
    record = await get_user(user_id)
    if record:
        users_table.update(record['id'], fields)
    else:
        users_table.create({'user_id': user_id, **fields})

async def check_trial_used(user_id: int) -> bool:
    """Проверяет, использовал ли пользователь пробный период (через Airtable)"""
    record = users_table.first(formula=f"{{user_id}} = {user_id}")
    if record and "end_date" in record["fields"]:
        end_date = datetime.fromisoformat(record["fields"]["end_date"]).astimezone()
        return end_date > datetime.now().astimezone()
    return False

async def get_main_menu_kb(user_id: int):
    buttons = [
        [KeyboardButton(text="ℹ️ Информация о курсе")],
    ]

    # Проверяем, есть ли активная подписка
    record = users_table.first(formula=f"{{user_id}} = {user_id}")
    now = datetime.now().astimezone()

    show_trial = True
    show_renew = False

    if record:
        fields = record.get("fields", {})
        end_date_str = fields.get("end_date")
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str).astimezone()
                if end_date > now:
                    show_trial = False  # Уже есть подписка
                    show_renew = True   # Можно продлить
            except:
                pass
        if fields.get("trial_used", False):
            show_trial = False

    if show_trial:
        buttons.append([KeyboardButton(text="🆓 Пробный период (5 дней)")])

    buttons.append([KeyboardButton(text="💳 Оформить подписку")])

    if show_renew:
        buttons.append([KeyboardButton(text="🔁 Продлить подписку")])

    buttons.append([KeyboardButton(text="👤 Личный кабинет")])

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

@dp.message(F.text == "🔁 Продлить подписку")
async def renew_subscription(message: Message, state: FSMContext):
    await subscribe(message, state)

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
    DETAILS_URL = "https://example.com/education"  # Здесь замени на свою ссылку
    await message.answer(f"Подробнее об обучении смотрите здесь:\n{DETAILS_URL}")

@dp.message(F.text == "Хочу в клуб")
async def start_subscription(message: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Оформить подписку")],
            [KeyboardButton(text="🆓 Пробный период (5 дней)")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Выберите способ подключения к обучению:\n"
        "💳 Полная подписка — откроет доступ ко всем урокам, чату и эфиру\n"
        "🆓 Пробный период — 5 дней бесплатного доступа\n",
        reply_markup=kb
    )

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
    # Проверяем активную подписку через Airtable
    record = users_table.first(formula=f"{{user_id}} = {message.from_user.id}")
    
    # if record and 'end_date' in record['fields']:
    #     end_date = datetime.fromisoformat(record['fields']['end_date'])
    #     # Делаем обе даты aware (с часовым поясом)
    #     now = datetime.now().astimezone()  # Добавляем текущий часовой пояс
    #     end_date = end_date.astimezone()  # Добавляем часовой пояс к end_date
    #     if end_date > now:
    #         days_left = (end_date - now).days
    #         kb = await get_main_menu_kb(message.from_user.id)
    #         await message.answer(
    #             f"У вас уже есть активная подписка, осталось {days_left} дней.",
    #             reply_markup=kb
    #         )
    #         return
    
    await message.answer("⏳ На сколько месяцев оформить подписку?", reply_markup=period_kb)
    await state.set_state(SubscribeSteps.choosing_period)

@dp.message(F.text == "🆓 Пробный период (5 дней)")
async def start_trial(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    record = users_table.first(formula=f"{{user_id}} = {user_id}")
    fields = record["fields"] if record else {}

    # Проверка: если уже использовал пробник
    if fields.get("trial_used", False):
        await message.answer("❌ Вы уже использовали пробный период")
        return

    # Проверка: все ли данные есть
    required_fields = ["email", "fullname", "phone", "city"]
    missing_fields = [field for field in required_fields if not fields.get(field)]

    if not missing_fields:
        # Всё есть — активируем пробник сразу
        await activate_trial(
            message=message,
            email=fields["email"],
            username=username,
            full_name=fields.get("fullname", ""),
            phone=fields.get("phone", ""),
            city=fields.get("city", "")
        )

        return

    # Данных не хватает — начинаем опрашивать
    await state.update_data(missing_fields=missing_fields, username=username)

    next_field = missing_fields[0]
    if next_field == "email":
        await message.answer("📧 Введите ваш email:", reply_markup=cancel_kb)
        await state.set_state(SubscribeSteps.getting_email_trial)
    elif next_field == "fullname":
        await message.answer("✍️ Введите ваше <b>ФИО</b>:", reply_markup=cancel_kb)
        await state.set_state(SubscribeSteps.getting_fullname)
    elif next_field == "phone":
        await message.answer("📱 Введите ваш номер телефона:", reply_markup=cancel_kb)
        await state.set_state(SubscribeSteps.getting_phone)
    elif next_field == "city":
        await message.answer("🏙️ Введите ваш город:", reply_markup=cancel_kb)
        await state.set_state(SubscribeSteps.getting_city)


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

    period = data.get("period")  # 🛡️ безопасно достаём

    if period:
        # Это платная подписка
        await message.answer("🏙️ Введите ваш <b>город</b>:", reply_markup=cancel_kb)
        await state.set_state(SubscribeSteps.getting_city)
    else:
        # Это пробный путь
        missing_fields = data.get("missing_fields", [])
        if "phone" in missing_fields:
            missing_fields.remove("phone")
        await state.update_data(missing_fields=missing_fields)

        if "city" in missing_fields:
            await message.answer("🏙️ Введите ваш город:", reply_markup=cancel_kb)
            await state.set_state(SubscribeSteps.getting_city)
        else:
            username = data.get("username") or message.from_user.username or message.from_user.full_name
            await activate_trial(message, data.get("email"), username)
            await state.clear()


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
    period = data.get("period")

    if period:
        # Это платная подписка
        await message.answer(
            f"""✅ Отлично!
Переведите <b>{get_price(period)}₽</b> на карту:

<code>2204 3203 6606 1564 (Озон банк, Алёна Александровна Добыко)</code>

После оплаты пришлите сюда скриншот чека.
""",
            reply_markup=cancel_kb
        )
        await state.set_state(SubscribeSteps.waiting_payment)
    else:
        username = data.get("username") or message.from_user.username or message.from_user.full_name
        await activate_trial(
            message=message,
            email=data.get("email"),
            username=username,
            full_name=data.get("full_name"),
            phone=data.get("phone"),
            city=city
        )




        await state.clear()



@dp.message(SubscribeSteps.waiting_payment, F.photo)
async def handle_payment(message: Message, state: FSMContext):
    data = await state.get_data()
    username = message.from_user.username or message.from_user.full_name
    kb = await get_main_menu_kb(message.from_user.id)
    await message.answer("⏳ Ожидайте подтверждение от администратора.", reply_markup=kb)
    for admin_id in ADMINS:
        try:

            short_period_code = get_months_by_text(data['period'])

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
                callback_data=f"approve:{message.from_user.id}|{short_period_code}"
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
    record = users_table.first(formula=f"{{user_id}} = {message.from_user.id}")
    fields = {
        'user_id': message.from_user.id,
        'username': username,
        'email': data['email'],
        'fullname': data['fullname'],
        'phone': data['phone'],
        'city': data['city'],
        'status': 'pending'
    }
    if record:
        users_table.update(record["id"], fields)
    else:
        users_table.create(fields)

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

    now = datetime.now(timezone.utc)

    record = users_table.first(formula=f"{{user_id}} = {user_id}")
    fields = record['fields'] if record else {}
    record_id = record['id'] if record else None

    current_end = None
    if "end_date" in fields:
        try:
            current_end = datetime.fromisoformat(fields["end_date"])
        except Exception:
            pass

    now = datetime.now(timezone.utc)
    if current_end and current_end > now:
        new_end = current_end + timedelta(days=30 * months)
    else:
        new_end = now + timedelta(days=30 * months)

    users_table.update(record_id, {
        "end_date": new_end.isoformat(),
        "username": username
    })

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
    record = users_table.first(formula=f"{{user_id}} = {message.from_user.id}")
    kb = await get_main_menu_kb(message.from_user.id)
    
    if record and 'end_date' in record['fields']:
        fields = record.get("fields", {})
        end_date = datetime.fromisoformat(fields["end_date"])
        now = datetime.now(timezone.utc)
        if end_date > now:
            days_left = (end_date - now).days
            status = "🔹 Пробный период" if days_left <= 5 else "🔹 Полная подписка"
            await message.answer(
                f"👤 Ваш профиль\n{status}\n"
                f"📆 До: {end_date.strftime('%d.%m.%Y')}\n"
                f"⏳ Осталось дней: {days_left}",
                reply_markup=kb
            )
            return
    
    await message.answer("У вас нет активной подписки.", reply_markup=kb)

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

    records = users_table.all()
    if not records:
        await message.answer("Список пуст.")
        return

    text = "<b>Список подписчиков:</b>\n\n"
    chunks = []

    for record in records:
        f = record.get("fields", {})
        user_id = f.get("user_id", "N/A")
        username = f.get("username", "")
        fullname = f.get("fullname", "")
        phone = f.get("phone", "")
        city = f.get("city", "")
        email = f.get("email", "")
        end_date = f.get("end_date", "N/A")

        username_display = f'<a href="https://t.me/{username}">@{username}</a>' if username else "—"

        entry = (
            f"<b>🆔 ID:</b> <code>{user_id}</code>\n"
            f"<b>👤 Username:</b> {username_display}\n"
            f"<b>📛 ФИО:</b> {fullname}\n"
            f"<b>📞 Телефон:</b> {phone}\n"
            f"<b>🏙️ Город:</b> {city}\n"
            f"<b>📧 Email:</b> {email}\n"
            f"<b>📆 До:</b> {end_date}\n\n"
        )

        if len(text) + len(entry) > 4000:
            chunks.append(text)
            text = ""
        text += entry

    if text:
        chunks.append(text)

    # Отправляем все части
    for chunk in chunks:
        await message.answer(chunk, parse_mode="HTML", disable_web_page_preview=True)


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
    record = users_table.first(formula=f"{{user_id}} = {user_id}")
    if record:
        users_table.delete(record["id"])
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
    records = users_table.all()
    success, failed = 0, 0

    for record in records:
        user_id = record["fields"].get("user_id")
        if user_id:
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
    record = users_table.first(formula=f"LOWER({{username}}) = '{username_to_find}'")
    if record:
        fields = record["fields"]
        user_id = fields.get("user_id", "N/A")
        end_date = fields.get("end_date", "N/A")
        username = fields.get("username", "N/A")
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

@dp.message(SubscribeSteps.getting_email_trial)
async def process_trial_email(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        kb = await get_main_menu_kb(message.from_user.id)
        await message.answer("Отменено. Возврат в главное меню.", reply_markup=kb)
        return

    email = message.text.strip()
    await state.update_data(email=email)

    user_id = message.from_user.id
    record = users_table.first(formula=f"{{user_id}} = {user_id}")
    fields = record["fields"] if record else {}

    # Собираем недостающие поля (уже с учетом введенного email)
    missing_fields = []
    if not fields.get("fullname"):
        missing_fields.append("fullname")
    if not fields.get("phone"):
        missing_fields.append("phone")
    if not fields.get("city"):
        missing_fields.append("city")

    # Если всё есть — сразу активируем
    if not missing_fields:
        username = message.from_user.username or message.from_user.full_name
        await activate_trial(
            message=message,
            email=email,
            username=username,
            full_name=fields.get("fullname", ""),
            phone=fields.get("phone", ""),
            city=fields.get("city", "")
        )

        await state.clear()
    else:
        await state.update_data(missing_fields=missing_fields)

        # Переходим к следующему шагу
        next_field = missing_fields[0]
        if next_field == "fullname":
            await message.answer("✍️ Введите ваше <b>ФИО</b>:", reply_markup=cancel_kb)
            await state.set_state(SubscribeSteps.getting_fullname)
        elif next_field == "phone":
            await message.answer("📱 Введите ваш номер телефона:", reply_markup=cancel_kb)
            await state.set_state(SubscribeSteps.getting_phone)
        elif next_field == "city":
            await message.answer("🏙️ Введите ваш город:", reply_markup=cancel_kb)
            await state.set_state(SubscribeSteps.getting_city)

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
    now = datetime.now(timezone.utc)
    new_end = now + timedelta(days=days)

    # Загружаем старые данные, если они есть
    record = users_table.first(formula=f"{{user_id}} = {user_id}")
    fields = record["fields"] if record else {}

    users_table.update(record["id"] if record else None, {
        "user_id": user_id,
        "end_date": new_end.isoformat(),
        "username": username,
        "email": fields.get("email", ""),
        "fullname": fields.get("fullname", ""),
        "phone": fields.get("phone", ""),
        "city": fields.get("city", "")
    })

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

    data = call.data.split(":")[1]  # формат: approve:user_id|months
    try:
        user_id_str, months_str = data.split("|")
        user_id = int(user_id_str)
        months = int(months_str)
    except Exception:
        return await call.answer("Некорректные данные.", show_alert=True)

    now = datetime.now(timezone.utc)

    # 🧠 ЗАМЕНА SQLite → Airtable:
    record = users_table.first(formula=f"{{user_id}} = {user_id}")
    fields = record["fields"] if record else {}
    record_id = record["id"] if record else None

    current_end = None
    try:
        if "end_date" in fields:
            current_end = datetime.fromisoformat(fields["end_date"])
    except:
        current_end = None

    if current_end and current_end > now:
        new_end = current_end + timedelta(days=30 * months)
    else:
        new_end = now + timedelta(days=30 * months)

    users_table.update(record_id, {
        "user_id": user_id,
        "username": call.from_user.username or "",
        "email": fields.get("email", ""),
        "fullname": fields.get("fullname", ""),
        "phone": fields.get("phone", ""),
        "city": fields.get("city", ""),
        "end_date": new_end.isoformat()
    })


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

3. Если возникли проблемы или сложности — сразу обратитесь в тех.поддержку: <a href="https://wa.me/79001234567">написать в WhatsApp</a>.
""",
            parse_mode="HTML"
        )
        await call.message.reply(f"✅ Подписка подтверждена для пользователя {user_id}")
        # Уведомление другим админам
        for admin_id in ADMINS:
            if admin_id != call.from_user.id:
                try:
                    await bot.send_message(
                        admin_id,
                        f"✅ Подписка для пользователя <code>{user_id}</code> подтверждена админом <b>{call.from_user.full_name}</b>.",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"❗ Не удалось уведомить админа {admin_id}: {e}")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"Ошибка при выдаче ссылки для {user_id}: {e}")
        await call.message.reply(f"Произошла ошибка: {e}")

    await call.answer("Подтверждено.")

@dp.message(F.text == "🆓 Пробный период (5 дней)")
async def start_trial(message: Message, state: FSMContext):
    async with aiosqlite.connect("users.db") as db:
        # Проверяем, есть ли уже подписка (включая пробную)
        async with db.execute("SELECT end_date FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                end_date = datetime.fromisoformat(row[0])
                if end_date > datetime.now().astimezone():
                    kb = await get_main_menu_kb(message.from_user.id)
                    await message.answer(
                        "У вас уже есть активная подписка или пробный период.",
                        reply_markup=kb
                    )
                    return

    # Запрашиваем email для пробного периода
    await message.answer("📧 Введите ваш email для активации пробного периода:", reply_markup=cancel_kb)
    await state.set_state(SubscribeSteps.getting_email_trial)

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
    # Проверяем подключение к Airtable
    try:
        test_records = users_table.all(max_records=1)
        print("Airtable connection successful")
    except Exception as e:
        print(f"Airtable connection error: {e}")
        raise

# ... (после всех хэндлеров, например после @dp.callback_query(F.data.startswith("deny:"))  

async def activate_trial(message: Message, email: str, username: str, full_name: str, phone: str, city: str):
    user_id = message.from_user.id
    now = datetime.now(timezone.utc)
    trial_days = 5
    end_date = (now + timedelta(days=trial_days)).isoformat()

    fields = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "fullname": full_name,
        "phone": phone,
        "city": city,
        "end_date": end_date,
        "trial_used": True
    }

    try:
        record = users_table.first(formula=f"{{user_id}} = {user_id}")
        if record:
            users_table.update(record["id"], fields)
        else:
            users_table.create(fields)

        await bot.unban_chat_member(GROUP_ID, user_id)

        invite_link = await bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            name=f"Trial link for {user_id}",
            expire_date=datetime.now() + timedelta(days=1),
            member_limit=1
        )

        await bot.send_message(
            message.chat.id,
            f"""✅ Готово!
Вы получили пробный доступ на {trial_days} дней.

🔗 <b>Вот ваша одноразовая ссылка для входа в группу:</b>
{invite_link.invite_link}

⚠️ Ссылка действует 24 часа и только для одного входа.
""",
            parse_mode="HTML",
            reply_markup=await get_main_menu_kb(user_id)
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при активации пробного периода:\n<code>{e}</code>")




async def check_trial_periods():
    while True:
        now = datetime.now().astimezone()
        records = users_table.all()

        for record in records:
            fields = record.get("fields", {})
            user_id = fields.get("user_id")
            end_date_str = fields.get("end_date")

            if not user_id or not end_date_str:
                continue

            try:
                end_date = datetime.fromisoformat(end_date_str).astimezone()
            except:
                continue

            # Если подписка закончилась
            if end_date < now:
                try:
                    await bot.ban_chat_member(GROUP_ID, user_id)
                    await bot.unban_chat_member(GROUP_ID, user_id)
                    print(f"⛔ Пользователь {user_id} удалён из группы (подписка закончилась)")
                except Exception as e:
                    print(f"⚠️ Не удалось удалить {user_id}: {e}")
            # Если заканчивается сегодня
            elif (end_date.date() - now.date()).days == 0:
                try:
                    await bot.send_message(
                        user_id,
                        "⚠️ Ваш доступ заканчивается сегодня!\n"
                        "Чтобы продолжить обучение, оформите полную подписку через меню бота."
                    )
                except Exception as e:
                    print(f"⚠️ Не удалось уведомить {user_id}: {e}")

        await asyncio.sleep(6 * 60 * 60)  # каждые 6 часов

# Далее идет функция main() и остальное...

async def main():
    import logging
    logging.basicConfig(level=logging.INFO)

    await on_startup()  # инициализация базы данных

    # +++ Вот эту строку добавляем! +++
    asyncio.create_task(check_trial_periods())  # Запуск фоновой проверки пробных периодов

    await dp.start_polling(bot)  # Старт бота

if __name__ == "__main__":
    asyncio.run(main())