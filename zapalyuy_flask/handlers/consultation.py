from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import aiosqlite
from keyboards import understood_button, back_to_menu_button, main_menu
from datetime import datetime
from utils import generate_slots
from config import KYIV_TZ
import logging

# Додайте ці глобальні змінні
user_weekly_consultations = {}
consultation_sessions = {}

async def consultation_menu(message: types.Message, state: FSMContext):
    """Нове меню консультації"""
    user_id = message.from_user.id
    
    # Перевіряємо кількість консультацій на тиждень
    current_week = datetime.now().isocalendar()[1]
    if user_id not in user_weekly_consultations:
        user_weekly_consultations[user_id] = {'week': current_week, 'count': 0}
    
    if user_weekly_consultations[user_id]['week'] != current_week:
        user_weekly_consultations[user_id] = {'week': current_week, 'count': 0}
    
    if user_weekly_consultations[user_id]['count'] >= 3:
        await message.answer(
            "⚠️ Ти вже використав/використала максимальну кількість консультацій на цей тиждень (3).\n"
            "Спробуй наступного тижня!",
            reply_markup=back_to_menu_button()
        )
        return
    
    consultation_text = (
        "Ми раді, що ти піклуєшся про своє ментальне та психологічне здоров'я 😘\n\n"
        "<b>Графік консультацій:</b>\n\n"
        "Понеділок – Субота\n"
        "10:00 – 20:00\n\n"
        "<b>ВАЖЛИВО❗️</b>\n\n"
        "Можна отримати не більше 3 консультацій на тиждень\n\n"
        "Це потрібно, щоб ти не перевантажувався/не перевантажувалася і мав/мала час все обдумати\n\n"
        "<b>Навіщо это тобі:</b>\n\n"
        "Тут ти можеш поділитися тим, що тебе турбує 👀\n\n"
        "Наприклад, тривога, стрес, складнощі у спілкуванні з батьками або друзями, булінг чи будь-які інші переживання. "
        "Все, що важливо для тебе, можна обговорити з психологом у безпечному форматі\n\n"
        "<b>Як это буде проходити:</b>\n\n"
        "Після того як ти надішлеш свій запит, ти потрапляєш у чергу. Психолог відповість протягом 1-2 днів у робочі години, "
        "які ми вказали вище ( постарається якнайшвидше, але будь готовий/готова, що це може зайняти трохи часу )\n\n"
        "Уся консультація проходить у форматі переписки і <b>триває до години</b>.\n\n"
        "Просимо не використовувати нецензурну лексику і поважати наших спеціалістів.\n\n"
        "<b>Не переймайся, вся інформація між тобою і психологом конфіденційна і нікуди не передається ☺️🫶</b>\n\n"
        "<b>ЗВЕРНИ УВАГУ!🗣</b>\n\n"
        "Після того, як психолог підключається до розмови, він дає <b>приблизно 30 хвилин на відповідь.</b> "
        "Якщо ти не відповідаєш, консультацію доведеться завершити.\n\n"
        "Під час переписки психолог зазвичай чекає <b>10–15 хвилин між повідомленнями</b>, тому радимо виділити цю годину, "
        "не відволікатися і бути готовим/готовою відповідати, щоб консультація була максимально корисною\n\n"
        "Тисни кнопку і ставай у чергу!👌"
    )
    
    await message.answer(consultation_text, reply_markup=understood_button())
    from main import ConsultationStates
    await state.set_state(ConsultationStates.waiting_for_confirmation)

async def handle_consultation_confirmation(message: types.Message, state: FSMContext):
    if message.text == "Зрозуміло)":
        # Збільшуємо лічильник консультацій
        user_id = message.from_user.id
        current_week = datetime.now().isocalendar()[1]
        
        if user_id not in user_weekly_consultations:
            user_weekly_consultations[user_id] = {'week': current_week, 'count': 0}
        
        if user_weekly_consultations[user_id]['week'] != current_week:
            user_weekly_consultations[user_id] = {'week': current_week, 'count': 0}
        
        # Перевіряємо ліміт
        if user_weekly_consultations[user_id]['count'] >= 3:
            await message.answer(
                "⚠️ Ти вже використав/використала максимальну кількість консультацій на цей тиждень (3).\n"
                "Спробуй наступного тижня!",
                reply_markup=back_to_menu_button()
            )
            await state.clear()
            return
        
        # Показуємо доступні слоти
        await show_available_times(message)
        await state.clear()

async def show_available_times(message: types.Message):
    """Показати доступні часи для консультації"""
    try:
        slots = generate_slots()
        if not slots:
            await message.answer(
                "На жаль, наразі немає вільних слотів для запису. Спробуйте пізніше.",
                reply_markup=back_to_menu_button()
            )
            return
            
        buttons = []
        row = []
        for i, slot in enumerate(slots, start=1):
            text = slot.astimezone(KYIV_TZ).strftime("%d.%m %H:%M")
            row.append(types.InlineKeyboardButton(text=text, callback_data=f"req_{slot.isoformat()}"))
            if len(row) == 2:  # 2 кнопки в рядку
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([types.InlineKeyboardButton(text="❌ Скасувати", callback_data="req_cancel")])
        kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer("Оберіть час консультації (за Києвом):", reply_markup=kb)
        
    except Exception as e:
        logging.error(f"Error in show_available_times: {e}")
        await message.answer(
            "Сталася помилка при отриманні доступних часів.",
            reply_markup=back_to_menu_button()
        )

