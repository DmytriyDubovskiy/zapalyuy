import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram import BaseMiddleware
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from typing import Callable, Dict, Any, Awaitable, Union
from datetime import datetime, timezone

from config import API_TOKEN, OWNER_ID
from database import init_db, add_psychologist_to_db, remove_psychologist_from_db
from keyboards import main_menu, back_to_menu_button, rating_keyboard, age_verification_keyboard
from utils import is_psychologist, generate_slots, KYIV_TZ
from handlers.start import cmd_start, handle_age_verification
from handlers.menu import show_hotlines, calm_exercises, distract_exercises, library, community_chat
from handlers.feedback import show_feedbacks, handle_feedback_message, rate, FeedbackState
from handlers.consultation import consultation_menu, req_cancel, create_request, end_consultation, handle_consultation_confirmation
from handlers.cabinet import cabinet, cabinet_actions, take_request, join_active, show_requests, show_scheduled_for_psych, show_active_for_psych, show_completed_for_psych
from handlers.admin import (
    admin_panel, admin_actions, add_psychologist, remove_psychologist, 
    broadcast_command, handle_broadcast_message, BroadcastStates,
)
from handlers.exercises import handle_exercises_callback
from background import keep_alive

# Global variables
user_games = {}
feedback_states: dict[int, dict] = {}  # user_id: {consultation_id: int, rating: int}
sent_reminders = set()  # Для відстеження надісланих нагадувань
consultation_sessions = {}  # Додаємо глобальну змінну для сесій консультацій

bot_start_time = datetime.now(timezone.utc)

# Setup logging
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

class AddPsychStates(StatesGroup):
    waiting_for_psych_id = State()

class RemovePsychStates(StatesGroup):
    waiting_for_psych_id = State()

# Додати клас станів для консультації
class ConsultationStates(StatesGroup):
    waiting_for_confirmation = State()

# Register handlers
dp.message.register(cmd_start, CommandStart())
dp.message.register(handle_age_verification, F.text.in_(["Поїхали 🚀"]) | F.text.regexp(r'^\d+$'))

# Menu handlers
dp.message.register(calm_exercises, F.text == "Медитація")
dp.message.register(distract_exercises, F.text == "Вправи")
dp.message.register(show_feedbacks, F.text == "Написати відгук")
dp.message.register(show_hotlines, F.text == "Термінова допомога")

# Consultation handlers
dp.message.register(end_consultation, Command("end"))
dp.message.register(consultation_menu, F.text == "Консультація")
dp.message.register(handle_consultation_confirmation, F.text == "Зрозуміло)", ConsultationStates.waiting_for_confirmation)
dp.callback_query.register(req_cancel, F.data == "req_cancel")
dp.callback_query.register(create_request, F.data.startswith("req_"))
dp.message(Command("end"))

# Cabinet handlers
dp.message.register(cabinet, Command("cabinet"))
dp.callback_query.register(cabinet_actions, F.data.startswith("cab_"))
dp.callback_query.register(take_request, F.data.startswith("take_"))
dp.callback_query.register(join_active, F.data.startswith("join_"))

# Admin handlers
dp.message.register(admin_panel, Command("admin"))
dp.callback_query.register(admin_actions, F.data.startswith("adm_"))
dp.message.register(add_psychologist, Command("add_psych"))
dp.message.register(remove_psychologist, Command("remove_psych"))
dp.message.register(broadcast_command, Command("broadcast"))
dp.message.register(handle_broadcast_message, BroadcastStates.waiting_for_broadcast_message)
dp.message.register(add_psychologist, AddPsychStates.waiting_for_psych_id)
dp.message.register(remove_psychologist, RemovePsychStates.waiting_for_psych_id)

# Feedback handler
dp.message.register(show_feedbacks, F.text == "Написати відгук")
dp.message.register(handle_feedback_message, FeedbackState.waiting_for_feedback)
dp.message.register(rate, Command("rate"))

# Exercise callbacks
dp.callback_query.register(handle_exercises_callback, F.data.in_([
    "dis_game", "dis_exercises", "dis_links", "back_to_exercises",
    "ex_lemon", "ex_balloon", "ex_square_breath", "ex_movement"
]))

