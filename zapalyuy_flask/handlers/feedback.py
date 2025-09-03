from aiogram import types
from aiogram.filters import Command
import aiosqlite
from keyboards import back_to_menu_button
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class FeedbackState(StatesGroup):
    waiting_for_feedback = State()
    waiting_for_comment = State()

async def show_feedbacks(message: types.Message, state: FSMContext):
    """Запуск механіки відгуків"""
    await message.answer(
        "Тут ти можеш написати свій відгук про наш бот або проєкт загалом 😊\n\n"
        "Пиши все, що думаєш — хороше чи погане. Ніхто не засудить!\n"
        "Бажано надіслати все одним повідомленням.",
        reply_markup=back_to_menu_button()
    )
    await state.set_state(FeedbackState.waiting_for_feedback)

async def handle_feedback_message(message: types.Message, state: FSMContext):
    """Обробка текстового відгуку"""
    feedback_text = message.text
    
    # Зберігаємо у БД
    async with aiosqlite.connect("bot.db") as db:
        await db.execute(
            "INSERT INTO feedback(user_id, comment) VALUES (?, ?)",
            (message.from_user.id, feedback_text)
        )
        await db.commit()
    
    await message.answer(
        "Дякуємо, що приділив/приділила свій час 💛  Обов’язково переглянемо твої коментарі і врахуємо їх. \n\nЗапалюємо разом! 🔥",
        reply_markup=back_to_menu_button()
    )
    await state.clear()

async def rate(message: types.Message):
    try:
        parts = message.text.split(maxsplit=2)
        rating = int(parts[1])
        comment = parts[2] if len(parts) > 2 else ""
        async with aiosqlite.connect("bot.db") as db:
            await db.execute(
                "INSERT INTO feedback(user_id, rating, comment) VALUES (?, ?, ?)",
                (message.from_user.id, rating, comment)
            )
            await db.commit()
        await message.answer("<b>Дякуємо за відгук!</b>")
    except Exception:
        await message.answer("<b>Використання:</b> <code>/rate [1-10] [коментар]</code>")