async def req_cancel(call: types.CallbackQuery):
    await call.message.edit_text("Скасовано")
    await call.answer()

async def create_request(call: types.CallbackQuery):
    user_id = call.from_user.id
    time_iso = call.data.replace("req_", "")
    
    try:
        scheduled_utc = datetime.fromisoformat(time_iso)
    except Exception:
        await call.answer("Помилка у виборі часу", show_alert=True)
        return

    # Збільшуємо лічильник консультацій
    current_week = datetime.now().isocalendar()[1]
    if user_id not in user_weekly_consultations:
        user_weekly_consultations[user_id] = {'week': current_week, 'count': 1}
    else:
        user_weekly_consultations[user_id]['count'] += 1

    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM consultations WHERE user_id=? AND scheduled_time=? AND status IN ('request','scheduled','active')",
            (user_id, scheduled_utc.isoformat())
        )
        exists = (await cur.fetchone())[0] > 0
        if exists:
            await call.answer("У вас уже є заявка/запланована сесія на цей час.", show_alert=True)
            return

        await db.execute(
            "INSERT INTO consultations(user_id, psychologist_id, scheduled_time, status) VALUES (?, NULL, ?, 'request')",
            (user_id, scheduled_utc.isoformat())
        )
        await db.commit()

        cur = await db.execute("SELECT user_id FROM psychologists")
        psychs = [row[0] for row in await cur.fetchall()]

    kyiv_txt = scheduled_utc.astimezone(KYIV_TZ).strftime("%d.%m.%Y %H:%M")
    await call.message.edit_text(f"✅ Заявку на консультацію створено на <b>{kyiv_txt}</b>.\nОчікуйте, поки психолог візьме її у роботу.")

    notify_text = (
        "🆕 <b>Нова заявка на консультацію!</b>\n\n"
        f"Користувач: {call.from_user.full_name}\n"
        f"User ID: `{user_id}`\n"
        f"Час (Київ): <b>{kyiv_txt}</b>\n\n"
        "Візьміть консультацію у /cabinet -> «Заявки»."
    )
    for pid in psychs:
        try:
            await call.bot.send_message(pid, notify_text)
        except Exception as e:
            logging.error(f"Notify psych {pid} failed: {e}")

async def end_consultation(message: types.Message):
    uid = message.from_user.id
    
    # Перевіряємо як в consultation_sessions, так і в базі даних
    if uid not in consultation_sessions:
        # Якщо немає в sessions, перевіряємо базу даних
        async with aiosqlite.connect("bot.db") as db:
            cur = await db.execute(
                "SELECT id FROM consultations WHERE (user_id=? OR psychologist_id=?) AND status='active'",
                (uid, uid)
            )
            consultation = await cur.fetchone()
            
            if not consultation:
                await message.answer("❌ <b>Ви не в активній консультації.</b>")
                return
            else:
                # Якщо консультація знайдена в БД, але не в sessions, додаємо її
                consultation_id = consultation[0]
                # Знаходимо peer (клієнта або психолога)
                cur = await db.execute(
                    "SELECT user_id, psychologist_id FROM consultations WHERE id=?",
                    (consultation_id,)
                )
                cons_data = await cur.fetchone()
                user_id, psychologist_id = cons_data
                
                # Визначаємо, хто є хто
                if uid == user_id:
                    consultation_sessions[uid] = psychologist_id
                    if psychologist_id:
                        consultation_sessions[psychologist_id] = uid
                else:
                    consultation_sessions[uid] = user_id
                    consultation_sessions[user_id] = uid
    
    # Знаходимо ID консультації та перевіряємо, хто завершує
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute(
            "SELECT id, user_id, psychologist_id FROM consultations WHERE (user_id=? OR psychologist_id=?) AND status='active'",
            (uid, uid)
        )
        consultation = await cur.fetchone()
        if not consultation:
            await message.answer("❌ <b>Консультацію не знайдено.</b>")
            return
            
        consultation_id, user_id, psychologist_id = consultation
        
        # Оновлюємо статус в базі даних
        await db.execute(
            "UPDATE consultations SET status='completed' WHERE id=?",
            (consultation_id,)
        )
        await db.commit()
    
    # Видаляємо з сесій
    peer = consultation_sessions.get(uid)
    consultation_sessions.pop(uid, None)
    if peer:
        consultation_sessions.pop(peer, None)
    
    # Запросити відгук у користувача (тільки якщо це клієнт завершує)
    if uid == user_id:  # Якщо завершує клієнт
        await ask_for_feedback(uid, consultation_id, message.bot)
    
    await message.answer("✅ <b>Консультацію завершено достроково.</b>")
    try:
        await message.bot.send_message(peer, "⚠️ <b>Співрозмовник завершив консультацію достроково.</b>")
    except:
        pass