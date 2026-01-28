# database/__init__.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

# Используем SQLite для начала (создаст файл bot.db)
engine = create_async_engine("sqlite+aiosqlite:///bot.db", echo=False)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def async_main():
    async with engine.begin() as conn:
        # Создает таблицы, если их нет
        await conn.run_sync(Base.metadata.create_all)