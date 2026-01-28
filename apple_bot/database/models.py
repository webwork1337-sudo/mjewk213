import os
from sqlalchemy import BigInteger, String, Integer, Float, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from enum import Enum

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'db.sqlite3')

engine = create_async_engine(url=f'sqlite+aiosqlite:///{DB_PATH}')
async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class UserRole(str, Enum):
    GUEST = "guest"
    APPLICANT = "applicant"
    USER = "user"
    LOCKER = "locker"
    ADMIN = "admin"

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(default=UserRole.GUEST)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    
    paytag: Mapped[str] = mapped_column(String, nullable=True)
    logs_count: Mapped[int] = mapped_column(Integer, default=0)
    profits_count: Mapped[int] = mapped_column(Integer, default=0)
    
    main_balance: Mapped[float] = mapped_column(Float, default=0.0)
    total_profit: Mapped[float] = mapped_column(Float, default=0.0)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    link_code: Mapped[str] = mapped_column(String, nullable=True)

class Application(Base):
    __tablename__ = 'applications'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    q1_source: Mapped[str] = mapped_column(String)
    q2_exp: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")

class WorkLog(Base):
    __tablename__ = 'work_logs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    locker_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=True)
    model: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    profit: Mapped[float] = mapped_column(Float)
    company_percent: Mapped[float] = mapped_column(Float)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

class TrackingLink(Base):
    __tablename__ = 'tracking_links'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    code: Mapped[str] = mapped_column(String, unique=True)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    joined: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

class Broadcast(Base):
    __tablename__ = 'broadcasts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    read_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

# 🔥 НОВАЯ ТАБЛИЦА ДЛЯ ССЫЛОК НА РЕСУРСЫ
class ResourceLink(Base):
    __tablename__ = 'resource_links'
    
    key: Mapped[str] = mapped_column(String, primary_key=True) # например "chat"
    url: Mapped[str] = mapped_column(String)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"📁 Database checked at path: {DB_PATH}")