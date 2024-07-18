from app.database.models import User, Category, Item, Area, Order
from app.database.models import async_session
from sqlalchemy.orm import joinedload
from sqlalchemy import select


async def get_city_id(city_name):
    async with async_session() as session:
        result = await session.execute(select(Category).where(Category.name == city_name))
        city = result.scalar_one_or_none()
        return city.id if city else None


async def get_all_cities():
    async with async_session() as session:
        result = await session.execute(select(Category.id))
        return result.scalars().all()

async def set_item(data):
    async with async_session() as session:
        if data.get('all_cities'):
            print("Adding item to all cities")
            cities = await get_all_cities()
            for city_id in cities:
                new_item = Item(name=data['name'], category=city_id, price=data['price'])  # Привязываем к ID города
                session.add(new_item)
                print(f"Added item to city ID: {city_id}")
        else:
            new_item = Item(name=data['name'], category=data['category'], price=data['price'])  # Привязываем к ID города
            session.add(new_item)
            print(f"Added item to city ID: {data['category']}")
        
        await session.commit()
        print("All items added and committed.")





async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id = tg_id))
            await session.commit()


async def get_users():
    async with async_session() as session:
        users = await session.scalars(select(User))
        return users

async def get_items_by_category(category_id: int):
    async with async_session() as session:
        items = await session.scalars(select(Item).where(Item.category == category_id))
        return items

async def get_areas_by_category(category_id: int):
    async with async_session() as session:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if category:
            return category.area_rel
        return []

async def get_area_by_id(area_id: int):
    async with async_session() as session:
        result = await session.execute(select(Area).options(joinedload(Area.category_rel)).where(Area.id == area_id))
        area = result.scalar_one_or_none()
        return area


async def get_items_by_city(city_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Item).where(Item.category == city_id)
        )
        items = result.scalars().all()
    return items

async def get_category_by_id(city_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Category).where(Category.id == city_id)
        )
        city = result.scalar_one_or_none()
    return city

async def get_are_by_id(area_id: int):
    async with async_session() as session:
        result = await session.execute(select(Area).options(joinedload(Area.category_rel)).where(Area.id == area_id))
        area = result.scalar_one_or_none()
        return area

async def get_item_by_id(item_id: int):
    async with async_session() as session:
        result = await session.execute(select(Item).where(Item.id == item_id))
        item = result.scalar_one_or_none()
        return item

async def create_order(user_id, item_id, area_id, order_number):
    async with async_session() as session:
        new_order = Order(user_id=user_id, item_id=item_id, area_id=area_id, order_number=order_number, status='pending')
        session.add(new_order)
        await session.commit()


async def get_order_by_order_number(order_number):
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.order_number == order_number))
        order = result.scalar_one_or_none()
        return order

async def update_order_status_by_order_number(order_number, new_status):
    async with async_session() as session:
        order = await get_order_by_order_number(order_number)
        if order:
            order.status = new_status
            await session.commit()
