import os
from aiogram import types
from keyboards import back_to_menu_button, understood_button
from handlers.emergency import EMERGENCY_PHOTO

async def show_hotlines(message: types.Message):
    """Термінова допомога з фото"""
    try:
        if os.path.exists(EMERGENCY_PHOTO):
            # Відправляємо фото без open()
            await message.answer_photo(
                photo=types.FSInputFile(EMERGENCY_PHOTO),
                caption=(
                    "Якщо тобі зараз важко або ти потребуєш термінової психологічної допомоги — ось контакти "
                    "\"<b>гарячих ліній</b>\"\n\n"
                    "Пам'ятай, ти не сам/сама ❤️‍🔥\n\n"
                ),
                reply_markup=back_to_menu_button()
            )
        else:
            raise FileNotFoundError("Файл не знайдено")
    except Exception:
        await message.answer(
            "Якщо тобі зараз важко або ти потребуєш термінової психологічної допомоги — ось контакти "
            "\"гарячих ліній\"\n\n"
            "Пам'ятай, ти не сам/сама ❤️‍🔥\n\n",
            reply_markup=back_to_menu_button()
        )

async def calm_exercises(message: types.Message):
    """Медитація"""
    await message.answer(
        "Я знаю, буває важко зупинитись, але давай спробуємо разом трохи видихнути й відпочити🫂\n\n"
        "Обери медитацію й дай собі кілька хвилин тиші👇",
        reply_markup=back_to_menu_button()
    )
    
    # Відправляємо аудіофайли медитації
    await send_meditation_audios(message)

async def send_meditation_audios(message: types.Message):
    """Відправка 3 аудіофайлів медитації"""
    meditation_files = [
        {"path": "music/morning.mp3", "title": "Ранкова медитація 'Налаштуйся на день'"},
        {"path": "music/safety place.mp3", "title": "Твоє безпечне місце"},
        {"path": "music/relaxation.mp3", "title": "М'яке розслаблення"},
    ]
    
    for audio in meditation_files:
        try:
            if os.path.exists(audio["path"]):
                # Використовуємо FSInputFile замість InputFile
                await message.answer_audio(
                    audio=types.FSInputFile(audio["path"]),
                    caption=f"<b>{audio['title']}</b>",
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    f"⚠️ Аудіофайл {audio['path']} не знайдено.\n"
                    f"<b>{audio['title']}</b>",
                    parse_mode="HTML"
                )
        except Exception as e:
            await message.answer(
                f"❌ Помилка при відправці {audio['title']}: {str(e)}"
            )
    
    await message.answer(
        "Оберіть наступну дію:",
        reply_markup=back_to_menu_button()
    )

async def distract_exercises(message: types.Message):
    """Вправи"""
    from keyboards import exercises_keyboard
    await message.answer(
        "Зібрали для тебе прості вправи й кілька прикольних розваг, щоб відволіктись🧘‍♀\n\n"
        "Обери, що цікавить:",
        reply_markup=exercises_keyboard()
    )

async def library(message: types.Message):
    await message.answer("Бібліотека функціонал", reply_markup=back_to_menu_button())

async def community_chat(message: types.Message):
    await message.answer("Чат спільноти функціонал", reply_markup=back_to_menu_button())