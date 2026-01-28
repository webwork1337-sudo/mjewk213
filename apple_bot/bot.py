import asyncio
import logging
import sys
import os

# 👇 Импортируем загрузчик кэша
from tools import load_cache_to_memory

print("🔵 1. Запуск системы...")

try:
    from aiogram import Bot, Dispatcher
    from config import BOT_TOKEN
    from database.models import async_main
    from handlers import admin, registration, user
    print("🟢 2. Импорты прошли успешно")
except ImportError as e:
    print(f"🔴 ОШИБКА ИМПОРТА: {e}")
    input("Нажми Enter чтобы выйти...")
    sys.exit()

async def main():
    print("🟡 3. Инициализация...")

    # --- ЗАГРУЗКА КЭША ФОТО (НОВОЕ) ---
    load_cache_to_memory()

    try:
        await async_main()
        print("🟢 4. База данных подключена")
    except Exception as e:
        print(f"🔴 ОШИБКА ПОДКЛЮЧЕНИЯ К БД: {e}")
        return

    try:
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()

        dp.include_router(admin.router)
        dp.include_router(registration.router)
        dp.include_router(user.router)
        
        print("🤖 5. БОТ ЗАПУЩЕН!")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
        
    except Exception as e:
        print(f"🔴 КРИТИЧЕСКАЯ ОШИБКА В MAIN: {e}")

if __name__ == "__main__":
    # Логи только WARNING, чтобы не тормозить консоль
    logging.basicConfig(level=logging.WARNING, stream=sys.stdout)
    
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Бот выключен вручную.")
    except Exception as e:
        print(f"🔴 ОШИБКА ЗАПУСКА: {e}")