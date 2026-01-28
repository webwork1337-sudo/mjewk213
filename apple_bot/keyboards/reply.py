from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ==========================================
# 1. КНОПКИ РЕГИСТРАЦИИ
# ==========================================
application_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Оформить заявку")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

source_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Источник"), KeyboardButton(text="Друг")],
        [KeyboardButton(text="Другое")]
    ],
    resize_keyboard=True
)

exp_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="До года"), KeyboardButton(text="Больше года")],
        [KeyboardButton(text="К сожалению, нет")]
    ],
    resize_keyboard=True
)

# ==========================================
# 2. ГЛАВНОЕ МЕНЮ (Для ЛС)
# ==========================================
def get_main_menu(role: str):
    kb = [
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="👥 Рефералка"), KeyboardButton(text="📚 Ресурсы")]
    ]

    if role == "user":
        kb.append([KeyboardButton(text="👮‍♂️ Локер")])
    
    if role in ["admin", "locker"]:
        kb.append([KeyboardButton(text="🔐 Админ Панель")])
        
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

main_menu_kb = get_main_menu("user")

# ==========================================
# 3. АДМИН ПАНЕЛЬ (Умная)
# ==========================================
def get_admin_panel_kb(role: str, chat_type: str = "private"):
    keyboard = []
    
    # 1. Кнопка Лог (Есть у всех)
    keyboard.append([KeyboardButton(text="📝 Создать Лог")])
    
    # 2. Профит и Поиск (Только Админ)
    if role == "admin":
        keyboard[0].append(KeyboardButton(text="💰 Создать Профит"))
        keyboard.append([KeyboardButton(text="🔍 Найти пользователя")])
    
    # 3. Кнопка Назад (ТОЛЬКО В ЛИЧКЕ! В Группе ее не будет)
    if chat_type == "private":
        keyboard.append([KeyboardButton(text="🔙 Выйти в меню")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отмена")]],
    resize_keyboard=True
)