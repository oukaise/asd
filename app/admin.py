from aiogram import F, Router, types
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InputFile
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import tg_admin
import app.keyboards as kb
from app.database.requests import get_users, set_item, get_order_by_order_number, update_order_status_by_order_number, get_all_cities, get_item_by_id
from common import send_message_from_bot, get_user_id
from bot import bot
from app.database.models import async_session
admin = Router()

class Newsletter(StatesGroup):
    message = State()

class AddItem(StatesGroup):
    name = State()
    category = State()  # category это и есть ID города
    price = State()
    all_cities = State()
    
class EditItem(StatesGroup):
    select_item = State()
    name = State()
    category = State()  # category это и есть ID города
    price = State()
    all_cities = State()

class AdminProtect(Filter):
    async def __call__(self, message: Message):
        return message.from_user.id in tg_admin

class PaymentCheck(StatesGroup):
    order_number = State()
    payment_status = State()
    admin_message = State()

@admin.message(AdminProtect(), Command('apanel'))
async def apanel(message: Message):
    await message.answer("Возможные команды:", reply_markup=await kb.admin_keyboard())

@admin.message(AdminProtect(), Command('newsletter'))
async def newsletter(message: Message, state: FSMContext):
    await state.set_state(Newsletter.message)
    await message.answer('Отправьте сообщение или фото, которое вы хотите разослать всем пользователям')

@admin.message(AdminProtect(), Newsletter.message)
async def newsletter_message(message: Message, state: FSMContext):
    await message.answer('Подождите... идёт рассылка.')
    
    if message.content_type == types.ContentType.TEXT:
        for user in await get_users():
            try:
                await bot.send_message(chat_id=user.tg_id, text=message.text)
            except Exception as e:
                print(f"Failed to send message to {user.tg_id}: {e}")
    elif message.content_type == types.ContentType.PHOTO:
        photo = message.photo[-1].file_id
        caption = message.caption if message.caption else ''
        for user in await get_users():
            try:
                await bot.send_photo(chat_id=user.tg_id, photo=photo, caption=caption)
            except Exception as e:
                print(f"Failed to send photo to {user.tg_id}: {e}")

    await message.answer('Рассылка успешно завершена.')
    await state.clear()

@admin.message(AdminProtect(), Command('add_item'))
async def item(message: Message, state: FSMContext):
    await state.set_state(AddItem.name)
    await message.answer('Введите название товара')

@admin.message(AdminProtect(), AddItem.name)
async def add_item_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddItem.category)
    await message.answer('Выберите город, в который будет добавлен товар', reply_markup=await kb.generate_cities_button())

@admin.callback_query(AdminProtect(), AddItem.category)
async def add_item_category(callback: CallbackQuery, state: FSMContext):
    await state.update_data(category=callback.data.split('_')[1])  # Сохранение ID города
    await state.set_state(AddItem.all_cities)
    await callback.answer('')
    await callback.message.answer('Добавить товар ко всем городам?', reply_markup=await kb.create_yes_no_buttons())

@admin.callback_query(AdminProtect(), AddItem.all_cities)
async def add_item_all_cities(callback: CallbackQuery, state: FSMContext):
    all_cities_flag = callback.data == 'yes_city'  # Убедимся, что значение сравнивается корректно
    await state.update_data(all_cities=all_cities_flag)
    await state.set_state(AddItem.price)
    await callback.answer('')
    await callback.message.answer('Введите цену товара (без обозначений по типу "₽", все равно в рублях будет)')

@admin.message(AdminProtect(), AddItem.price)
async def add_item_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    data = await state.get_data()

    if not all([data.get('name'), data.get('category'), data.get('price')]):
        await message.answer("Ошибка: не все данные были введены. Попробуйте еще раз.")
        return

    await set_item(data)
    await message.answer('Товар успешно добавлен')
    await state.clear()
    
@admin.callback_query(AdminProtect(), F.data == 'newsletter')
async def newsletter_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await newsletter(callback.message, state)

@admin.callback_query(AdminProtect(), F.data == 'add_item')
async def add_item_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await item(callback.message, state)
    
@admin.callback_query(AdminProtect(), F.data == 'edit_item')
async def edit_item_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await item(callback.message, state)

@admin.callback_query(AdminProtect(), F.data.startswith('check_payment_for_admin'))
async def check_payment_for_admin(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentCheck.order_number)
    await callback.answer('')
    await callback.message.answer('Введите номер заказа: ')

@admin.message(AdminProtect(), PaymentCheck.order_number)
async def enter_order_number(message: Message, state: FSMContext):
    order_number = message.text
    order = await get_order_by_order_number(order_number)
    if order:
        await state.update_data(order_id=order_number, user_id=order.user_id)
        await state.set_state(PaymentCheck.payment_status)
        await message.answer('Выберите статус оплаты:', reply_markup=await kb.payment_keyboard())
    else:
        await message.answer(f"Заказ {order_number} не найден.")

@admin.callback_query(AdminProtect(), lambda c: c.data in ["paid", "not_paid"])
async def check_payment_status(callback: CallbackQuery, state: FSMContext):
    payment_status = "Оплачено" if callback.data == "paid" else "Не оплачено"
    await state.update_data(payment_status=payment_status)
    await state.set_state(PaymentCheck.admin_message)
    await callback.answer('')
    await callback.message.answer('Введите сообщение для пользователя')

@admin.message(AdminProtect(), PaymentCheck.admin_message)
async def send_admin_message(message: Message, state: FSMContext):
    state_data = await state.get_data()
    order_number = state_data.get('order_id')
    user_id = state_data.get('user_id')
    payment_status = state_data.get('payment_status')
    
    await update_order_status_by_order_number(order_number, payment_status)
    
    if message.content_type == types.ContentType.TEXT:
        admin_message = message.text
        await bot.send_message(user_id, admin_message)
    elif message.content_type == types.ContentType.PHOTO:
        photo = message.photo[-1].file_id
        caption = message.caption if message.caption else ''
        await bot.send_photo(user_id, photo, caption=caption)

    await message.answer(f"Статус оплаты для заказа {order_number} обновлен до: {payment_status}")
    await message.answer("Сообщение отправлено пользователю.")
    await state.clear()

@admin.callback_query(AdminProtect(), F.data == 'payment_reject')
async def reject_payment(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    order_number = state_data.get('order_number')
    user_id = await get_user_id(order_number)
    await send_message_from_bot("Оплата отклонена. Пожалуйста, свяжитесь с поддержкой.", user_id)
    await callback.message.edit_reply_markup()
    await callback.answer("Оплата отклонена.")
