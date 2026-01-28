import json
import os

CACHE_FILE = "photo_cache.json"
MEMORY_CACHE = {}

# Загружаем кэш в оперативную память при старте
def load_cache_to_memory():
    global MEMORY_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                MEMORY_CACHE = json.load(f)
            print(f"🔥 Кэш загружен в память: {len(MEMORY_CACHE)} фото")
        except Exception as e:
            print(f"⚠️ Ошибка чтения кэша: {e}")

# Супер-быстрая отправка
async def send_photo_safe(message_or_bot, chat_id, path, caption, reply_markup):
    bot = message_or_bot.bot if hasattr(message_or_bot, 'bot') else message_or_bot
    
    # 1. Пытаемся взять из памяти (0.0001 сек)
    file_id = MEMORY_CACHE.get(path)
    
    if file_id:
        try:
            await bot.send_photo(chat_id, photo=file_id, caption=caption, reply_markup=reply_markup, parse_mode="HTML")
            return
        except Exception as e:
            print(f"⚠️ ID устарел или ошибка: {e}")
    
    # 2. Если ID нет (забыл прогнать скрипт) — шлем ТЕКСТ.
    # Не пытаемся грузить файл, чтобы не лагало. Лучше быстро текст, чем 13 сек тупняка.
    await bot.send_message(chat_id, text=caption, reply_markup=reply_markup, parse_mode="HTML")