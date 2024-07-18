from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from app.database.requests import get_all_cities, get_items_by_category, get_areas_by_category
from config import CHANNEL
from app.database.models import Category, async_session
from sqlalchemy import select

class CityCallback(CallbackData, prefix="city"):
    id: int
    name: str

class PageCallback(CallbackData, prefix="page"):
    number: int

async def generate_cities_button(page: int = 1, per_page: int = 33):
    start = (page - 1) * per_page
    end = start + per_page

    async with async_session() as session:
        result = await session.execute(
            select(Category).order_by(Category.id).offset(start).limit(per_page)
        )
        current_cities = result.scalars().all()

    keyboard = InlineKeyboardBuilder()
    for category in current_cities:
        keyboard.add(InlineKeyboardButton(text=category.name, 
                                          callback_data=f'category_{category.id}'))

    total_pages = 2

    def wrap_page_number(number: int) -> int:
        if number < 1:
            return total_pages + number
        elif number > total_pages:
            return number - total_pages
        return number

    navigation_buttons = []
    navigation_buttons.append(InlineKeyboardButton(text="<", callback_data=PageCallback(number=wrap_page_number(page-1)).pack()))
    navigation_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data=PageCallback(number=page).pack()))
    navigation_buttons.append(InlineKeyboardButton(text=">", callback_data=PageCallback(number=wrap_page_number(page+1)).pack()))  
    
    keyboard.row(*navigation_buttons)
    keyboard.row(InlineKeyboardButton(text='Мои покупки🛒', callback_data='basket'))
    keyboard.row(InlineKeyboardButton(text='Работа💰', callback_data='work'))
    keyboard.row(InlineKeyboardButton(text='Поддержка👤', callback_data='support_work'))
    keyboard.row(InlineKeyboardButton(text='Отзывы', url=CHANNEL))

    if page == 2:
        keyboard.adjust(3,3,3,2,3,2)
    else:
        keyboard.adjust(3,3,3,3,3,3,3,3,3,3,3,3,2)

    return keyboard.as_markup()

class BackCallback(CallbackData, prefix="back"):
    pass

async def generate_items_button(category_id: int):
    items = await get_items_by_category(category_id)
    keyboard = InlineKeyboardBuilder()
    for item in items:
        keyboard.add(InlineKeyboardButton(text=f"{item.name} - {item.price}₽",
                                          callback_data=f"item_{item.id}"))
    keyboard.add(InlineKeyboardButton(text='Выбрать город🏙', callback_data='to_main'))
    return keyboard.adjust(1).as_markup()

async def generate_areas_button(category_id: int):
    areas = await get_areas_by_category(category_id)
    keyboard = InlineKeyboardBuilder()
    for area in areas:
        keyboard.add(InlineKeyboardButton(text=area.name,
                                          callback_data=f"area_{area.id}"))
    keyboard.add(InlineKeyboardButton(text='Другой товар🛒', callback_data='to_item'))
    keyboard.add(InlineKeyboardButton(text='Вернуться в меню', callback_data='to_main'))
    return keyboard.adjust(1).as_markup()

async def create_confirmation_buttons():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Да", callback_data="yes"))
    keyboard.add(InlineKeyboardButton(text="Нет", callback_data="to_main"))
    keyboard.add(InlineKeyboardButton(text="Другой район", callback_data="another_district"))
    return keyboard.adjust(2, 1).as_markup()

async def generate_itema_button(items):
    keyboard = InlineKeyboardBuilder()
    for item in items:
        keyboard.add(InlineKeyboardButton(text=f"{item.name} - {item.price}₽",
                                          callback_data=f"item_{item.id}"))
    keyboard.add(InlineKeyboardButton(text='Выбрать город🏙', callback_data='to_main'))
    return keyboard.adjust(1).as_markup()

async def create_payment_buttons():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="СБП (по номеру)", callback_data='pay_sbp'))
    keyboard.add(InlineKeyboardButton(text="Tether TRC20 (USDT)", callback_data="pay_usdt"))
    keyboard.add(InlineKeyboardButton(text="Bitcoin", callback_data="pay_btc"))
    keyboard.add(InlineKeyboardButton(text="Отменить заказ", callback_data="cancel_order"))
    return keyboard.adjust(1).as_markup()

async def create_sbp_buttons():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Проверить оплату', callback_data='check_payment'))
    keyboard.add(InlineKeyboardButton(text='Отменить заказ', callback_data='cancel_order'))
    keyboard.add(InlineKeyboardButton(text='Поддержка👤', callback_data='support_work'))
    return keyboard.adjust(1).as_markup()

async def admin_keyboard():
    markup = InlineKeyboardBuilder()
    markup.add(
        InlineKeyboardButton(text='Рассылка', callback_data='newsletter'),
        InlineKeyboardButton(text='Добавить товар', callback_data='add_item'),
    )
    return markup.adjust(1).as_markup()

async def create_payment_confirmation_buttons(order_number):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Дать ответ, оплатил или нет", callback_data=f"check_payment_for_admin"))
    return keyboard.adjust(1).as_markup()

async def create_yes_no_buttons():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Да', callback_data='yes_city'))
    keyboard.add(InlineKeyboardButton(text='Нет', callback_data='no_city'))
    return keyboard.adjust(1).as_markup()

async def payment_keyboard():

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Оплачено", callback_data="paid"))
    keyboard.add(InlineKeyboardButton(text="Не оплачено", callback_data="not_paid"))
    return keyboard.adjust(2).as_markup()



async def work_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Вернуться в меню", callback_data="to_main"))
    keyboard.add(InlineKeyboardButton(text="Подать заявку👷", callback_data="not_paid"))
    return keyboard.adjust(2).as_markup()

async def return_keyboarr():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Вернуться в меню", callback_data="to_main"))
    return keyboard.adjust(1).as_markup()
    