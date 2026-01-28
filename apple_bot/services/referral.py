# services/referral.py

async def process_log_creation(worker_id: int, profit: float, model: str):
    """
    Вызывается, когда создается лог (Локером или Админом).
    """
    worker = await get_user(worker_id)
    
    # 1. Считаем % команды и чистый профит воркера
    # Допустим, команда берет 20%
    team_share = profit * 0.2
    worker_profit = profit - team_share
    
    # 2. Обновляем баланс воркера
    await add_balance(worker_id, worker_profit)
    
    # 3. Проверка рефералки
    if worker.referrer_id:
        referrer = await get_user(worker.referrer_id)
        # Если реферер админ - скипаем (по ТЗ)
        if referrer.role != "admin":
            # 1% от лога
            ref_share = profit * 0.01 
            
            # Проверка: это первый лог?
            is_first_log = await check_if_first_log(worker_id)
            bonus = 3.0 if is_first_log else 0.0
            
            total_ref_reward = ref_share + bonus
            
            await add_referral_balance(referrer.id, total_ref_reward)
            # Уведомляем реферера
            await bot.send_message(referrer.id, f"💰 Реферальное начисление: +{total_ref_reward}$ от {worker.username}")