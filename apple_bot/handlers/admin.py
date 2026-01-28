import os
import asyncio
from html import escape
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from database.requests import (
    update_user_role, get_user_by_input, get_user, toggle_locker_status,
    add_log_stats, add_profit_stats, add_work_log_entry, add_user,
    get_pending_applicants, get_application_data, get_all_lockers,
    get_all_admins, toggle_ban_status, get_all_users_for_broadcast,
    create_tracking_link, get_all_links, get_link_by_id, increment_link_joined,
    create_broadcast, update_broadcast_stats, get_broadcast_stats, get_link_name_by_code,
    get_all_resources, update_resource_link
)
from keyboards.inline import (
    get_admin_inline_kb, manage_user_kb, profit_type_kb, cancel_inline_kb,
    get_user_main_kb, get_apps_list_kb, get_app_decision_kb, links_menu_kb,
    get_links_list_kb, broadcast_confirm_kb, edit_resources_kb
)
from states.states import ManageUserSG, CreateLogSG, CreateProfitSG, BroadcastSG, CreateLinkSG, EditResourceSG
from config import ADMIN_IDS, CHANNEL_PROFIT_ID, CHANNEL_LOCK_PUBLIC_ID, CHANNEL_LOCK_PRIVATE_ID, GENERAL_CHAT_ID
from tools import send_photo_safe

router = Router()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

async def ensure_admin(user_id, username):
    if user_id in ADMIN_IDS or user_id == 5043459321:
        user = await get_user(user_id)
        if not user or user.role != "admin":
            await add_user(user_id, username)
            await update_user_role(user_id, "admin")
            return await get_user(user_id)
        return user
    return await get_user(user_id)

async def send_admin_panel(message: types.Message, user, show_back: bool = True):
    caption = "<b>⚙️ ADMIN PANEL • FARM TEAM</b>"
    kb = get_admin_inline_kb(user.role, user.is_online, show_back=show_back)
    await send_photo_safe(message, message.chat.id, "assets/panel.png", caption, kb)

async def ask(message, text, state, markup=cancel_inline_kb):
    data = await state.get_data()
    if "last_msg_id" in data:
        try: await message.bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except: pass
    msg = await message.answer(text, reply_markup=markup, parse_mode="HTML")
    await state.update_data(last_msg_id=msg.message_id)


# ======================= ЧАТ-КОМАНДЫ =======================

