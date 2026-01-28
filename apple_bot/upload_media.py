import asyncio
import os
import json
from aiogram import Bot
from aiogram.types import FSInputFile
from config import BOT_TOKEN, ADMIN_IDS

# Путь к папке с картинками
ASSETS_DIR = "assets"
CACHE_FILE = "photo_cache.json"

async def upload_all():
    print("🚀 Начинаем жесткую загрузку всех фото...")
    bot = Bot(token=BOT_TOKEN)
    
    # Берем первого админа из списка, чтобы ему кидать фотки
    target_chat_id = ADMIN_IDS[0] 
    
    cache = {}
    
    # Проверяем, есть ли папка
    if not os.path.exists(ASSETS_DIR):
        print(f"❌ Папка {ASSETS_DIR} не найдена!")
        await bot.session.close()
        return

    files = [f for f in os.listdir(ASSETS_DIR) if f.endswith(".png") or f.endswith(".jpg")]
    
    if not files:
        print("❌ В папке assets нет картинок!")
        await bot.session.close()
        return

    print(f"📸 Найдено файлов: {len(files)}")

    for filename in files:
        path = os.path.join(ASSETS_DIR, filename)
        print(f"📤 Загружаю: {filename} ...", end="")
        
        try:
            # Отправляем фото админу
            msg = await bot.send_photo(
                chat_id=target_chat_id, 
                photo=FSInputFile(path), 
                caption=f"Cache: {filename}"
            )
            
            # Получаем ID самой большой версии фото
            file_id = msg.photo[-1].file_id
            
            # Сохраняем в словарь (ключ - путь как в боте)
            # Важно: в боте мы пишем "assets/name.png", сохраняем так же
            key = f"assets/{filename}"
            cache[key] = file_id
            
            print(f" ✅ OK! ID: {file_id[:10]}...")
            
        except Exception as e:
            print(f" ❌ ОШИБКА: {e}")

    # Записываем всё в JSON
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4)
        
    print(f"\n💾 Все сохранено в {CACHE_FILE}")
    print("⚡️ Теперь бот будет летать. Запускай bot.py!")
    
    await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(upload_all())
    except KeyboardInterrupt:
        print("Стоп.")