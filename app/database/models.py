from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from typing import List
from sqlalchemy import delete

ENGINE = 'sqlite+aiosqlite:///db.sqlite3'

ECHO = True

engine = create_async_engine(url=ENGINE, echo=ECHO)
async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    order_rel: Mapped[List['Order']] = relationship('Order', back_populates='user_rel')

class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    item_rel: Mapped[List['Item']] = relationship(back_populates='category_rel')
    area_rel: Mapped[List['Area']] = relationship('Area', back_populates='category_rel', lazy='selectin')  # one-to-many relationship

class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    price: Mapped[int] = mapped_column()
    category: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    category_rel: Mapped['Category'] = relationship(back_populates='item_rel')
    order_rel: Mapped[List['Order']] = relationship('Order', back_populates='item_rel')

class Area(Base):
    __tablename__ = 'areas'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    category: Mapped[int] = mapped_column(ForeignKey('categories.id'))  # foreign key
    category_rel: Mapped['Category'] = relationship('Category', back_populates='area_rel')  # many-to-one relationship
    order_rel: Mapped[List['Order']] = relationship('Order', back_populates='area_rel')

class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[int] = mapped_column()  # новый столбец order_number
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    item_id: Mapped[int] = mapped_column(ForeignKey('items.id'))
    area_id: Mapped[int] = mapped_column(ForeignKey('areas.id'))
    status: Mapped[str] = mapped_column(String(50))  # Например, 'pending', 'paid', 'delivered' и т.д.
    user_rel: Mapped['User'] = relationship('User', back_populates='order_rel')
    item_rel: Mapped['Item'] = relationship('Item', back_populates='order_rel')
    area_rel: Mapped['Area'] = relationship('Area', back_populates='order_rel')



async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
