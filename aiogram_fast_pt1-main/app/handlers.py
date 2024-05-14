from aiogram import F, Router
from aiogram.types import (
    Message,
    CallbackQuery,
    InputFile,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiofiles
from app.config import ADMINS_ID
import app.keyboards as kb
import app.database.requests as rq
from app.utils.utils import generate_qr_code, scan_qr_code
from pyzbar.pyzbar import decode
from PIL import Image
import io

router = Router()


class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    img = State()


class AddQRCode(StatesGroup):
    usage_limit = State()
    bonus_points = State()


class ScanQRCode(StatesGroup):
    qr_code = State()


class RegistrationState(StatesGroup):
    phone = State()
    name = State()
    # surname = State()


# Функция для проверки, является ли пользователь администратором
def is_admin(user_id):
    return user_id in ADMINS_ID


# Функция для оформления сообщения с эмодзи
def styled_message(text, style="info"):
    # return f"ℹ️ {text}
    if style == "info":
        return f"ℹ️ {text}"
    elif style == "error":
        return f"❌ {text}"
    elif style == "warning":
        return f"⚠️ {text}"
    elif style == "success":
        return f"✅ {text}"


# Команда для регистрации пользователя
@router.message(F.text == "/reg")
async def start_registration(message: Message, state: FSMContext):
    user_registered = await rq.is_user_registered(message.from_user.id)
    if user_registered:
        await message.answer(
            styled_message("Вы уже зарегистрированы.", style="warning")
        )
    else:
        await message.answer(
            styled_message("Для регистрации введите ваш номер телефона:"),
            reply_markup=kb.get_number,
        )
        await state.set_state(RegistrationState.phone)


# Обработчик регистрации номера телефона
@router.message(RegistrationState.phone)
async def process_registration_phone(message: Message, state: FSMContext):
    if not message.contact:
        await message.answer(
            styled_message("Пожалуйста, используйте кнопку отправки контакта.")
        )
        return

    contact = message.contact
    await state.update_data(phone=contact.phone_number)
    await message.answer(
        styled_message("Теперь введите ваше ФИО (Фамилия Имя Отчество):"),
        reply_markup=kb.main,
    )
    await state.set_state(RegistrationState.name)


# Обработчик регистрации ФИО
@router.message(RegistrationState.name)
async def process_registration_name(message: Message, state: FSMContext):
    full_name = message.text.split(" ")
    if len(full_name) != 3:
        await message.answer(
            styled_message("Введите ФИО в формате 'Фамилия Имя Отчество'.")
        )
        return

    await state.update_data(
        name=full_name[1], surname=full_name[0], patronymic=full_name[2]
    )
    # print()
    data = await state.get_data()
    phone = data["phone"]
    await rq.register_user(
        message.from_user.id, full_name[1], full_name[0], full_name[2], phone
    )
    await message.answer(
        styled_message(
            "Регистрация успешно завершена! Теперь вы можете приступить к покупкам.",
            style="success",
        )
    )
    await state.clear()


@router.message(F.text == "Каталог")
async def ask_catalog(message: Message):
    catalog_message = (
        "🛍️ Здесь представлен каталог товаров, которые вы можете приобрести полностью оплатив бонусами. "
        "Выберите интересующий вас товар из списка ниже:"
    )
    await message.answer(catalog_message, reply_markup=kb.show_katalog)


@router.callback_query(F.data == "show_katalog")
async def show_katalog(callback: CallbackQuery):
    items = await rq.get_all_items()
    for item in items:
        item_text = (
            f"📦 *Название:* {item.name}\n"
            f"📝 *Описание:* {item.description}\n"
            f"💰 *Цена:* {item.price}💎"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Купить", callback_data=f"item_{item.id}")]
            ]
        )
        await callback.message.answer_photo(
            photo=item.img,
            caption=item_text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


@router.callback_query(F.data.startswith("item_"))
async def buy_item(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    item = await rq.get_item_by_id(item_id)

    user_balance = await rq.get_user_balance(callback.from_user.id)

    if user_balance >= item.price:
        await send_invoice(callback.bot, callback.from_user.id, item)

        await send_admin_notification(callback.bot, item, callback.from_user.id)

        await rq.set_user_balance(callback.from_user.id, user_balance - item.price)

        await callback.answer("✅ Товар успешно куплен")
    else:
        await callback.answer("❌ Недостаточно бонусов для покупки товара")


async def send_invoice(bot, user_id, item):
    await bot.send_message(
        user_id,
        f"✨ Вы успешно приобрели товар:\n📦 Название: {item.name}\n📝 Описание: {item.description}\n💎 Цена: {item.price}",
    )


async def send_admin_notification(bot, item, user_id):
    user = await rq.get_user_by_id(user_id)
    admin_message = f"🛒 *Пользователь:* {user_id} - {user.Name} {user.Surname} {user.Patronymic} \n📦 *Пользователь совершил покупку товара:*\n📝 *Название:* {item.name}\n📋 *Описание:* {item.description}\n💎 *Цена:* {item.price}"
    for adm in ADMINS_ID:
        await bot.send_message(adm, admin_message)


# Команда для открытия панели администратора
@router.message(Command("admin"))
async def cmd_admin_panel(message: Message):
    if is_admin(message.from_user.id):
        await message.answer(
            styled_message("Здравствуйте! Открываю для вас панель администратора"),
            reply_markup=kb.admin_keyboard,
        )
    else:
        await message.answer(styled_message("У вас нет прав доступа к этой команде."))


# Команда для сканирования QR-кода
@router.message(F.text == "Сканировать QR-код")
async def scan_qr_code_command(message: Message, state: FSMContext):
    await message.answer(styled_message("Отправьте QR-код 📷"))
    await state.set_state(ScanQRCode.qr_code)

@router.message(Command('cancel'))
async def cancel_action(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(styled_message("Действие отменено."))
    
# Обработчик фото с QR-кодом
@router.message(ScanQRCode.qr_code)
async def handle_qr_code_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer(styled_message("Пожалуйста, отправьте изображение"))
        return

    photo_file_id = message.photo[-1].file_id
    image_data = await message.bot.get_file(photo_file_id)
    downloaded_file = await message.bot.download_file(image_data.file_path)

    file_path = f"{photo_file_id}.jpg"

    async with aiofiles.open(file_path, "wb") as new_file:
        await new_file.write(downloaded_file.read())

    qr_code_data = scan_qr_code(file_path)

    if qr_code_data:
        if "Bonus points" in qr_code_data:
            id = int(
                qr_code_data.split("Bonus points: ")[0].replace("ID: ", "").strip()
            )
            if not await rq.is_qr_code_scaned_by_user(message.from_user.id, id):
                limit = await rq.get_usage_limit_by_id(id)
                if not limit:
                    limit = 0
                if limit > 0:
                    await rq.set_usage_limit_by_id(
                        id, await rq.get_usage_limit_by_id(id) - 1
                    )
                    await message.answer(
                        styled_message(
                            f"Вы получили {qr_code_data.split('Bonus points: ')[1]} бонусов.",
                            style="success",
                        )
                    )
                    await rq.set_user_scanned_qr(message.from_user.id, id)
                    add_bonus = int(qr_code_data.split("Bonus points: ")[1])
                    user_balance = (
                        await rq.get_user_balance(message.from_user.id) + add_bonus
                    )
                    await rq.set_user_balance(message.from_user.id, user_balance)
                else:
                    await message.answer(
                        styled_message(
                            "Бонусы для этого QR-кода закончились.", style="error"
                        )
                    )
            else:
                await message.answer(
                    styled_message(
                        "Вы уже получили бонусы для этого QR.", style="error"
                    )
                )
        else:
            await message.answer(
                styled_message("Это не QR-код бонусов.", style="error")
            )
    else:
        await message.answer(
            styled_message(
                "На отправленном изображении не обнаружено QR-кода.", style="error"
            )
        )

    await state.clear()


# Функция для обработки QR-кода
async def process_qr_code(image_data):
    async with image_data.download() as file_data:
        image = Image.open(io.BytesIO(await file_data.read()))

    decoded_objects = decode(image)

    if decoded_objects:
        qr_code_data = decoded_objects[0].data.decode("utf-8")
        return qr_code_data
    else:
        return None


# Команда для добавления товара (доступно только администраторам)
@router.message(F.text == "Добавить товар")
async def admin_add_item_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddProduct.name)
    await message.answer(styled_message("🛍️ Отправьте название для нового товара"))


@router.message(F.text == "Отмена")
async def cancel_action(message: Message, state: FSMContext):
    await state.finish()
    await message.answer(styled_message("Действие отменено."))


# Обработчик названия товара
@router.message(AddProduct.name)
async def admin_add_item_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(styled_message("✏️ Отправьте описание для нового товара"))
    await state.set_state(AddProduct.description)


# Обработчик описания товара
@router.message(AddProduct.description)
async def admin_add_item_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(styled_message("💲 Отправьте цену для нового товара"))
    await state.set_state(AddProduct.price)


# Обработчик цены товара
@router.message(AddProduct.price)
async def admin_add_item_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        await message.answer(
            styled_message("❌ Пожалуйста, введите корректную цену (число)")
        )
        return
    await state.update_data(price=price)
    await message.answer(styled_message("📷 Отправьте изображение для нового товара"))
    await state.set_state(AddProduct.img)


# Обработчик изображения товара
@router.message(AddProduct.img)
async def admin_add_item_img(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer(styled_message("❌ Пожалуйста, отправьте изображение"))
        return

    photo_file_id = message.photo[-1].file_id
    await state.update_data(img_id=photo_file_id)
    item_data = await state.get_data()
    item_card_text = (
        f"🏷️ Название: {item_data['name']}\n"
        f"📝 Описание: {item_data['description']}\n"
        f"💲 Цена: {item_data['price']}💎"
    )

    await message.answer_photo(
        photo=photo_file_id, caption=item_card_text, reply_markup=kb.add_item_true
    )

    await state.update_data(item_data=item_data)


# Кнопка для сохранения товара
@router.callback_query(F.data == "save_item")
async def save_item_callback(callback: CallbackQuery, state: FSMContext):
    item_data = await state.get_data()
    await rq.add_item(
        name=item_data["name"],
        description=item_data["description"],
        price=item_data["price"],
        img=item_data["img_id"],
    )
    await callback.answer("✅ Товар успешно добавлен")
    await state.clear()


# Кнопка для отмены добавления товара
@router.callback_query(F.data == "cancel_add_item")
async def cancel_add_item_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer(styled_message("❌ Добавление товара отменено"))


# Команда для удаления товара
@router.message(F.text == "Удалить товар")
async def delete_item_message(message: Message):
    if not is_admin(message.from_user.id):
        return
    items = await rq.get_all_items()
    for item in items:
        item_text = (
            f"🏷️ Название: {item.name}\n"
            f"📝 Описание: {item.description}\n"
            f"💲 Цена: {item.price}💎"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Удалить", callback_data=f"delete_item_{item.id}"
                    )
                ]
            ]
        )
        await message.answer_photo(
            photo=item.img, caption=item_text, reply_markup=keyboard
        )


