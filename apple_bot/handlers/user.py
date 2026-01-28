import os
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from database.requests import get_user, get_all_lockers, update_paytag, get_team_stats, get_top_worker_by_profit, get_top_worker_by_logs, increment_broadcast_read, get_all_resources # 🔥
from keyboards.inline import get_resources_links_kb, get_user_main_kb, back_to_menu_kb, get_lockers_list_kb, back_to_lockers_kb, profile_kb, cancel_inline_kb # 🔥
from states.states import ChangeTagSG
from tools import send_photo_safe

router = Router()

@router.callback_query(F.data.startswith("read_broadcast_"))
async def read_broadcast(callback: types.CallbackQuery):
    b_id = int(callback.data.split("_")[2])
    await increment_broadcast_read(b_id)
    await callback.answer("✅ Спасибо, мы учли ваш ответ!")
    try: await callback.message.edit_reply_markup(reply_markup=None)
    except: pass

@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    user = await get_user(callback.from_user.id)
    try: await callback.message.delete()
    except: pass
    
    await send_photo_safe(
        callback.message, 
        callback.from_user.id,
        "assets/mainmenu.png", 
        "<b>🍏 Главное меню</b>", 
        get_user_main_kb(user.role)
    )

@router.callback_query(F.data == "menu_profile")
async def show_profile(callback: types.CallbackQuery):
    await callback.answer()
    user = await get_user(callback.from_user.id)
    
    text = (
        f"ℹ️ <b>Информация:</b>\n"
        f" └ 🥷🏻 ID: <code>{user.id}</code>\n"
        f" └ 👁 Paytag: <b>{user.paytag}</b>\n"
        f" └ 💲 Процент: 75%\n\n"
        f"📊 <b>Статистика:</b>\n"
        f" └ 💰 Сумма профитов: {user.total_profit}$\n"
        f" └  💎 Кол.Во Профитов: {user.profits_count}\n"
        f" └  📱 Кол.Во Логов: {user.logs_count}"
    )
    
    try: await callback.message.delete()
    except: pass
    
    await send_photo_safe(callback.message, callback.from_user.id, "assets/profile.png", text, profile_kb)

@router.callback_query(F.data == "change_paytag")
async def start_change_tag(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    msg = await callback.message.answer("🏷 <b>Введите новый Paytag:</b>\n(Например: #Worker1)", reply_markup=cancel_inline_kb, parse_mode="HTML")
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(ChangeTagSG.new_tag)

@router.message(ChangeTagSG.new_tag)
async def process_new_tag(message: types.Message, state: FSMContext, bot):
    try: await message.delete()
    except: pass
    data = await state.get_data()
    if "last_msg_id" in data:
        try: await bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except: pass
        
    new_tag = message.text
    await update_paytag(message.from_user.id, new_tag)
    await message.answer(f"✅ Paytag изменен на <b>{new_tag}</b>", parse_mode="HTML")
    
    user = await get_user(message.from_user.id)
    text = (
        f"ℹ️ <b>Информация:</b>\n"
        f" └ 🥷🏻 ID: <code>{user.id}</code>\n"
        f" └ 👁 Paytag: <b>{user.paytag}</b>\n"
        f" └ 💲 Процент: 75%\n\n"
        f"📊 <b>Статистика:</b>\n"
        f" └ 💰 Сумма профитов: {user.total_profit}$\n"
        f" └  💎 Кол.Во Профитов: {user.profits_count}\n"
        f" └  📱 Кол.Во Логов: {user.logs_count}"
    )
    
    await send_photo_safe(message, message.from_user.id, "assets/profile.png", text, profile_kb)
    await state.clear()

@router.callback_query(F.data == "menu_stats")
async def show_team_stats(callback: types.CallbackQuery):
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    
    stats = await get_team_stats()
    top_week = await get_top_worker_by_profit(7)
    top_month = await get_top_worker_by_profit(30)
    top_logs = await get_top_worker_by_logs()
    
    text = (
        f"👥 <b>Статистика команды</b>\n"
        f"┠  Топ за Месяц: <b>{top_month}</b>\n"
        f"┠  Топ за Неделю: <b>{top_week}</b>\n"
        f"┠  Топ по Логам: <b>{top_logs}</b>\n"
        f"┠  Кол.Во Логов: {stats['logs']}\n"
        f"┠  Кол.Во Профитов: {stats['profits']}\n"
        f"┠ Сумма Профитов: {stats['money']}$"
    )
    
    await send_photo_safe(callback.message, callback.from_user.id, "assets/stat.png", text, back_to_menu_kb)

@router.callback_query(F.data == "menu_locker")
async def show_lockers_list(callback: types.CallbackQuery):
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    lockers = await get_all_lockers()
    caption = "<b>👮‍♂️ Список Локеров</b>\nВыберите локера, чтобы увидеть статус:"
    
    await send_photo_safe(callback.message, callback.from_user.id, "assets/locker.png", caption, get_lockers_list_kb(lockers))

@router.callback_query(F.data.startswith("view_locker_"))
async def view_locker_details(callback: types.CallbackQuery):
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    target_id = int(callback.data.split("_")[2])
    locker = await get_user(target_id)
    if not locker: return await callback.answer("Локер не найден", show_alert=True)
    status_icon = "🟢" if locker.is_online else "🔴"
    status_text = "Готов принять лог!" if locker.is_online else "Не в сети"
    name = locker.username if locker.username else f"ID {locker.id}"
    
    text = f"@{name} • {status_text} ({status_icon})"
    await callback.message.answer(text, reply_markup=back_to_lockers_kb, parse_mode="HTML")

# 🔥 ОБНОВЛЕННАЯ ФУНКЦИЯ РЕСУРСОВ
@router.callback_query(F.data == "menu_resources")
async def show_resources(callback: types.CallbackQuery):
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    
    # Получаем ссылки из БД
    links = await get_all_resources()
    
    caption = "<b>📚 Полезные ресурсы:</b>"
    
    # Генерируем клавиатуру с актуальными ссылками
    await send_photo_safe(
        callback.message, 
        callback.from_user.id, 
        "assets/resources.png", 
        caption, 
        get_resources_links_kb(links) # Используем новую функцию
    )

@router.callback_query(F.data == "menu_ref")
async def show_dev(callback: types.CallbackQuery):
    await callback.answer("🛠 Раздел отключен", show_alert=True)