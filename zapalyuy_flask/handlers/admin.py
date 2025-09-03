import asyncio
from aiogram import types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiosqlite
from keyboards import admin_kb, back_to_menu_button
from config import OWNER_ID

# Додаємо стани для адмінки
class BroadcastStates(StatesGroup):
    waiting_for_broadcast_message = State()

class AddPsychStates(StatesGroup):
    waiting_for_psych_id = State()

class RemovePsychStates(StatesGroup):
    waiting_for_psych_id = State()

async def admin_panel(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ <b>Доступ заборонено.</b>")
        return
    text = (
        "<b>Адмін-панель</b>\n\n"
        "<b>Команди:</b>\n"
        "<code>/add_psych &lt;id&gt;</code> — додати психолога\n"
        "<code>/remove_psych &lt;id&gt;</code> — видалити психолога\n"
        "<code>/broadcast</code> — розсилка повідомлення всім користувачам\n"
        "<code>/cabinet</code> — кабінет психолога (для перевірки)"
    )
    await message.answer(text, reply_markup=admin_kb())

async def admin_actions(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("⛔ Доступ заборонено.", show_alert=True)
        return

    if call.data == "adm_list":
        async with aiosqlite.connect("bot.db") as db:
            cur = await db.execute("SELECT user_id FROM psychologists ORDER BY user_id")
            ids = [str(r[0]) for r in await cur.fetchall()]
        txt = "<b>👥 Психологи:</b>\n" + ("\n".join(f"• <code>{i}</code>" for i in ids) if ids else "<i>список порожній</i>")
        await call.message.edit_text(txt, reply_markup=admin_kb())
    elif call.data == "adm_feedbacks":
        await show_feedbacks_admin(call)
    elif call.data == "adm_broadcast":
        await call.message.answer(
            "<b>📢 Розсилка</b>\n\n"
            "Надішліть повідомлення для розсилки всім користувачам:",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="❌ Скасувати розсилку")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        await state.set_state(BroadcastStates.waiting_for_broadcast_message)
        await call.answer()
    elif call.data == "adm_close":
        await call.message.delete()
        await call.answer("Закрито")

async def show_feedbacks_admin(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("⛔ Доступ заборонено.", show_alert=True)
        return

    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("""
            SELECT f.comment, f.created, u.first_name, u.username 
            FROM feedback f 
            LEFT JOIN users u ON f.user_id = u.user_id 
            ORDER BY f.created DESC 
            LIMIT 20
        """)
        feedbacks = await cur.fetchall()
    
    if not feedbacks:
        await call.message.answer("📝 Немає відгуків для перегляду.")
        return
    
    text = "<b>📝 Останні відгуки:</b>\n\n"
    for comment, created, first_name, username in feedbacks:
        user_info = f"{first_name} (@{username})" if username else first_name
        date = created.split(' ')[0] if created else "н/д"
        text += f"👤 {user_info}\n📅 {date}\n💬 {comment or 'Без коментаря'}\n\n"
        if len(text) > 3500:  # Обмеження Telegram
            text += "..."
            break
    
    await call.message.answer(text)
    await call.answer()

async def add_psychologist(message: types.Message):
    """Обробка команди /add_psych"""
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ <b>Лише власник може додавати.</b>")
        return
    
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("<b>Використання:</b> <code>/add_psych 1234567</code>")
        return
    
    pid = int(parts[1])
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT OR IGNORE INTO psychologists(user_id) VALUES(?)", (pid,))
        await db.commit()
    
    await message.answer(f"✅ <b>Додано психолога</b> <code>{pid}</code>.")

async def remove_psychologist(message: types.Message):
    """Обробка команди /remove_psych"""
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ <b>Лише власник може видаляти.</b>")
        return
    
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("<b>Використання:</b> <code>/remove_psych 1234567</code>")
        return
    
    pid = int(parts[1])
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("DELETE FROM psychologists WHERE user_id=?", (pid,))
        await db.commit()
    
    await message.answer(f"🗑 <b>Видалено психолога</b> <code>{pid}</code>.")

async def broadcast_command(message: types.Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ <b>Лише власник може робити розсилку.</b>")
        return
    
    await message.answer(
        "<b>📢 Розсилка</b>\n\n"
        "Надішліть повідомлення для розсилки всім користувачам:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="❌ Скасувати розсилку")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.set_state(BroadcastStates.waiting_for_broadcast_message)

async def handle_broadcast_message(message: types.Message, state: FSMContext, bot: Bot):
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ <b>Лише власник може робити розсилку.</b>")
        await state.clear()
        return
    
    if message.text == "❌ Скасувати розсилку":
        await message.answer("❌ <b>Розсилку скасовано.</b>", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return

    # Отримуємо всіх користувачів
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("SELECT user_id FROM users")
        users = await cursor.fetchall()
    
    total_users = len(users)
    successful = 0
    failed = 0
    
    # Відправляємо повідомлення про початок розсилки
    progress_message = await message.answer(
        f"📤 <b>Початок розсилки...</b>\n"
        f"Користувачів: {total_users}\n"
        f"Успішно: 0\n"
        f"Не вдалося: 0"
    )
    
    # Розсилаємо повідомлення всім користувачам
    for user in users:
        user_id = user[0]
        try:
            # Відправляємо повідомлення в залежності від типу
            if message.content_type == "text":
                await bot.send_message(
                    user_id, 
                    f"{message.text}"
                )
            elif message.content_type == "photo":
                await bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=f"{message.caption or ''}"
                )
            elif message.content_type == "video":
                await bot.send_video(
                    user_id,
                    message.video.file_id,
                    caption=f"{message.caption or ''}"
                )
            elif message.content_type == "document":
                await bot.send_document(
                    user_id,
                    message.document.file_id,
                    caption=f"{message.caption or ''}"
                )
            else:
                # Для інших типів повідомлень просто пересилаємо
                await message.send_copy(user_id)
            
            successful += 1
            
            # Оновлюємо прогрес кожні 10 повідомлень
            if successful % 10 == 0:
                await progress_message.edit_text(
                    f"📤 <b>Розсилка...</b>\n"
                    f"Користувачів: {total_users}\n"
                    f"Успішно: {successful}\n"
                    f"Не вдалося: {failed}"
                )
            
            # Невелика затримка, щоб не перевантажувати сервер
            await asyncio.sleep(0.1)
            
        except Exception as e:
            failed += 1
            # Логуємо помилки, але не зупиняємо розсилку
            print(f"Помилка відправки для {user_id}: {e}")
    
    # Фінальний звіт
    await progress_message.edit_text(
        f"✅ <b>Розсилка завершена!</b>\n\n"
        f"📊 <b>Результати:</b>\n"
        f"• Всього користувачів: {total_users}\n"
        f"• Успішно доставлено: {successful}\n"
        f"• Не вдалося доставити: {failed}\n"
    )

    await state.clear()