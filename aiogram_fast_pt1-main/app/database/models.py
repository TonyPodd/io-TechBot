from sqlalchemy import BigInteger, String, ForeignKey, LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    balance: Mapped[float] = mapped_column(default=0)
    scanned_qr: Mapped[str] = mapped_column(String(200), default='')
    phone: Mapped[str] = mapped_column(String(20), default='')
    Name: Mapped[str] = mapped_column(String(20), default= '')
    Surname: Mapped[str] = mapped_column(String(20), default=  '')
    Patronymic: Mapped[str] = mapped_column(String(20), default=   '')


class Item(Base):
    __tablename__ = 'items'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(25))
    description: Mapped[str] = mapped_column(String(120))
    price: Mapped[int] = mapped_column()
    img: Mapped[str] = mapped_column(String(120))
    
class QRCode(Base):
    __tablename__ = "qrcodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    qr_code_id: Mapped[str] = mapped_column(String(120))
    usage_limit: Mapped[int] = mapped_column()
    bonus_points: Mapped[int] = mapped_column()
    

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)