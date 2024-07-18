from aiogram import F
from aiogram import Router, types
from aiogram.types import CallbackQuery, Message
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import (set_user, get_area_by_id, get_items_by_city, get_category_by_id, 
                                   get_items_by_city, get_are_by_id, get_item_by_id, create_order)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import spb_info, trc_info, btc_info, tg_admin, operator_username, operator_link, image_url, channel_link, chat_link
from random import choice, randint
from aiogram.utils.markdown import link
from bot import bot
import app.keyboards as kb
router = Router()
psip = ["Магнит 🧲", "Тайник 🪨", "Прикоп🪹" ]

class UserChoice(StatesGroup):
    city = State()  # состояние для города
    item = State()  # состояние для товара

class OrderInfo(StatesGroup):  # состояние для ID пользователя
    item_name = State()  # состояние для названия товара
    city_name = State()  # состояние для названия города
    area_name = State()  # состояние для названия района
    price = State()  # состояние для цены
    order_number = State()  # состояние для номера заказа

class CheckPayment(StatesGroup):
    userid = State()
    user_message = State()
    payment_method = State()
    
class OrderProcess(StatesGroup):
    city = State()
    item = State()
    area = State()
    confirm = State()
    payment_method = State()
    payment_proof = State()
    order_number = State()  # добавляем состояние для метода оплаты
    
class ChooseCity(StatesGroup):
    waiting_for_city_name = State()

@router.message(CommandStart())
@router.callback_query(F.data == 'to_main')
async def cmd_start(message: Message | CallbackQuery, state: FSMContext):
    if isinstance(message, Message):
        await set_user(message.from_user.id)
        await message.answer(text='Выберите город или отправьте его название с большой буквы:',
                             reply_markup=await kb.generate_cities_button())
    else: 
        await message.message.edit_text(text='Выберите город или отправьте его название с большой буквы:',
                             reply_markup=await kb.generate_cities_button())

@router.callback_query(kb.PageCallback.filter())
async def page_navigate(callback: CallbackQuery, callback_data: kb.PageCallback):
    await callback.message.edit_reply_markup(reply_markup=await kb.generate_cities_button(page=callback_data.number))
    await callback.answer()


async def send_order_info_to_admin(order_info):
    admin_id = tg_admin[0]  # используем первый ID из списка админов
    order_text = f"Новый заказ: {order_info}"
    item_info = f"Товар: {order_info['item_name']}, Город: {order_info['city_name']}, Район: {order_info['area_name']}, Цена: {order_info['price']}"
    await bot.send_message(admin_id, order_text + "\n" + item_info)


@router.callback_query(F.data.startswith('category_'))
async def choose_city(callback: CallbackQuery, state: FSMContext):
    city_id = int(callback.data.split('_')[1])
    await state.update_data(city=city_id)
    await callback.answer('')
    await callback.message.edit_text('Выберите товар: ', reply_markup=await kb.generate_items_button(int(callback.data.split('_')[1])))

@router.callback_query(F.data.startswith('item_'))
async def choose_item(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split('_')[1])
    item = await get_item_by_id(item_id)
    await state.update_data(item=item_id)  # сохраняем ID товара в состоянии
    await state.set_state(OrderProcess.area)
    await callback.answer('')
    await callback.message.edit_text('Выберите район: ', reply_markup=await kb.generate_areas_button(item.category))

