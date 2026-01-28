from database.models import User, Application, WorkLog, TrackingLink, Broadcast, ResourceLink, async_session # 🔥
from sqlalchemy import select, update, func, desc
from datetime import datetime, timedelta
import uuid

# --- USER & ADMIN MANAGEMENT ---
async def add_user(tg_id: int, username: str, link_code: str = None):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == tg_id))
        if not user:
            default_tag = f"#Fworker{str(tg_id)[-4:]}"
            session.add(User(id=tg_id, username=username, paytag=default_tag, link_code=link_code))
            await session.commit()

async def get_user(tg_id: int):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.id == tg_id))

async def get_user_by_input(user_input: str):
    async with async_session() as session:
        clean_input = user_input.replace("@", "").strip()
        if clean_input.isdigit():
            stmt = select(User).where(User.id == int(clean_input))
        else:
            stmt = select(User).where(User.username.ilike(clean_input))
        return await session.scalar(stmt)

async def update_paytag(user_id: int, new_tag: str):
    async with async_session() as session:
        if not new_tag.startswith("#"):
            new_tag = f"#{new_tag}"
        await session.execute(update(User).where(User.id == user_id).values(paytag=new_tag))
        await session.commit()

async def update_user_role(user_id: int, new_role: str):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == user_id).values(role=new_role))
        await session.commit()

async def toggle_locker_status(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == user_id))
        if user:
            new_status = not user.is_online
            user.is_online = new_status
            await session.commit()
            return new_status
        return False

async def toggle_ban_status(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == user_id))
        if user:
            user.is_banned = not user.is_banned
            await session.commit()
            return user.is_banned
    return False

# --- LIST GETTERS ---
async def get_all_lockers():
    async with async_session() as session:
        stmt = select(User).where(User.role == 'locker')
        result = await session.scalars(stmt)
        return result.all()

async def get_all_admins():
    async with async_session() as session:
        stmt = select(User).where(User.role == 'admin')
        result = await session.scalars(stmt)
        return result.all()

async def get_pending_applicants():
    async with async_session() as session:
        stmt = select(User).where(User.role == 'applicant')
        result = await session.scalars(stmt)
        return result.all()

async def get_all_users_for_broadcast():
    async with async_session() as session:
        stmt = select(User).where(User.is_banned == False)
        result = await session.scalars(stmt)
        return result.all()

# --- BROADCAST SYSTEM ---
async def create_broadcast():
    async with async_session() as session:
        new_broadcast = Broadcast()
        session.add(new_broadcast)
        await session.flush()
        b_id = new_broadcast.id
        await session.commit()
        return b_id

async def update_broadcast_stats(b_id: int, success: int, fail: int):
    async with async_session() as session:
        await session.execute(
            update(Broadcast)
            .where(Broadcast.id == b_id)
            .values(success_count=success, fail_count=fail)
        )
        await session.commit()

async def increment_broadcast_read(b_id: int):
    async with async_session() as session:
        b = await session.scalar(select(Broadcast).where(Broadcast.id == b_id))
        if b:
            b.read_count += 1
            await session.commit()

async def get_broadcast_stats(b_id: int):
    async with async_session() as session:
        return await session.scalar(select(Broadcast).where(Broadcast.id == b_id))

# --- 🔥 УПРАВЛЕНИЕ РЕСУРСАМИ (ССЫЛКИ) ---
DEFAULT_RESOURCES = {
    "chat": "https://t.me/+0kxjiHfRiARmZWYy",
    "logs": "https://t.me/+g0IVIfd3hbM3ZmRi",
    "payments": "https://t.me/+svU96gx2dkU5OTNi",
    "channel": "https://t.me/+jJlNVgh2Hw8wMzEy",
    "manuals": "https://farmteam.help"
}
async def init_resources():
    async with async_session() as session:
        # Проверяем, есть ли хоть одна запись
        first = await session.scalar(select(ResourceLink))
        if not first:
            for key, url in DEFAULT_RESOURCES.items():
                session.add(ResourceLink(key=key, url=url))
            await session.commit()