# Кнопка для удаления товара
@router.callback_query(F.data.startswith("delete_item_"))
async def delete_item_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    item_id = int(callback.data.split("_")[2])
    await rq.delete_item(item_id)
    await callback.answer(styled_message("✅ Товар успешно удален"))


# Команда для генерации QR-кода
@router.message(F.text == "Сгенерировать QR-код")
async def add_qr_code_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        styled_message("Введите количество использований для QR-кода:")
    )
    await state.set_state(AddQRCode.usage_limit)


# Обработчик количества использований QR-кода
@router.message(AddQRCode.usage_limit)
async def process_usage_limit(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        usage_limit = int(message.text)
    except ValueError:
        await message.answer(styled_message("Пожалуйста, введите число."))
        return

    await state.update_data(usage_limit=usage_limit)
    await state.set_state(AddQRCode.bonus_points)
    await message.answer(
        styled_message("Введите количество бонусов, которое будет давать QR-код:")
    )


# Обработчик количества бонусов QR-кода
@router.message(AddQRCode.bonus_points)
async def process_bonus_points(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        bonus_points = int(message.text)
    except ValueError:
        await message.answer(styled_message("Пожалуйста, введите число."))
        return

    await state.update_data(bonus_points=bonus_points)
    qr_data = await state.get_data()
    last_qr_code_id = await rq.get_last_qr_code_id()
    generate_qr_code(last_qr_code_id + 1, qr_data["bonus_points"], "qr_code.png")
    qr_code_input_file = FSInputFile("qr_code.png", "qr_code")
    result = await message.answer_photo(
        qr_code_input_file,
        caption=styled_message("QR-код успешно создан!", style="success"),
    )
    file_id = result.photo[-1].file_id

    await rq.add_qr_code(
        usage_limit=qr_data["usage_limit"],
        bonus_points=qr_data["bonus_points"],
        qr_code_id=file_id,
    )
    await state.clear()


# Команда для начала работы с ботом
@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id)
    if is_admin(message.from_user.id):
        await message.answer(
            styled_message(
                "Здравствуйте! Открываю для вас панель администратора", style="success"
            ),
            reply_markup=kb.admin_keyboard,
        )
    else:
        await message.answer(
            styled_message(
                "Рад приветствовать в нашем магазине! Здесь ты можешь копить бонусы и оплаивать ими 100% от стоимости товара"
            ),
            reply_markup=kb.main,
        )


@router.message(F.text == "Баланс")
async def show_balance(message: Message):
    user_registered = await rq.is_user_registered(message.from_user.id)
    if not user_registered:
        await message.answer(
            styled_message("Для доступа к балансу необходимо пройти регистрацию.")
        )
        await message.answer(
            styled_message("Для этого введите команду /reg и следуйте инструкциям.")
        )
        return

    balance = await rq.get_user_balance(message.from_user.id)
    await message.answer(styled_message(f"Ваш текущий баланс: {balance}💎"))


# Команда для просмотра контактов
@router.message(F.text == "Контакты")
async def show_contacts(message: Message):
    contacts = "Наши контакты:\nТелефон: +7 (XXX) XXX-XX-XX\nEmail: example@example.com"
    await message.answer(styled_message(contacts))


#