@router.callback_query(lambda call: call.data.startswith('area_') or call.data.startswith('yes') or call.data.startswith('pay_sbp') or call.data.startswith('pay_usdt') or call.data.startswith('pay_btc'))
async def handle_callback(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    item_id = state_data.get('item')

    if callback.data.startswith('area_'):
        area_id = int(callback.data.split('_')[1])
        area = await get_area_by_id(area_id)
        if area is None:
            await callback.answer("Район не найден.", show_alert=True)
            return

        category = area.category_rel
        item = await get_item_by_id(item_id)
        if item is None:
            await callback.answer("Товар не найден.", show_alert=True)
            return

        stash_type = choice(psip)
        await state.update_data(area=area_id, stash_type=stash_type)

        text = (f"*Подтверждаете заказ?*\n"
                "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                f"`Город: {category.name}`\n"
                f"`Район: {area.name.rstrip()}`\n"
                f"`Товар: {item.name}`\n"
                f"`Тип клада: {stash_type}`\n"
                f"`Цена: {item.price}₽`\n"
                "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                "*Нажав на кнопку 'Да' вы подтверждаете заказ!*")
        await callback.message.edit_text(text=text, reply_markup=await kb.create_confirmation_buttons(), parse_mode='Markdown')
    
    elif callback.data.startswith('yes'):
        item = await get_item_by_id(item_id)
        if item is None:
            await callback.answer("Товар не найден.", show_alert=True)
            return

        area_id = state_data.get('area')
        area = await get_area_by_id(area_id)
        if area is None:
            await callback.answer("Район не найден.", show_alert=True)
            return

        category = area.category_rel
        stash_type = state_data.get('stash_type')
        order_number = randint(7000, 120000)  # генерация номера заказа

        await state.update_data(order_number=order_number)
        await create_order(callback.from_user.id, item_id, area_id, order_number)

    # Ваш код...


        text = (f"*Спасибо за заказ!*\n"
                "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                f"Заказ №{order_number}\n"
                f"`Город: {category.name}`\n"
                f"`Район: {area.name.rstrip()}`\n"
                f"`Товар: {item.name}`\n"
                f"`Тип клада: {stash_type}`\n"
                f"`Сумма к оплате: {item.price}₽`\n"
                "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                "*Выберите удобный для вас способ оплаты:*")
        await callback.message.edit_text(text=text, reply_markup=await kb.create_payment_buttons(), parse_mode='Markdown')

        # Отправка информации о заказе администратору
        order_info = f"Пользователь: {callback.from_user.id}, Товар: {item.name}, Район: {area.name}"
        await bot.send_message(tg_admin[0], order_info)

    
    elif callback.data.startswith('pay_sbp'):
        order_number = state_data.get('order_number')  # Получение номера заказа из состояния
        item = await get_item_by_id(item_id)
        if item is None:
            await callback.answer("Товар не найден.", show_alert=True)
            return

        text = (f"<b>Ваш номер заказа - </b><code>№{order_number}</code>\n"
        "Вы зарезервировали товар на 30 минут.\n"
        "Все ранее зарезервированные заказы сняты с резерва.\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<b>Для оплаты заказа:</b>\n"
        f"Совершите перевод через СБП на сумму <u>{item.price}₽</u> по номеру:\n\n"
        f"<code>{spb_info[0]}</code>\n"
        f"{spb_info[1]}\n"
        f"{spb_info[2]}\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
        "После оплаты отправьте квитанцию боту\n"
        "и нажмите на кнопку <b>\"Проверить оплату\"</b>.\n"
        "Бот проверит оплату в течении 5 минут и автоматически выдаст координаты.\n"
        "<b>В случае проблем с оплатой обратитесь к оператору!</b>")

        await state.update_data(payment_method='sbp')
        await callback.message.edit_text(text=text, reply_markup=await kb.create_sbp_buttons(), parse_mode='HTML')
    
    elif callback.data.startswith('pay_usdt'):
        order_number = state_data.get('order_number')  # Получение номера заказа из состояния
        item = await get_item_by_id(item_id)
        if item is None:
            await callback.answer("Товар не найден.", show_alert=True)
            return

        text = (f"<b>Ваш номер заказа - </b><code>№{order_number}</code>\n"
        "Вы зарезервировали товар на 30 минут.\n"
        "Все ранее зарезервированные заказы сняты с резерва.\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<b>Для оплаты заказа:</b>\n"
        f"Совершите перевод на сумму <u>{item.price // 90}</u> USDT по кошельку:\n\n"
        f"{trc_info}\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
        "После оплаты отправьте хэш-ссылку боту\n"
        "и нажмите на кнопку <b>\"Проверить оплату\"</b>.\n"
        "Бот проверит оплату в течении 5 минут и автоматически выдаст координаты.\n"
        "<b>В случае проблем с оплатой обратитесь к оператору!</b>")

        await state.update_data(payment_method='usdt')
        await callback.message.edit_text(text=text, reply_markup=await kb.create_sbp_buttons(), parse_mode='HTML')

    elif callback.data.startswith('pay_btc'):
        order_number = state_data.get('order_number')  # Получение номера заказа из состояния
        item = await get_item_by_id(item_id)
        if item is None:
            await callback.answer("Товар не найден.", show_alert=True)
            return

        text = (f"<b>Ваш номер заказа - </b><code>№{order_number}</code>\n"
        "Вы зарезервировали товар на 30 минут.\n"
        "Все ранее зарезервированные заказы сняты с резерва.\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"<b>Для оплаты заказа:</b>\n"
        f"Совершите перевод на сумму <u>{item.price / 6000000} BTC</u> по кошельку:\n\n"
        f"{btc_info}\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
        "После оплаты отправьте хэш-ссылку боту\n"
        "и нажмите на кнопку <b>\"Проверить оплату\"</b>.\n"
        "Бот проверит оплату в течении 5 минут и автоматически выдаст координаты.\n"
        "<b>В случае проблем с оплатой обратитесь к оператору!</b>")

        await state.update_data(payment_method='btc')
        await callback.message.edit_text(text=text, reply_markup=await kb.create_sbp_buttons(), parse_mode='HTML')

async def start_check_payment(message: Message, state: FSMContext, payment_method: str, answer_text: str):
    await state.set_state(CheckPayment.user_message)
    await state.update_data(payment_method=payment_method)
    await message.answer(answer_text)

@router.callback_query(F.data.startswith('pay_'))
async def choose_payment_method(callback: CallbackQuery, state: FSMContext):
    payment_method = callback.data.split('_')[1]
    await state.update_data(payment_method=payment_method)  # сохраняем метод оплаты в состоянии
    await state.set_state(OrderProcess.payment_proof)
    await callback.answer('')
    await callback.message.edit_text('Отправьте квитанцию или хэш-ссылку: ')


@router.message(F.photo | F.text)
async def handle_payment_proof(message: Message, state: FSMContext):
    payment_proof = message.photo[-1].file_id if message.photo else message.text
    await state.update_data(payment_proof=payment_proof)  # сохраняем квитанцию или хэш-ссылку в состоянии
    state_data = await state.get_data()
    user_id = message.from_user.id
    item_id = state_data.get('item')
    area_id = state_data.get('area')
    order_number = state_data.get('order_number')
    payment_method = state_data.get('payment_method')
    payment_proof = state_data.get('payment_proof')

    # Получаем информацию о товаре, районе и городе из базы данных
    item = await get_item_by_id(item_id)
    area = await get_area_by_id(area_id)
    city = await get_category_by_id(area.category)  # предполагая, что у вас есть такая функция
    if item is None or area is None or city is None:
        await message.answer("Ошибка: товар, район или город не найден.")
        return

    # Отправляем информацию о заказе админу
    order_info = (f"*Информация о заказе*\n"
                "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                f"Заказ №`{order_number}`\n"
                f"`Город: {city.name}`\n"
                f"`Район: {area.name.rstrip()}`\n"
                f"`Товар: {item.name}`\n"
                f"`Сумма к оплате: {item.price}₽`\n"
                f"Метод оплаты: {payment_method}\n"
                "➖➖➖➖➖➖➖➖➖➖➖➖➖\n")
    if message.photo:
        await bot.send_photo(chat_id=tg_admin[0], photo=payment_proof, caption=order_info, reply_markup=await kb.create_payment_confirmation_buttons(order_number), parse_mode='Markdown')
    else:
        order_info += f", Квитанция/хэш: `{payment_proof}`"
        await bot.send_message(tg_admin[0], order_info, reply_markup=await kb.create_payment_confirmation_buttons(order_number), parse_mode='Markdown')

    await state.set_state(None)  # Используйте set_state(None) для сброса состояния




@router.callback_query(F.data == 'check_payment')
async def check_payment(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await callback.message.answer("Данные отправлены оператору. Ожидайте подтверждения.")


@router.callback_query(F.data == 'cancel_order')
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text='Выберите город или отправьте его название с большой буквы:',
                                     reply_markup=await kb.generate_cities_button())
    await callback.answer("Вы успешно отменили заказ.", show_alert=True)

@router.callback_query(F.data.startswith('another_district'))
async def another_district(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    item_id = state_data.get('item')
    item = await get_item_by_id(item_id)
    if item is None:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    await callback.message.edit_text('Выберите район: ', reply_markup=await kb.generate_areas_button(item.category))
    await callback.answer()

@router.callback_query(F.data == 'basket')
async def show_basket(callback: CallbackQuery):
    await callback.answer('Вы ещё не совершали покупку.', show_alert=True)

@router.callback_query(F.data == 'work')
async def show_feedback(callback: CallbackQuery):
    text = """
    Вакансии:
➡️🚶🏼‍♀️ПЕШИЙ КУРЬЕР: от 1200 $ в неделю 🚶🏼‍♀️
Заработай 400 тысяч уже на этой неделе
➡️🚗 ВОДИТЕЛЬ: от 1000$ до 4000$ за поездку 🚗
Заработай уже на этой неделе
➡️ Графитчик / Трафоретчик
-Оплата от 25 надписей или тэгов
1 надпись 7$
1 тэг 4$
1 наклейка 3$
➖➖➖➖➖➖➖➖➖➖➖➖➖
Обязанности:
☑️ Доставка малогабаритных товаров по городу 
☑️ Умение пользоваться смартфоном
➖➖➖➖➖➖➖➖➖➖➖➖➖
Требования:
☑️ Желание работать и зарабатывать
    """
    await callback.message.edit_text(text, reply_markup=await kb.work_keyboard())

@router.callback_query(F.data == 'to_item')
async def back_to_items(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    city_id = data.get('city')
    if city_id is not None:
        items = await get_items_by_city(city_id)
        await callback.answer('')
        await callback.message.edit_text('Выберите товар: ', reply_markup=await kb.generate_itema_button(items))
    else:
        await callback.answer('Ошибка: город не выбран.')
        
@router.callback_query(F.data == 'support_work')
async def support_work(callback: CallbackQuery):
    text = f"""
▪️Что-то пошло не так?
▪️Саппорт тебе поможет!

😎Оператор: <a href="{operator_link}">{operator_username}</a>


➖➖➖➖➖➖➖➖
Подпишитесь на ➡️ <a href="{channel_link}">НАШ КАНАЛ</a> с информацией
<a href="{image_url}">&#8205;</a>

Вступите в ➡️ <a href="{chat_link}">НАШ ЧАТ</a> с отзывами

    """
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=await kb.return_keyboarr())