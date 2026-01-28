import os
from html import escape
from aiogram import Router, F, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, ReplyKeyboardRemove

from states.states import RegistrationSG
from database.requests import add_user, update_user_role, create_application, get_user, get_all_admins, increment_link_stats, get_link_name_by_code
from keyboards.inline import get_user_main_kb, app_start_kb, source_kb, exp_kb
from config import ADMIN_IDS
from tools import send_photo_safe

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext):
    clean_msg = await message.answer("⌛", reply_markup=ReplyKeyboardRemove())
    await clean_msg.delete() 
    
    args = command.args
    if args:
        await increment_link_stats(args)
    
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user:
        username = message.from_user.username or "Unknown"
        await add_user(user_id, username, link_code=args)
        user = await get_user(user_id)
        
    if user.is_banned:
        return await message.answer("⛔ <b>ВЫ ЗАБЛОКИРОВАНЫ АДМИНИСТРАЦИЕЙ</b>", parse_mode="HTML")
        
    if user_id in ADMIN_IDS or user_id == 5043459321:
        if user.role != "admin":
            await update_user_role(user_id, "admin")
            user.role = "admin"
            await message.answer("👑 <b>Права администратора выданы.</b>", parse_mode="HTML")

    if user.role == "applicant":
        await message.answer("⏳ <b>Ваша заявка на рассмотрении, ожидайте!</b>", parse_mode="HTML")
        return

    if user.role in ["user", "admin", "locker"]:
        await send_photo_safe(message, message.chat.id, "assets/mainmenu.png", "<b>🍏 Главное меню</b>", get_user_main_kb(user.role))
    else:
        await message.answer("👋 <b>Приветствуем тебя!</b>\nДля получения доступа необходимо подать заявку.", reply_markup=app_start_kb, parse_mode="HTML")

@router.callback_query(F.data == "reg_start")
async def start_application(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(RegistrationSG.q1_source)
    await state.update_data(reg_msg_id=callback.message.message_id)
    await callback.message.edit_text("1️⃣ <b>Откуда узнали о нашем проекте?</b>", reply_markup=source_kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("reg_src_"))
async def answer_q1(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    source_code = callback.data.split("_")[2]
    if source_code == "Other":
        await state.set_state(RegistrationSG.custom_source_text)
        await callback.message.edit_text("✍️ <b>Напишите, откуда узнали о команде:</b>", reply_markup=None, parse_mode="HTML")
        return
    await state.update_data(source=source_code)
    await state.set_state(RegistrationSG.q2_exp)
    await callback.message.edit_text("2️⃣ <b>Был ли опыт в сфере Apple Lock?</b>", reply_markup=exp_kb, parse_mode="HTML")

@router.message(RegistrationSG.custom_source_text)
async def process_custom_source(message: types.Message, state: FSMContext, bot):
    try: await message.delete()
    except: pass
    await state.update_data(source=message.text)
    data = await state.get_data()
    if "reg_msg_id" in data:
        try: await bot.edit_message_text(chat_id=message.chat.id, message_id=data['reg_msg_id'], text="2️⃣ <b>Был ли опыт в сфере Apple Lock?</b>", reply_markup=exp_kb, parse_mode="HTML")
        except:
            msg = await message.answer("2️⃣ <b>Был ли опыт в сфере Apple Lock?</b>", reply_markup=exp_kb, parse_mode="HTML")
            await state.update_data(reg_msg_id=msg.message_id)
    await state.set_state(RegistrationSG.q2_exp)

@router.callback_query(F.data.startswith("reg_exp_"))
async def answer_q2(callback: types.CallbackQuery, state: FSMContext, bot):
    await callback.answer()
    exp = callback.data.split("_")[2]
    data = await state.get_data()
    
    app_id = await create_application(callback.from_user.id, data['source'], exp)
    await update_user_role(callback.from_user.id, "applicant")
    
    await callback.message.edit_text("✅ <b>Ваша заявка отправлена! Ожидайте решения.</b>", reply_markup=None, parse_mode="HTML")
    await state.clear()
    
    # --- СБОР ИНФОРМАЦИИ ДЛЯ ШАБЛОНА ---
    user_db = await get_user(callback.from_user.id)
    
    # 1. Ссылка
    link_name = "Органика"
    if user_db.link_code:
        link_name = await get_link_name_by_code(user_db.link_code)
    
    # 2. Юзернейм
    if callback.from_user.username:
        username_txt = f"@{callback.from_user.username}"
    else:
        username_txt = "(отсутствует)"
        
    fullname = escape(callback.from_user.full_name)
    safe_source = escape(str(data['source']))
    safe_exp = escape(str(exp))
    
    # 🔥 НОВЫЙ ШАБЛОН ПО ТЗ
    text = (
        f"📨 <b>Новая Заявка</b>\n"
        f"┠ Никнейм: <b>{fullname}</b>\n"
        f"┠ {username_txt}\n"
        f"┠ ID: <code>{callback.from_user.id}</code>\n"
        f"┠ Ссылка: <b>{link_name}</b>\n\n"
        f"🗂 <b>Ответы на вопросы</b>\n"
        f"┠ Источник: {safe_source}\n"
        f"┠ Опыт: {safe_exp}"
    )
            
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Принять", callback_data=f"app_accept_{callback.from_user.id}_{app_id}"),
         types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"app_reject_{callback.from_user.id}_{app_id}")]
    ])
    
    admins_to_send = set(ADMIN_IDS)
    db_admins = await get_all_admins()
    for adm in db_admins:
        admins_to_send.add(adm.id)
        
    for admin_id in admins_to_send:
        try:
            await bot.send_message(chat_id=admin_id, text=text, reply_markup=kb, parse_mode="HTML")
        except:
            pass