# Feedback handlers
@dp.callback_query(F.data.startswith("rate_"))
async def handle_rating(call: types.CallbackQuery, state: FSMContext):
    rating = int(call.data.split("_")[1])
    await state.update_data(rating=rating)
    
    await call.message.answer(
        f"Дякуємо за оцінку {rating}/10! Бажаєте залишити текстовий коментар? "
        "(Напишіть його або натисніть /skip щоб пропустити)",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(FeedbackState.waiting_for_comment)
    await call.answer()

dp.message.register(handle_feedback_message, FeedbackState.waiting_for_feedback)
async def handle_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    rating = data.get('rating')
    consultation_id = data.get('consultation_id')
    
    comment = message.text if message.text != "/skip" else ""
    
    # Зберігаємо відгук
    async with aiosqlite.connect("bot.db") as db:
        await db.execute(
            "INSERT INTO feedback(user_id, rating, comment) VALUES (?, ?, ?)",
            (message.from_user.id, rating, comment)
        )
        await db.commit()
    
    await state.clear()
    
    # Отримуємо інформацію про вік користувача
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute(
            "SELECT age_verified FROM users WHERE user_id = ?", 
            (message.from_user.id,)
        )
        user_data = await cursor.fetchone()
        show_consultation = user_data and user_data[0] and user_data[0] >= 14
    
    await message.answer("Дякуємо за ваш відгук! 💙", reply_markup=main_menu(show_consultation))

class MessageTimeMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[
        [Union[types.Message, types.CallbackQuery], Dict[str, Any]],
                       Awaitable[Any]], event: Union[types.Message, types.CallbackQuery],
                       data: Dict[str, Any]) -> Any:
        event_date = None

        if isinstance(event, types.Message):
            event_date = event.date
        elif isinstance(event, types.CallbackQuery) and event.message:
            event_date = event.message.date

        if event_date and event_date < bot_start_time:
            logging.info(
                f"Ignoring message from {event.from_user.id} sent before bot start"
            )
            return

        return await handler(event, data)

dp.message.middleware(MessageTimeMiddleware())
dp.callback_query.middleware(MessageTimeMiddleware())

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid in user_games:
        del user_games[uid]
    
    # Отримуємо інформацію про вік користувача
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute(
            "SELECT age_verified FROM users WHERE user_id = ?", 
            (uid,)
        )
        user_data = await cursor.fetchone()
        show_consultation = user_data and user_data[0] and user_data[0] >= 14
    
    await call.message.answer("Повертаємось до головного меню:", reply_markup=main_menu(show_consultation))
    await call.answer()

