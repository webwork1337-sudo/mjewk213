from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_user_main_kb(role: str):
    kb = [
        [InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")],
        [InlineKeyboardButton(text="📚 Ресурсы", callback_data="menu_resources")]
    ]
    if role == "user":
        kb.append([InlineKeyboardButton(text="👮‍♂️ Локер", callback_data="menu_locker")])
    if role in ["locker", "admin"]:
        kb.append([InlineKeyboardButton(text="⚙️ ADMIN PANEL", callback_data="enter_admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

profile_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏷 Изменить Paytag", callback_data="change_paytag")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main_menu")]
    ]
)

def get_admin_inline_kb(role: str, is_online: bool = False, show_back: bool = True):
    kb = []
    
    if role in ["locker", "admin"]:
        status_text = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
        kb.append([InlineKeyboardButton(text=f"Статус: {status_text}", callback_data="toggle_status")])
    
    kb.append([InlineKeyboardButton(text="📝 Создать Лог", callback_data="panel_log")])
    
    if role == "admin":
        kb.append([InlineKeyboardButton(text="💰 Создать Профит", callback_data="panel_profit")])
        kb.append([InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="panel_find")])
        kb.append([InlineKeyboardButton(text="📂 Активные заявки", callback_data="panel_apps")])
        kb.append([InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")])
        kb.append([InlineKeyboardButton(text="🔗 Ссылки", callback_data="admin_links")])
        # 🔥 НОВАЯ КНОПКА
        kb.append([InlineKeyboardButton(text="📚 Изменить Ресурсы", callback_data="admin_resources")])
        
    if show_back:
        kb.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

# 🔥 ДИНАМИЧЕСКАЯ КЛАВИАТУРА РЕСУРСОВ (ДЛЯ ЮЗЕРОВ)
def get_resources_links_kb(links: dict):
    kb = [
        [InlineKeyboardButton(text="💬 Chat", url=links.get("chat", "https://t.me/placeholder"))],
        [InlineKeyboardButton(text="🪵 Logs", url=links.get("logs", "https://t.me/placeholder"))],
        [InlineKeyboardButton(text="💸 Payments", url=links.get("payments", "https://t.me/placeholder"))],
        [InlineKeyboardButton(text="📢 Channel", url=links.get("channel", "https://t.me/placeholder"))],
        [InlineKeyboardButton(text="📖 Manuals", url=links.get("manuals", "https://farmteam.help"))],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# 🔥 КЛАВИАТУРА ВЫБОРА РЕСУРСА ДЛЯ РЕДАКТИРОВАНИЯ (АДМИН)
edit_resources_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💬 Chat", callback_data="edit_res_chat"),
         InlineKeyboardButton(text="🪵 Logs", callback_data="edit_res_logs")],
        [InlineKeyboardButton(text="💸 Payments", callback_data="edit_res_payments"),
         InlineKeyboardButton(text="📢 Channel", callback_data="edit_res_channel")],
        [InlineKeyboardButton(text="📖 Manuals", callback_data="edit_res_manuals")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="enter_admin_panel")]
    ]
)

links_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Создать ссылку", callback_data="link_create")],
    [InlineKeyboardButton(text="📋 Созданные ссылки", callback_data="link_list")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="enter_admin_panel")]
])

def get_links_list_kb(links):
    kb = []
    if not links:
        pass
    else:
        for link in links:
            btn_text = f"{link.name} ({link.clicks})"
            kb.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_link_{link.id}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_links")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def manage_user_kb(user_id, is_banned):
    ban_text = "🟢 Разблокировать" if is_banned else "🔴 Заблокировать"
    ban_callback = f"unban_{user_id}" if is_banned else f"ban_{user_id}"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👮‍♂️ Локер", callback_data=f"setrole_locker_{user_id}"),
             InlineKeyboardButton(text="👑 Админ", callback_data=f"setrole_admin_{user_id}")],
            [InlineKeyboardButton(text="❌ Снять права", callback_data=f"setrole_user_{user_id}")],
            [InlineKeyboardButton(text=ban_text, callback_data=ban_callback)],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="panel_find")]
        ]
    )

broadcast_confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Да, отправить", callback_data="confirm_broadcast")],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
])

def get_apps_list_kb(applicants):
    kb = []
    if not applicants:
        pass 
    else:
        for app_user in applicants:
            name = app_user.username or "Unknown"
            btn_text = f"👤 {name} | {app_user.id}"
            kb.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_app_{app_user.id}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад в панель", callback_data="enter_admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_app_decision_kb(user_id, app_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Принять", callback_data=f"app_accept_{user_id}_{app_id}")],
        [types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"app_reject_{user_id}_{app_id}")],
        [types.InlineKeyboardButton(text="🔙 К списку", callback_data="panel_apps")]
    ])

def get_lockers_list_kb(lockers):
    kb = []
    for locker in lockers:
        status_icon = "🟢" if locker.is_online else "🔴"
        status_text = "ONLINE" if locker.is_online else "OFFLINE"
        name = locker.username if locker.username else f"ID {locker.id}"
        btn_text = f"{status_icon} {name} • {status_text}"
        kb.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_locker_{locker.id}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

back_to_lockers_kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="🔙 К списку локеров", callback_data="menu_locker")]]
)

back_to_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main_menu")]]
)

cancel_inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]]
)

app_start_kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="✍🏻 Подать заявку", callback_data="reg_start")]]
)

source_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Друг", callback_data="reg_src_Друг"),
         InlineKeyboardButton(text="Реклама", callback_data="reg_src_Реклама")],
        [InlineKeyboardButton(text="Другое", callback_data="reg_src_Other")]
    ]
)

exp_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="До года", callback_data="reg_exp_<1"),
         InlineKeyboardButton(text="Больше года", callback_data="reg_exp_>1")],
        [InlineKeyboardButton(text="Нет опыта", callback_data="reg_exp_0")]
    ]
)

profit_type_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🌐 WEB", callback_data="source_WEB"), 
         InlineKeyboardButton(text="💳 Прямая", callback_data="source_Прямая")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
    ]
)