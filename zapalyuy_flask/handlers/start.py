from aiogram import types, F
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from keyboards import main_menu, age_verification_keyboard, understood_button, instagram_keyboard
import aiosqlite
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def cmd_start(message: types.Message):
    # Перевіряємо, чи користувач вже пройшов вікову перевірку
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute(
            "SELECT age_verified FROM users WHERE user_id = ?", 
            (message.from_user.id,)
        )
        user_data = await cursor.fetchone()
        
        # Якщо користувач вже існує і пройшов перевірку
        if user_data and user_data[0] is not None:
            await message.answer("<b>Меню:</b>", reply_markup=main_menu(user_data[0] >= 14))
            return
    
    # Якщо користувач ще не пройшов перевірку
    await message.answer(
        "<b>Привіт! 👋</b>\n\n"
        "Раді бачити тебе у нашому просторі\nТут на тебе чекає психологічна підтримка, корисні вправи, медитації та різні цікаві «фішечки», щоб відволіктися і зарядитися енергією.\n\n"
        "<b>Тисни кнопку нижче – і поїхали запалювати разом!</b> 🔥\n\n",
        reply_markup=age_verification_keyboard()
    )

async def handle_age_verification(message: types.Message):
    if message.text == "Поїхали 🚀":
        # Запитуємо вік користувача
        await message.answer(
            "Перед тим, як ми почнемо — вкажи, будь ласка, свій вік",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    
    # Перевіряємо, чи це числова відповідь на запит віку
    try:
        age = int(message.text)
        
        # Зберігаємо вік у базі даних
        async with aiosqlite.connect("bot.db") as db:
            await db.execute(
                "INSERT OR REPLACE INTO users (user_id, first_name, last_name, username, age_verified) "
                "VALUES (?, ?, ?, ?, ?)",
                (message.from_user.id, message.from_user.first_name, 
                 message.from_user.last_name, message.from_user.username, age)
            )
            await db.commit()
        
        # Відповідь в залежності від віку
        if age >= 14:
            await message.answer(
                "Супер!\n\n"
                "Тепер обирай, чим би хотів/хотіла зайнятись",
                reply_markup=main_menu(True)
            )
        else:
            # Створюємо інлайн кнопку для Instagram
            builder = InlineKeyboardBuilder()
            builder.row(
                types.InlineKeyboardButton(
                    text="📷 Наш Instagram",
                    url="https://www.instagram.com/zapa.luy?igsh=MWJlMm94ODJ5Ymdp"
                )
            )
            
            await message.answer(
                "Нам дуже шкода, але тут діють <b>вікові обмеження 🙈</b>\n\n"
                "Але не переймайся!\n"
                "Приєднуйся до нашої Instagram-сторінки — там ти точно знайдеш щось цікаве для себе",
                reply_markup=builder.as_markup()
            )
        
    except ValueError:
        await message.answer("<b>Будь ласка, введіть коректний вік (число):</b>")
        
    except ValueError:
        await message.answer("<b>Будь ласка, введіть коректний вік (число):</b>")

async def understood(message: types.Message):
    """Обробка кнопки 'Зрозуміло' після інформації про консультацію"""
    await message.answer(
        "Супер! Тепер обери зручний час для консультації:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    # Тут буде логіка вибору часу (потрібно додати)