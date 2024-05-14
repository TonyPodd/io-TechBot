from app.database.models import User, Item, QRCode
from app.database.models import async_session

from sqlalchemy import select

async def set_user(tg_id):
    async with async_session() as session:
        user = await  session.scalar(select(User).where(User.tg_id == tg_id))
        
        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()
            
    
async def get_all_items():
    async with async_session() as session:
        return await session.scalars(select(Item))
    
async def add_item(name, description, price, img):
    async with async_session() as session:
        session.add(Item(name=name, description=description, price=price, img=img))
        await session.commit()
        
async def get_item_by_id(id):
    async with async_session() as session:
        return await session.get(Item, id)
    
async def get_user_by_id(tg_id):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))
        
async def delete_item(id):
    async with async_session() as session:
        item = await session.get(Item, id)
        if item:
            await session.delete(item)
            await session.commit()
        else:
            print(f"Товар с id={id} не найден.")
            
async def is_user_registered(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user.Name != '' and user.Surname != '' and user.phone != ''

 
async def set_user_phone(tg_id, phone):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.phone = phone
        await session.commit()
        
async def get_user_phone(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user.phone
    
async def set_user_name(tg_id, name, surname):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.Name = name
        user.Surname = surname
        await session.commit()
        
async def register_user(tg_id, username, surname, patronymic, phone):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.Name = username
        user.Surname = surname
        user.Patronymic = patronymic
        user.phone = phone
        await session.commit()

async def get_user_balance(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user.balance
    
async def set_user_balance(tg_id, balance):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        user.balance = balance
        await session.commit()
        
async def is_qr_code_scaned_by_user(tg_id, qr_code_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return str(qr_code_id) in user.scanned_qr.split(',')
    
async def set_user_scanned_qr(tg_id, qr_code_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user.scanned_qr:
            user.scanned_qr += f',{qr_code_id}'
        else:
            user.scanned_qr = qr_code_id
        # user.scanned_qr += f',{qr_code_id}'
        await session.commit()
        
        
async def add_qr_code(usage_limit: int, bonus_points: int, qr_code_id: str):
    async with async_session() as session:
        qr_code = QRCode(qr_code_id =qr_code_id, usage_limit=usage_limit, bonus_points=bonus_points)
        session.add(qr_code)
        await session.commit()
        return qr_code

async def get_qr_code_by_id(qr_code_id: int):
    async with async_session() as session:
        return await session.get(QRCode, qr_code_id)

async def get_last_qr_code_id():
    async with async_session() as session:
        if (await session.scalars(select(QRCode.id).order_by(QRCode.id.desc()).limit(1))).first():
            return (await session.scalars(select(QRCode.id).order_by(QRCode.id.desc()).limit(1))).first()
        return 0
    
async def get_usage_limit_by_id(qr_code_id: int):
    async with async_session() as session:
        return (await session.scalars(select(QRCode.usage_limit).where(QRCode.id == qr_code_id))).first()
    
async def set_usage_limit_by_id(qr_code_id: int, usage_limit: int):
    async with async_session() as session:
        qr_code = await session.get(QRCode, qr_code_id)
        qr_code.usage_limit = usage_limit
        await session.commit()
        
        