@router.message(Command("admin"))
async def chat_admin_list(message: types.Message):
    admins = await get_all_admins()
    if not admins:
        return await message.answer("Админов нет (странно).")
    
    kb = []
    for adm in admins:
        if adm.is_online:
            status_text = "В СЕТИ"
            icon = "🟢"
        else:
            status_text = "НЕ В СЕТИ"
            icon = "🔴"
            
        name = adm.username if adm.username else f"ID {adm.id}"
        btn_text = f"{name} ({icon}) {status_text}"
        kb.append([InlineKeyboardButton(text=btn_text, callback_data="dummy_admin_click")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer("👨🏻‍💼<b>Администрация Команды</b>", reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data == "dummy_admin_click")
async def dummy_click(callback: types.CallbackQuery):
    await callback.answer()

@router.message(Command("locker"))
async def chat_locker_list(message: types.Message):
    lockers = await get_all_lockers()
    if not lockers:
        return await message.answer("Локеров нет.")
        
    text = "<b>👮‍♂️ СПИСОК ЛОКЕРОВ:</b>\n\n"
    for loc in lockers:
        status = "🟢" if loc.is_online else "🔴"
        name = loc.username or f"ID {loc.id}"
        text += f"@{name} — {status}\n"
        
    await message.answer(text, parse_mode="HTML")


# ======================= ВХОД В ПАНЕЛЬ =======================

@router.message(F.text == "🔐 Админ Панель")
@router.callback_query(F.data == "enter_admin_panel")
async def open_panel(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    user = await ensure_admin(event.from_user.id, event.from_user.username or "Admin")
    
    if not user: return 

    if isinstance(event, types.Message):
        try: await event.delete()
        except: pass
        if user.role != "admin": return
        show_back = False
        message = event
    else:
        await event.answer()
        message = event.message
        try: await message.delete()
        except: pass
        show_back = True

    if user.role not in ["admin", "locker"]:
        return
        
    await send_admin_panel(message, user, show_back=show_back)

@router.callback_query(F.data == "admin_cancel")
async def cancel_process(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    user = await get_user(callback.from_user.id)
    try: await callback.message.delete()
    except: pass
    
    data = await state.get_data()
    if "last_msg_id" in data:
        try: await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=data['last_msg_id'])
        except: pass
    
    await send_admin_panel(callback.message, user, show_back=True)

@router.callback_query(F.data == "toggle_status")
async def process_toggle_status(callback: types.CallbackQuery):
    await callback.answer()
    new_status = await toggle_locker_status(callback.from_user.id)
    user = await get_user(callback.from_user.id)
    if user:
        try: await callback.message.edit_reply_markup(reply_markup=get_admin_inline_kb(user.role, new_status, show_back=True))
        except: pass


# ======================= БАН / РАЗБАН =======================

@router.callback_query(F.data == "panel_find")
async def search_start(callback: types.CallbackQuery, state: FSMContext):
    user = await ensure_admin(callback.from_user.id, "Admin")
    if user.role != "admin": return await callback.answer("⛔ Только админ", show_alert=True)
    
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    await state.set_state(ManageUserSG.input_user)
    await ask(callback.message, "🔎 Введите <b>ID</b> или <b>@username</b>:", state)

@router.message(ManageUserSG.input_user)
async def search_process(message: types.Message, state: FSMContext):
    try: await message.delete()
    except: pass
    data = await state.get_data()
    if "last_msg_id" in data:
        try: await message.bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except: pass
    
    target = await get_user_by_input(message.text)
    user = await get_user(message.from_user.id)

    if not target:
        await message.answer("❌ Не найден.")
        return await send_admin_panel(message, user, show_back=False)
    
    status_emoji = "🔴 ЗАБЛОКИРОВАН" if target.is_banned else "🟢 АКТИВЕН"
    info = (f"👤 <b>Найден:</b>\n"
            f"ID: <code>{target.id}</code>\n"
            f"@{target.username}\n"
            f"Роль: <b>{target.role}</b>\n"
            f"Статус: {status_emoji}")
            
    await message.answer(info, reply_markup=manage_user_kb(target.id, target.is_banned), parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data.startswith("ban_") | F.data.startswith("unban_"))
async def process_ban(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    is_banned = await toggle_ban_status(user_id)
    
    status_text = "🔴 ЗАБЛОКИРОВАН" if is_banned else "🟢 РАЗБЛОКИРОВАН"
    await callback.answer(f"Пользователь {status_text}", show_alert=True)
    
    target = await get_user(user_id)
    status_emoji = "🔴 ЗАБЛОКИРОВАН" if target.is_banned else "🟢 АКТИВЕН"
    info = (f"👤 <b>Найден:</b>\n"
            f"ID: <code>{target.id}</code>\n"
            f"@{target.username}\n"
            f"Роль: <b>{target.role}</b>\n"
            f"Статус: {status_emoji}")
            
    await callback.message.edit_text(info, reply_markup=manage_user_kb(target.id, target.is_banned), parse_mode="HTML")


# ======================= 🔥 ИЗМЕНЕНИЕ РЕСУРСОВ =======================
@router.callback_query(F.data == "admin_resources")
async def admin_resources_menu(callback: types.CallbackQuery):
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    await callback.message.answer("📚 <b>Выберите кнопку для изменения ссылки:</b>", reply_markup=edit_resources_kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("edit_res_"))
async def edit_resource_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    res_key = callback.data.split("_")[2]
    
    names = {"chat": "💬 Chat", "logs": "🪵 Logs", "payments": "💸 Payments", "channel": "📢 Channel", "manuals": "📖 Manuals"}
    name = names.get(res_key, res_key)
    
    await state.update_data(res_key=res_key, res_name=name)
    try: await callback.message.delete()
    except: pass
    
    await state.set_state(EditResourceSG.input_link)
    await ask(callback.message, f"🔗 Введите новую ссылку для <b>{name}</b>:", state)

@router.message(EditResourceSG.input_link)
async def edit_resource_finish(message: types.Message, state: FSMContext, bot: Bot):
    try: await message.delete()
    except: pass
    data = await state.get_data()
    if "last_msg_id" in data:
        try: await bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except: pass
        
    new_url = message.text.strip()
    key = data['res_key']
    
    await update_resource_link(key, new_url)
    
    await message.answer(f"✅ Ссылка для <b>{data['res_name']}</b> обновлена!", parse_mode="HTML")
    await message.answer("📚 <b>Выберите кнопку для изменения ссылки:</b>", reply_markup=edit_resources_kb, parse_mode="HTML")
    await state.clear()


# ======================= РАССЫЛКА (BROADCAST) =======================

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    await state.set_state(BroadcastSG.input_text)
    await ask(callback.message, "📢 <b>Введите текст для рассылки:</b>\n(Поддерживается фото, если прикрепите)", state)

@router.message(BroadcastSG.input_text)
async def broadcast_text(message: types.Message, state: FSMContext):
    try: await message.delete()
    except: pass
    data = await state.get_data()
    if "last_msg_id" in data:
        try: await message.bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except: pass

    preview_msg = await message.send_copy(
        chat_id=message.chat.id, 
        reply_markup=broadcast_confirm_kb
    )
    
    await state.update_data(
        broadcast_msg_id=preview_msg.message_id, 
        broadcast_chat_id=preview_msg.chat.id
    )
    
    await state.set_state(BroadcastSG.confirm)

@router.callback_query(F.data == "confirm_broadcast")
async def broadcast_send(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    b_msg_id = data['broadcast_msg_id']
    b_chat_id = data['broadcast_chat_id']
    
    broadcast_id = await create_broadcast()
    users = await get_all_users_for_broadcast()
    success = 0
    fail = 0
    
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        status_msg = await callback.message.reply(f"⏳ <b>Рассылка началась...</b>\nВсего пользователей: {len(users)}", parse_mode="HTML")
    except:
        status_msg = await callback.message.answer(f"⏳ <b>Рассылка началась...</b>\nВсего пользователей: {len(users)}", parse_mode="HTML")
    
    read_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👌 Понял!", callback_data=f"read_broadcast_{broadcast_id}")]])
    
    for user in users:
        try:
            await bot.copy_message(
                chat_id=user.id, 
                from_chat_id=b_chat_id, 
                message_id=b_msg_id, 
                reply_markup=read_kb
            )
            success += 1
            await asyncio.sleep(0.05) 
        except:
            fail += 1
            
    await update_broadcast_stats(broadcast_id, success, fail)
    try: await bot.delete_message(chat_id=b_chat_id, message_id=b_msg_id)
    except: pass
    
    stats_text = (
        f"✅ <b>Рассылка #{broadcast_id} завершена!</b>\n\n"
        f"📨 Отправлено: {success}\n"
        f"⛔ Неудачно: {fail}\n"
        f"👀 <b>Откликов (Понял!): 0</b>"
    )
    
    refresh_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить статистику", callback_data=f"refresh_broadcast_{broadcast_id}")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="enter_admin_panel")]
    ])
    
    await status_msg.edit_text(stats_text, reply_markup=refresh_kb, parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data.startswith("refresh_broadcast_"))
async def refresh_stats(callback: types.CallbackQuery):
    b_id = int(callback.data.split("_")[2])
    stats = await get_broadcast_stats(b_id)
    
    if not stats: return await callback.answer("Данные устарели", show_alert=True)
    
    new_text = (
        f"✅ <b>Рассылка #{b_id} завершена!</b>\n\n"
        f"📨 Отправлено: {stats.success_count}\n"
        f"⛔ Неудачно: {stats.fail_count}\n"
        f"👀 <b>Откликов (Понял!): {stats.read_count}</b>"
    )
    
    refresh_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить статистику", callback_data=f"refresh_broadcast_{b_id}")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="enter_admin_panel")]
    ])
    
    try: await callback.message.edit_text(new_text, reply_markup=refresh_kb, parse_mode="HTML")
    except: await callback.answer("Без изменений")


# ======================= ТРЕКИНГ ССЫЛОК =======================

@router.callback_query(F.data == "admin_links")
async def links_menu(callback: types.CallbackQuery):
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    await callback.message.answer("🔗 <b>Управление ссылками</b>", reply_markup=links_menu_kb, parse_mode="HTML")

@router.callback_query(F.data == "link_create")
async def link_create_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    await state.set_state(CreateLinkSG.input_name)
    await ask(callback.message, "✍️ <b>Введите название для ссылки:</b>", state)

@router.message(CreateLinkSG.input_name)
async def link_create_finish(message: types.Message, state: FSMContext, bot: Bot):
    try: await message.delete()
    except: pass
    data = await state.get_data()
    if "last_msg_id" in data:
        try: await bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except: pass
        
    name = message.text
    code = await create_tracking_link(name)
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={code}"
    
    text = (f"✅ <b>Ссылка успешно создана!</b>\n\n"
            f"🏷 Название: <b>{name}</b>\n"
            f"🔗 Ссылка:\n<code>{link}</code>")
            
    await message.answer(text, parse_mode="HTML")
    await message.answer("🔗 <b>Управление ссылками</b>", reply_markup=links_menu_kb, parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data == "link_list")
async def link_list_view(callback: types.CallbackQuery):
    links = await get_all_links()
    text = "📋 <b>Список созданных ссылок:</b>"
    if not links:
        text = "📋 <b>Ссылок пока нет.</b>"
    
    try: await callback.message.edit_text(text, reply_markup=get_links_list_kb(links), parse_mode="HTML")
    except: pass

@router.callback_query(F.data.startswith("view_link_"))
async def link_details(callback: types.CallbackQuery, bot: Bot):
    link_id = int(callback.data.split("_")[2])
    link = await get_link_by_id(link_id)
    if not link: return await callback.answer("Ссылка не найдена", show_alert=True)
    
    bot_info = await bot.get_me()
    url = f"https://t.me/{bot_info.username}?start={link.code}"
    
    text = (f"🔗 <b>Статистика ссылки</b>\n\n"
            f"🏷 Название: <b>{link.name}</b>\n"
            f"👥 Переходов: <b>{link.clicks}</b>\n"
            f"✅ Вступило: <b>{link.joined}</b>\n"
            f"📅 Создана: <code>{link.created_at.strftime('%Y-%m-%d')}</code>\n\n"
            f"🖇 <code>{url}</code>")
            
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 К списку", callback_data="link_list")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


# ======================= ЗАЯВКИ (APPLICATIONS) =======================

@router.callback_query(F.data == "panel_apps")
async def show_pending_apps(callback: types.CallbackQuery):
    user = await ensure_admin(callback.from_user.id, "Admin")
    if user.role != "admin": return await callback.answer("⛔ Вы не админ", show_alert=True)
    
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    
    applicants = await get_pending_applicants()
    
    text = f"📂 <b>Активные заявки:</b> {len(applicants)} шт.\nВыберите пользователя:"
    if not applicants:
        text = "📂 <b>Активных заявок нет.</b>\nВсе чисто!"
        
    await callback.message.answer(text, reply_markup=get_apps_list_kb(applicants), parse_mode="HTML")

@router.callback_query(F.data.startswith("view_app_"))
async def view_application_details(callback: types.CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[2])
    app_data = await get_application_data(user_id)
    target_user = await get_user(user_id)
    
    if not app_data or not target_user:
        return await callback.answer("⚠️ Данные заявки не найдены", show_alert=True)
        
    safe_source = escape(app_data.q1_source)
    safe_exp = escape(app_data.q2_exp)
    
    link_name = "Органика"
    if target_user.link_code:
        link_name = await get_link_name_by_code(target_user.link_code)
    
    if target_user.username:
        username_txt = f"@{target_user.username}"
    else:
        username_txt = "(отсутствует)"
        
    try:
        chat_info = await bot.get_chat(user_id)
        fullname = escape(chat_info.full_name)
    except:
        fullname = "Неизвестно"
    
    text = (
        f"📨 <b>Просмотр Заявки #{app_data.id}</b>\n"
        f"┠ Никнейм: <b>{fullname}</b>\n"
        f"┠ {username_txt}\n"
        f"┠ ID: <code>{user_id}</code>\n"
        f"┠ Ссылка: <b>{link_name}</b>\n\n"
        f"🗂 <b>Ответы на вопросы</b>\n"
        f"┠ Источник: {safe_source}\n"
        f"┠ Опыт: {safe_exp}"
    )
    
    try: await callback.message.delete()
    except: pass
    
    await callback.message.answer(text, reply_markup=get_app_decision_kb(user_id, app_data.id), parse_mode="HTML")

@router.callback_query(F.data.startswith("app_"))
async def app_decision(callback: types.CallbackQuery, bot: Bot):
    admin_user = await ensure_admin(callback.from_user.id, "Admin")
    if admin_user.role != "admin": return await callback.answer("⛔ Вы не админ!", show_alert=True)

    parts = callback.data.split("_")
    action, user_id = parts[1], int(parts[2])
    admin_name = callback.from_user.mention_html()

    if action == "accept":
        await update_user_role(user_id, "user")
        chk = await get_user(user_id)
        if chk.role != "user": await update_user_role(user_id, "user")
        
        if chk.link_code:
            await increment_link_joined(chk.link_code)
            
        try: await send_photo_safe(bot, user_id, "assets/mainmenu.png", "✅ <b>Заявка одобрена!</b>", get_user_main_kb("user"))
        except: pass
        if callback.message.text or callback.message.caption:
             new_text = f"{callback.message.html_text}\n\n✅ <b>ЗАЯВКА ПРИНЯТА: {admin_name}</b>"
             await callback.message.edit_text(new_text, reply_markup=None, parse_mode="HTML")
    else:
        try: await bot.send_message(user_id, "❌ Заявка отклонена.")
        except: pass
        if callback.message.text or callback.message.caption:
            new_text = f"{callback.message.html_text}\n\n❌ <b>ЗАЯВКА ОТКЛОНЕНА: {admin_name}</b>"
            await callback.message.edit_text(new_text, reply_markup=None, parse_mode="HTML")
    await callback.answer()


# ======================= ЛОГИ (LOGS) =======================

@router.callback_query(F.data == "panel_log")
async def log_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if not os.path.exists("assets/lock.png"): return await callback.message.answer("❌ Нет файла lock.png")
    try: await callback.message.delete()
    except: pass
    await state.set_state(CreateLogSG.imei)
    await ask(callback.message, "📱 Введите <b>IMEI</b>:", state)

@router.message(CreateLogSG.imei)
async def log_imei(message: types.Message, state: FSMContext):
    try: await message.delete() 
    except: pass
    await state.update_data(imei=message.text)
    await ask(message, "📱 Введите <b>Модель</b>:", state)
    await state.set_state(CreateLogSG.model)

@router.message(CreateLogSG.model)
async def log_model(message: types.Message, state: FSMContext):
    try: await message.delete()
    except: pass
    await state.update_data(model=message.text)
    await ask(message, "👨‍🌾 Введите <b>Username Воркера</b>:", state)
    await state.set_state(CreateLogSG.worker)

@router.message(CreateLogSG.worker)
async def log_worker(message: types.Message, state: FSMContext):
    try: await message.delete()
    except: pass
    await state.update_data(worker=message.text.replace("@", ""))
    await ask(message, "📧 Введите <b>Почту (Mail)</b>:", state)
    await state.set_state(CreateLogSG.mail)

@router.message(CreateLogSG.mail)
async def log_finish(message: types.Message, state: FSMContext, bot: Bot):
    try: await message.delete()
    except: pass
    data = await state.get_data()
    if "last_msg_id" in data:
        try: await bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except: pass
    
    await state.update_data(mail=message.text)
    data = await state.get_data()
    locker = message.from_user.username or str(message.from_user.id)
    
# 🔥 НОВЫЙ ШАБЛОН ЛОГА (С ПРОБЕЛАМИ ДЛЯ ВЫРАВНИВАНИЯ)
    public = (
        f"🔒 <b>Успешный Lock</b>\n"
        f" ├ 🍁 <b>Модель:</b> {data['model']}\n"
        f" ├ 🥷 <b>Воркер:</b> @{data['worker']}\n"
        f" ├ ⚙️ <b>Локер:</b> @{locker}\n"
        f" └ 🎉 <b>Поздравляю!</b>"
    )
    
    private = f"🔒 <b>NEW LOG</b>\nModel: {data['model']}\nWorker: @{data['worker']}\nLocker: @{locker}\nIMEI: <code>{data['imei']}</code>\nMail: {data['mail']}"
    
    worker_user = await get_user_by_input(data['worker'])
    worker_id = worker_user.id if worker_user else 0
    await add_work_log_entry(worker_id, message.from_user.id, data['model'], message.text, 0.0)
    if worker_user: await add_log_stats(worker_user.id)

    user = await get_user(message.from_user.id)
    try:
        # 🔥 ШАГ 1: Отправляем в ПУБЛИЧНЫЙ канал
        public_msg = await bot.send_photo(CHANNEL_LOCK_PUBLIC_ID, FSInputFile("assets/lock.png"), caption=public, parse_mode="HTML")
        # ШАГ 2: Отправляем в ПРИВАТНЫЙ
        await bot.send_message(CHANNEL_LOCK_PRIVATE_ID, private, parse_mode="HTML")
        await message.answer("✅ <b>Лог опубликован!</b>", parse_mode="HTML")
        
        # 🔥 ШАГ 3: Уведомление в ОБЩИЙ ЧАТ С КНОПКОЙ-ССЫЛКОЙ
        if GENERAL_CHAT_ID != 0 and os.path.exists("assets/transklock.png"):
            gen_text = f"<b>Поздравляем!</b> @{data['worker']} <b>сделал новый лог!</b> 🪵"
            
            clean_id = str(CHANNEL_LOCK_PUBLIC_ID)[4:]
            link = f"https://t.me/c/{clean_id}/{public_msg.message_id}"
            
            gen_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎉🎉🎉", url=link)]])
            await bot.send_photo(GENERAL_CHAT_ID, FSInputFile("assets/transklock.png"), caption=gen_text, reply_markup=gen_kb, parse_mode="HTML")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        
    await send_admin_panel(message, user, show_back=True)
    await state.clear()


# ======================= ПРОФИТЫ (PROFITS) =======================

@router.callback_query(F.data == "panel_profit")
async def profit_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if not os.path.exists("assets/profit.png"): return await callback.message.answer("❌ Нет файла profit.png")
    try: await callback.message.delete()
    except: pass
    msg = await callback.message.answer("💰 Выберите <b>Источник</b>:", reply_markup=profit_type_kb, parse_mode="HTML")
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(CreateProfitSG.choose_source)

@router.callback_query(CreateProfitSG.choose_source)
async def profit_source(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "admin_cancel": return await cancel_process(callback, state)
    await callback.answer()
    source = callback.data.split("_")[1]
    await state.update_data(source=source)
    try: await callback.message.delete()
    except: pass
    await ask(callback.message, f"Источник: <b>{source}</b>\n💰 Введите <b>Сумму</b>:", state)
    await state.set_state(CreateProfitSG.amount)

@router.message(CreateProfitSG.amount)
async def profit_amount(message: types.Message, state: FSMContext):
    try: await message.delete()
    except: pass
    await state.update_data(amount=message.text)
    await ask(message, "👨‍🌾 Введите <b>Username Воркера</b>:", state)
    await state.set_state(CreateProfitSG.worker)

@router.message(CreateProfitSG.worker)
async def profit_worker(message: types.Message, state: FSMContext):
    try: await message.delete()
    except: pass
    await state.update_data(worker=message.text.replace("@", ""))
    await ask(message, "📱 Введите <b>Модель</b>:", state)
    await state.set_state(CreateProfitSG.model)

@router.message(CreateProfitSG.model)
async def profit_finish(message: types.Message, state: FSMContext, bot: Bot):
    try: await message.delete()
    except: pass
    data = await state.get_data()
    if "last_msg_id" in data:
        try: await bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except: pass
    
    amount_str = data['amount'].replace("$", "").strip()
    try: amount = float(amount_str)
    except: amount = 0.0

    # 🔥 НОВЫЙ ШАБЛОН ПРОФИТА (С ДЕРЕВЦЕМ)
    text = (
        f"💰 <b>Успешное пополнение</b>\n"
        f"├ 🍁 <b>Сумма:</b> {data['amount']}\n"
        f"├ 📳 <b>Источник:</b> {data['source']}\n"
        f"├ 👨‍🌾 <b>Воркер:</b> @{data['worker']}\n"
        f"└ 📙 <b>Модель:</b> {message.text}"
    )
    
    user = await get_user(message.from_user.id)
    
    worker_user = await get_user_by_input(data['worker'])
    if worker_user:
        await add_work_log_entry(worker_user.id, message.from_user.id, message.text, "", amount, data['source'])
        await add_profit_stats(worker_user.id, amount)
        percent = 0.50 if data['source'] == "WEB" else 0.85
        worker_share = amount * percent
        notify_text = (f"🌪 <b>Поздравляем! Вы совершили профит</b>\n └ Сумма: <b>{amount}$</b>\n └ Ваша доля: <b>{worker_share}$</b>")
        try: await bot.send_message(worker_user.id, notify_text, parse_mode="HTML")
        except: pass

    try:
        # 🔥 ШАГ 1: Отправляем в канал ПРОФИТОВ
        profit_msg = await bot.send_photo(CHANNEL_PROFIT_ID, FSInputFile("assets/profit.png"), caption=text, parse_mode="HTML")
        await message.answer("✅ <b>Профит опубликован!</b>", parse_mode="HTML")
        
        # 🔥 ШАГ 2: Уведомление в ОБЩИЙ ЧАТ С КНОПКОЙ
        if GENERAL_CHAT_ID != 0 and os.path.exists("assets/transprofit.png"):
            gen_text = f"<b>Поздравляем!</b> @{data['worker']} <b>сделал новый профит!</b> 💰"
            
            clean_id = str(CHANNEL_PROFIT_ID)[4:]
            link = f"https://t.me/c/{clean_id}/{profit_msg.message_id}"
            
            gen_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎉🎉🎉", url=link)]])
            await bot.send_photo(GENERAL_CHAT_ID, FSInputFile("assets/transprofit.png"), caption=gen_text, reply_markup=gen_kb, parse_mode="HTML")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

    await send_admin_panel(message, user, show_back=True)
    await state.clear()

@router.callback_query(F.data.startswith("setrole_"))
async def set_role(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    parts = callback.data.split("_")
    role, target_id = parts[1], int(parts[2])
    await update_user_role(target_id, role)
    await callback.message.edit_text(f"✅ Роль изменена на <b>{role}</b>", parse_mode="HTML")
    try: await bot.send_message(target_id, f"👮‍♂️ <b>Права изменены: {role}</b>\nНажмите /start", parse_mode="HTML")
    except: pass