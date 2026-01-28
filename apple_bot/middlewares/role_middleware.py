# middlewares/role_middleware.py
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from database.requests import get_user 

class RoleMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        # Если событие не сообщение (например, кнопка админа), пропускаем
        if not isinstance(event, Message):
            return await handler(event, data)

        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # Получаем данные пользователя из БД
        db_user = await get_user(user.id)
        
        # Инжектим роль в хэндлер
        # Если юзера нет в базе или роль не задана -> guest
        role = db_user.role if db_user else "guest"
        data['role'] = role
        data['db_user'] = db_user

        # Проверяем состояние FSM (запущена ли анкета?)
        fsm_state = data.get("state")
        current_state = await fsm_state.get_state() if fsm_state else None

        # 🛑 ЛОГИКА БЛОКИРОВКИ 🛑
        # Если юзер - Гость (или нет в базе)
        if role == "guest":
            # Разрешаем проходить ТОЛЬКО если:
            allowed = (
                event.text == "/start" or           # 1. Это команда старт
                event.text == "Оформить заявку" or  # 2. Это кнопка заявки (👈 ВОТ ЧТО МЫ ДОБАВИЛИ)
                current_state is not None           # 3. Юзер уже заполняет анкету
            )
            
            if not allowed:
                return await event.answer("Доступ закрыт. Нажмите /start для подачи заявки.")

        # Если юзер APPLICANT (подал заявку, ждет)
        if role == "applicant":
            await event.answer("Ваша заявка на рассмотрении. Ожидайте решения.")
            return # Полная блокировка

        # Если user, admin или locker -> пропускаем
        return await handler(event, data)