# Message handler
@dp.message()
async def all_messages_router(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Перевіряємо, чи очікуємо коментар для відгуку
    current_state = await state.get_state()
    if current_state == FeedbackState.waiting_for_comment.state:
        return
    
    # Команда для повернення в головне меню - ПЕРЕМІСТИТИ ЦЮ ПЕРЕВІРКУ ВГОРУ!
    if message.text == "/menu" or message.text == "Головне меню":
        if user_id in user_games:
            del user_games[user_id]
        if user_id in feedback_states:
            del feedback_states[user_id]
        
        # Отримуємо інформацію про вік користувача
        async with aiosqlite.connect("bot.db") as db:
            cursor = await db.execute(
                "SELECT age_verified FROM users WHERE user_id = ?", 
                (user_id,)
            )
            user_data = await cursor.fetchone()
            show_consultation = user_data and user_data[0] and user_data[0] >= 14
        
        await message.answer("Повертаємось до головного меню:", reply_markup=main_menu(show_consultation))
        return
    
    # Пропускаємо всі спеціальні команди, які вже обробляються окремими хендлерами
    special_commands = ["Зрозуміло)", "Медитація", "Вправи", "Написати відгук", 
                       "Термінова допомога", "Консультація"]
    if message.text in special_commands:
        return
    
    # Перевіряємо, чи очікуємо підтвердження консультації
    if current_state == ConsultationStates.waiting_for_confirmation.state:
        # Якщо це не "Зрозуміло", пропускаємо обробку
        if message.text != "Зрозуміло)":
            await message.answer("Будь ласка, натисніть кнопку 'Зрозуміло)' для продовження")
        return
    
    # зберігаємо юзера для імені
    try:
        async with aiosqlite.connect("bot.db") as db:
            await db.execute(
                "INSERT OR REPLACE INTO users (user_id, first_name, last_name, username) VALUES (?, ?, ?, ?)",
                (user_id, message.from_user.first_name, message.from_user.last_name, message.from_user.username)
            )
            await db.commit()
    except Exception as e:
        logging.error(f"Error saving user: {e}")

    # Якщо в активному містку — пересилаємо як текст
    if user_id in consultation_sessions:
        peer = consultation_sessions.get(user_id)
        if peer:
            try:
                if message.content_type == "text":
                    # Пересилаємо текст без префіксів
                    await bot.send_message(peer, message.text)
                elif message.content_type == "photo":
                    photo = message.photo[-1].file_id
                    await bot.send_photo(peer, photo, caption=message.caption or "")
                elif message.content_type == "voice":
                    await bot.send_voice(peer, message.voice.file_id)
                elif message.content_type == "document":
                    await bot.send_document(peer, message.document.file_id, caption=message.caption or "")
                else:
                    await bot.send_message(user_id, "⚠️ Цей тип повідомлення поки не підтримується у приватному чаті.")
            except Exception as e:
                logging.error(f"Bridge send failed: {e}")
            return

    # Не в містку — просте меню
    if message.text == "ℹ️ Допомога та правила":
        await message.answer(
            "Правила спільноти: анонімність, повага, безпека.\n\n"
            "Щоб забронювати консультацію, оберіть «Консультація».",
            reply_markup=main_menu(True)
        )
    else:
        # Отримуємо інформацію про вік користувача
        async with aiosqlite.connect("bot.db") as db:
            cursor = await db.execute(
                "SELECT age_verified FROM users WHERE user_id = ?", 
                (user_id,)
            )
            user_data = await cursor.fetchone()
            show_consultation = user_data and user_data[0] and user_data[0] >= 14
        
        await message.answer("Оберіть опцію:", reply_markup=main_menu(show_consultation))

async def is_psychologist(user_id: int) -> bool:
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT 1 FROM psychologists WHERE user_id=?", (user_id,))
        return (await cur.fetchone()) is not None

# Функція для запрошення відгуку
async def ask_for_feedback(user_id: int, consultation_id: int, bot):
    """Запросити відгук після консультації тільки у користувачів (не психологів)"""
    # Перевіряємо, чи це клієнт (не психолог)
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT 1 FROM psychologists WHERE user_id=?", (user_id,))
        is_psych = await cur.fetchone()
        
        # Також перевіряємо, чи цей користувач дійсно був клієнтом у цій консультації
        cur = await db.execute("SELECT user_id FROM consultations WHERE id=?", (consultation_id,))
        consultation = await cur.fetchone()
    
    if is_psych or not consultation or consultation[0] != user_id:
        return  # Не запитуємо відгук у психологів або якщо це не клієнт
    
    # Зберігаємо стан у глобальному словнику
    feedback_states[user_id] = {"consultation_id": consultation_id}
    
    await bot.send_message(
        user_id,
        "📝 <b>Будь ласка, оцініть проведену консультацію:</b>",
        reply_markup=rating_keyboard()
    )

async def cleanup_old_reminders():
    """Очистити нагадування для завершених консультацій"""
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT id FROM consultations WHERE status='completed'")
        completed_ids = [f"reminder_{row[0]}" for row in await cur.fetchall()]
        
        # Видаляємо нагадування для завершених консультацій
        for reminder_id in completed_ids:
            if reminder_id in sent_reminders:
                sent_reminders.remove(reminder_id)

# Background checker
async def background_checker():
    from config import SESSION_DURATION_MIN, CHECK_EVERY_SEC
    
    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            async with aiosqlite.connect("bot.db") as db:
                # Reminder logic
                cur = await db.execute(
                    "SELECT id, user_id, psychologist_id, scheduled_time FROM consultations "
                    "WHERE status='scheduled'"
                )
                for cid, uid, pid, tiso in await cur.fetchall():
                    t = datetime.fromisoformat(tiso).replace(tzinfo=timezone.utc)
                    diff = (t - now_utc).total_seconds()
                    
                    # Створюємо унікальний ідентифікатор для нагадування
                    reminder_id = f"reminder_{cid}"
                    
                    if 3500 <= diff <= 3700 and reminder_id not in sent_reminders:
                        kyiv = t.astimezone(KYIV_TZ).strftime("%d.%m %H:%M")
                        try:
                            await bot.send_message(uid, f"🔔 Нагадування: консультація о *{kyiv}* (через ~1 год).")
                        except Exception as e:
                            logging.error(f"Notify user reminder failed: {e}")
                        try:
                            await bot.send_message(pid, f"🔔 Нагадування: сесія з `{uid}` о *{kyiv}* (через ~1 год).")
                        except Exception as e:
                            logging.error(f"Notify psych reminder failed: {e}")
                        
                        # Додаємо ідентифікатор до множини надісланих нагадувань
                        sent_reminders.add(reminder_id)

                # Activate sessions
                cur = await db.execute(
                    "SELECT id, user_id, psychologist_id, scheduled_time FROM consultations "
                    "WHERE status='scheduled'"
                )
                for cid, uid, pid, tiso in await cur.fetchall():
                    t = datetime.fromisoformat(tiso).replace(tzinfo=timezone.utc)
                    if 0 <= (now_utc - t).total_seconds() <= 300:
                        await db.execute("UPDATE consultations SET status='active' WHERE id=?", (cid,))
                        await db.commit()
                        consultation_sessions[uid] = pid
                        consultation_sessions[pid] = uid
                        kyiv = t.astimezone(KYIV_TZ).strftime("%H:%M")
                        try:
                            await bot.send_message(uid, f"💬 Консультація розпочалася о {kyiv}. Можете писати психологу.")
                        except Exception as e:
                            logging.error(f"Notify user start failed: {e}")
                        try:
                            await bot.send_message(pid, f"💬 Почалася сесія з користувачем `{uid}` о {kyiv}.")
                        except Exception as e:
                            logging.error(f"Notify psych start failed: {e}")

                # Complete sessions
                cur = await db.execute(
                    "SELECT id, user_id, psychologist_id, scheduled_time FROM consultations "
                    "WHERE status='active'"
                )
                for cid, uid, pid, tiso in await cur.fetchall():
                    t = datetime.fromisoformat(tiso).replace(tzinfo=timezone.utc)
                    if (now_utc - t).total_seconds() >= SESSION_DURATION_MIN * 60:
                        await db.execute("UPDATE consultations SET status='completed' WHERE id=?", (cid,))
                        await db.commit()
                        consultation_sessions.pop(uid, None)
                        consultation_sessions.pop(pid, None)
                        
                        # Видаляємо ідентифікатор нагадування для цієї консультації
                        reminder_id = f"reminder_{cid}"
                        if reminder_id in sent_reminders:
                            sent_reminders.remove(reminder_id)
                        
                        # Запросити відгук у користувача (тільки якщо це клієнт)
                        await ask_for_feedback(uid, cid, bot)
                        
                        try:
                            await bot.send_message(uid, "✅ <b>Консультацію завершено. Дякуємо!</b>")
                        except Exception as e:
                            logging.error(f"Notify user end failed: {e}")
                        try:
                            await bot.send_message(pid, "✅ <b>Сесію завершено.</b>")
                        except Exception as e:
                            logging.error(f"Notify psych end failed: {e}")

        except Exception as e:
            logging.error(f"background_checker error: {e}")

        await asyncio.sleep(CHECK_EVERY_SEC)

# Main function
async def main():
    keep_alive()
    await init_db()
    await cleanup_old_reminders()
    asyncio.create_task(background_checker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())