async def get_all_resources():
    async with async_session() as session:
        # Если вдруг пусто, инициализируем
        await init_resources()
        
        links = await session.scalars(select(ResourceLink))
        result = {}
        for l in links:
            result[l.key] = l.url
        return result

async def update_resource_link(key: str, new_url: str):
    async with async_session() as session:
        await session.execute(
            update(ResourceLink)
            .where(ResourceLink.key == key)
            .values(url=new_url)
        )
        await session.commit()


# --- LINK TRACKING ---
async def create_tracking_link(name: str):
    async with async_session() as session:
        code = uuid.uuid4().hex[:8]
        link = TrackingLink(name=name, code=code)
        session.add(link)
        await session.commit()
        return code

async def get_all_links():
    async with async_session() as session:
        stmt = select(TrackingLink).order_by(desc(TrackingLink.created_at))
        result = await session.scalars(stmt)
        return result.all()

async def get_link_by_id(link_id: int):
    async with async_session() as session:
        return await session.scalar(select(TrackingLink).where(TrackingLink.id == link_id))

async def increment_link_stats(code: str):
    async with async_session() as session:
        link = await session.scalar(select(TrackingLink).where(TrackingLink.code == code))
        if link:
            link.clicks += 1
            await session.commit()
            return True
        return False

async def increment_link_joined(code: str):
    async with async_session() as session:
        link = await session.scalar(select(TrackingLink).where(TrackingLink.code == code))
        if link:
            link.joined += 1
            await session.commit()
            return True
        return False

async def get_link_name_by_code(code: str):
    async with async_session() as session:
        link = await session.scalar(select(TrackingLink).where(TrackingLink.code == code))
        return link.name if link else "Неизвестно"

# --- APPLICATIONS & LOGS ---
async def get_application_data(user_id: int):
    async with async_session() as session:
        stmt = select(Application).where(Application.user_id == user_id).order_by(desc(Application.id)).limit(1)
        return await session.scalar(stmt)

async def create_application(user_id: int, q1: str, q2: str):
    async with async_session() as session:
        app = Application(user_id=user_id, q1_source=q1, q2_exp=q2)
        session.add(app)
        await session.flush()
        app_id = app.id
        await session.commit()
        return app_id

async def add_work_log_entry(worker_id: int, locker_id: int, model: str, email: str, profit: float, source: str = None):
    async with async_session() as session:
        entry = WorkLog(
            worker_id=worker_id,
            locker_id=locker_id,
            model=model,
            email=email,
            profit=profit,
            company_percent=0.5 if source == "WEB" else 0.85
        )
        session.add(entry)
        await session.commit()

async def add_log_stats(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == user_id))
        if user:
            user.logs_count += 1
            await session.commit()

async def add_profit_stats(user_id: int, amount: float):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == user_id))
        if user:
            user.profits_count += 1
            user.total_profit += amount
            await session.commit()

async def get_team_stats():
    async with async_session() as session:
        total_logs = await session.scalar(select(func.sum(User.logs_count)))
        total_profits_count = await session.scalar(select(func.sum(User.profits_count)))
        total_money = await session.scalar(select(func.sum(User.total_profit)))
        return {
            "logs": total_logs if total_logs else 0,
            "profits": total_profits_count if total_profits_count else 0,
            "money": total_money if total_money else 0.0
        }

async def get_top_worker_by_profit(days: int):
    async with async_session() as session:
        start_date = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(WorkLog.worker_id, func.sum(WorkLog.profit).label("total"))
            .where(WorkLog.created_at >= start_date)
            .group_by(WorkLog.worker_id)
            .order_by(desc("total"))
            .limit(1)
        )
        result = await session.execute(stmt)
        row = result.first()
        if row:
            user = await session.scalar(select(User).where(User.id == row[0]))
            return user.paytag if user and user.paytag else f"ID {row[0]}"
        return "Никого"

async def get_top_worker_by_logs():
    async with async_session() as session:
        stmt = select(User).order_by(desc(User.logs_count)).limit(1)
        user = await session.scalar(stmt)
        if user and user.logs_count > 0:
            return user.paytag if user.paytag else f"ID {user.id}"
        return "Никого"