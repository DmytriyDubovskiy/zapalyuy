from aiogram import types
from aiogram.types import FSInputFile
from keyboards import back_to_menu_button, exercises_links_keyboard, exercises_practical_keyboard
import aiosqlite

# Додайте константи з file_id фото для вправ
EXERCISE_PHOTOS = {
    "lemon": FSInputFile("pics/lemon.jpg"),
    "balloon": FSInputFile("pics/balloon.jpg"),
    "square_breath": FSInputFile("pics/square_breath.jpg"),
    "movement": FSInputFile("pics/movement.jpg")
}

async def handle_exercises_callback(call: types.CallbackQuery):
    """Обробник для кнопок вправ"""
    if call.data == "dis_game":
        # Онлайн-ігри
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🫧 Лопай бульбашки", url="https://bubblespop.netlify.app/")],
            [types.InlineKeyboardButton(text="🎨 Розмальовка", url="https://share.google/x7tDo6h893JID5DVT")],
            [types.InlineKeyboardButton(text="🦖 Динозаврик", url="https://share.google/I9d3iCVj6lLPXa3N3")],
            [types.InlineKeyboardButton(text="🧪 Психологічні тести", url="https://share.google/rxVZ3vji3h8O5Kmzb")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_exercises")]
        ])
        await call.message.answer(
            "🎮 <b>Онлайн-ігри для розслаблення:</b>\n\n"
            "Оберіть гру, яка вас зацікавить:",
            reply_markup=kb
        )

    elif call.data == "dis_exercises":
        # Практичні вправи
        await call.message.answer(
            "🧘‍♀️ <b>Практичні вправи для розслаблення:</b>\n\n"
            "Оберіть вправу, яка вам подобається:",
            reply_markup=exercises_practical_keyboard()
        )

    elif call.data == "back_to_exercises":
        # Повернення до головного меню вправ
        from keyboards import exercises_keyboard
        await call.message.answer(
            "Зібрали для тебе прості вправи й кілька прикольних розваг, щоб відволіктись🧘‍♀\n\n"
            "Обери, що цікавить:",
            reply_markup=exercises_keyboard()
        )

    # Обробка практичних вправ
    elif call.data == "ex_lemon":
        try:
            await call.message.answer_photo(
                photo=EXERCISE_PHOTOS["lemon"],
                caption="🍋 <b>Лимон</b>\n\n"
                        "Уяви, що тримаєш лимон. Стисни кулак так, ніби вичавлюєш сік, потім розслаб. "
                        "Спочатку правою, потім лівою рукою. Це допомагає відчути різницю між напругою і розслабленням.",
                reply_markup=back_to_menu_button()
            )
        except:
            await call.message.answer(
                "🍋 <b>Лимон</b>\n\n"
                "Уяви, що тримаєш лимон. Стисни кулак так, ніби вичавлюєш сік, потім розслаб. "
                "Спочатку правою, потім лівою рукою. Це допомагає відчути різницю між напругою і розслабленням.",
                reply_markup=back_to_menu_button()
            )

    elif call.data == "ex_balloon":
        try:
            await call.message.answer_photo(
                photo=EXERCISE_PHOTOS["balloon"],
                caption="🎈 <b>Повітряна кулька</b>\n\n"
                        "Поклади руки на живіт. Уяви, що він — кулька. На вдиху \"надувай\" його, на видиху — \"здувай\".",
                reply_markup=back_to_menu_button()
            )
        except:
            await call.message.answer(
                "🎈 <b>Повітряна кулька</b>\n\n"
                "Поклади руки на живіт. Уяви, що він — кулька. На вдиху \"надувай\" його, на видиху — \"здувай\".",
                reply_markup=back_to_menu_button()
            )

    elif call.data == "ex_square_breath":
        try:
            await call.message.answer_photo(
                photo=EXERCISE_PHOTOS["square_breath"],
                caption="⬛️ <b>Квадратне дихання</b>\n\n"
                        "Уяви квадрат. Дихай по його сторонам:\n\n"
                        "• вдих (рахуй до 4)\n"
                        "• затримка (рахуй до 4)\n"
                        "• видих (рахуй до 4)\n"
                        "• затримка (рахуй до 4)",
                reply_markup=back_to_menu_button()
            )
        except:
            await call.message.answer(
                "⬛️ <b>Квадратне дихання</b>\n\n"
                "Уяви квадрат. Дихай по його сторонам:\n\n"
                "• вдих (рахуй до 4)\n"
                "• затримка (рахуй до 4)\n"
                "• видих (рахуй до 4)\n"
                "• затримка (рахуй до 4)",
                reply_markup=back_to_menu_button()
            )

    elif call.data == "ex_movement":
        try:
            await call.message.answer_photo(
                photo=EXERCISE_PHOTOS["movement"],
                caption="💃 <b>Рух</b>\n\n"
                        "Стань зручно на обидві ноги. Почни м'яко трясти руками, ніби струшуєш воду з пальців. "
                        "Потім підключи плечі, ноги, все тіло. Дозволь собі «потрястися» кілька хвилин — "
                        "так ніби з тебе спадає весь зайвий стрес.",
                reply_markup=back_to_menu_button()
            )
        except:
            await call.message.answer(
                "💃 <b>Рух</b>\n\n"
                "Стань зручно на обидві ноги. Почни м'яко трясти руками, ніби струшуєш воду з пальців. "
                "Потім підключи плечі, ноги, все тіло. Дозволь собі «потрястися» кілька хвилин — "
                "так ніби з тебе спадає весь зайвий стрес.",
                reply_markup=back_to_menu_button()
            )

    await call.answer()