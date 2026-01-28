import os
from dotenv import load_dotenv

# Загружаем данные из твоего файла .env
load_dotenv()

# 1. Токен
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 2. Админы
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip().lstrip("-").isdigit()]

# 3. Вспомогательная функция
def get_int_env(key):
    value = os.getenv(key, "0")
    if value.lstrip("-").isdigit():
        return int(value)
    return 0

# 4. Каналы и чаты
ADMIN_CHAT_ID = get_int_env("ADMIN_CHAT_ID")
CHANNEL_PROFIT_ID = get_int_env("CHANNEL_PROFIT_ID")
CHANNEL_LOCK_PUBLIC_ID = get_int_env("CHANNEL_LOCK_PUBLIC_ID")
CHANNEL_LOCK_PRIVATE_ID = get_int_env("CHANNEL_LOCK_PRIVATE_ID")

# 🔥 ID ОБЩЕГО ЧАТА
GENERAL_CHAT_ID = get_int_env("GENERAL_CHAT_ID") 
# Если в .env нет переменной GENERAL_CHAT_ID, можно временно вписать число сюда руками:
if GENERAL_CHAT_ID == 0:
    GENERAL_CHAT_ID = -1003887233477