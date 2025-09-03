from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

def main_menu(show_consultation=True):
    buttons = []
    
    if show_consultation:
        buttons.append([KeyboardButton(text="Консультація")])
    
    buttons.extend([
        [KeyboardButton(text="Медитація")],
        [KeyboardButton(text="Вправи")],
        [KeyboardButton(text="Написати відгук")],
        [KeyboardButton(text="Термінова допомога")]
    ])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def age_verification_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Поїхали 🚀")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def back_to_menu_button():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Головне меню")]],
        resize_keyboard=True
    )

def understood_button():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Зрозуміло)")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def cabinet_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Заявки", callback_data="cab_requests")],
        [InlineKeyboardButton(text="📅 Заплановані", callback_data="cab_scheduled")],
        [InlineKeyboardButton(text="🔴 Активні", callback_data="cab_active")],
        [InlineKeyboardButton(text="✅ Завершені", callback_data="cab_completed")],
        [InlineKeyboardButton(text="🔄 Оновити", callback_data="cab_refresh")]
    ])

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Список психологів", callback_data="adm_list")],
        [InlineKeyboardButton(text="📝 Переглянути відгуки", callback_data="adm_feedbacks")],
        [InlineKeyboardButton(text="📢 Розсилка", callback_data="adm_broadcast")],
    ])

def rating_keyboard():
    """Клавіатура для оцінки від 1 до 10"""
    buttons = []
    row = []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(text=f"{i}⭐", callback_data=f"rate_{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def exercises_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Онлайн-ігри", callback_data="dis_game")],
        [InlineKeyboardButton(text="🧘‍♀️ Вправи", callback_data="dis_exercises")],
    ])

def exercises_links_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🫧 Лопай бульбашки", url="https://bubblespop.netlify.app/")],
        [InlineKeyboardButton(text="🎨 Розмальовка", url="https://share.google/x7tDo6h893JID5DVT")],
        [InlineKeyboardButton(text="🦖 Динозаврик", url="https://share.google/I9d3iCVj6lLPXa3N3")],
        [InlineKeyboardButton(text="🧪 Психологічні тести", url="https://share.google/rxVZ3vji3h8O5Kmzb")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_exercises")]
    ])

def exercises_practical_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍋 Лимон", callback_data="ex_lemon")],
        [InlineKeyboardButton(text="🎈 Повітряна кулька", callback_data="ex_balloon")],
        [InlineKeyboardButton(text="⬛️ Квадратне дихання", callback_data="ex_square_breath")],
        [InlineKeyboardButton(text="💃 Рух", callback_data="ex_movement")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_exercises")]
    ])

def exercises_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Онлайн-ігри", callback_data="dis_game")],
        [InlineKeyboardButton(text="🧘‍♀️ Практичні вправи", callback_data="dis_exercises")],
    ])

def exercises_links_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🫧 Лопай бульбашки", url="https://bubblespop.netlify.app/")],
        [InlineKeyboardButton(text="🎨 Розмальовка", url="https://share.google/x7tDo6h893JID5DVT")],
        [InlineKeyboardButton(text="🦖 Динозаврик", url="https://share.google/I9d3iCVj6lLPXa3N3")],
        [InlineKeyboardButton(text="🧪 Психологічні тести", url="https://share.google/rxVZ3vji3h8O5Kmzb")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_exercises")]
    ])

def exercises_practical_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍋 Лимон", callback_data="ex_lemon")],
        [InlineKeyboardButton(text="🎈 Повітряна кулька", callback_data="ex_balloon")],
        [InlineKeyboardButton(text="⬛️ Квадратне дихання", callback_data="ex_square_breath")],
        [InlineKeyboardButton(text="💃 Рух", callback_data="ex_movement")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_exercises")]
    ])

def instagram_keyboard():
    """Клавіатура з кнопкою Instagram"""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="📷 Наш Instagram",
            url="https://www.instagram.com/zapa.luy?igsh=MWJlMm94ODJ5Ymdp"
        )
    )
    return builder.as_markup()