from aiogram import types, F
import aiosqlite
import logging
from datetime import datetime
from keyboards import cabinet_kb
from utils import KYIV_TZ

async def cabinet(message: types.Message):
    uid = message.from_user.id
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT 1 FROM psychologists WHERE user_id=?", (uid,))
        ok = await cur.fetchone()
    if not ok:
        await message.answer("⛔ Доступ лише для психологів.")
        return
    await message.answer("👩‍⚕️ <b>Кабінет психолога</b>", reply_markup=cabinet_kb())

async def cabinet_actions(call: types.CallbackQuery):
    uid = call.from_user.id
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT 1 FROM psychologists WHERE user_id=?", (uid,))
        ok = await cur.fetchone()
    if not ok:
        await call.answer("⛔ Доступ лише для психологів.", show_alert=True)
        return

    action = call.data
    if action == "cab_refresh":
        await call.message.edit_text("👩‍⚕️ <b>Кабінет психолога</b>", reply_markup=cabinet_kb())
        await call.answer("Оновлено")
        return

    if action == "cab_requests":
        await show_requests(call)
    elif action == "cab_scheduled":
        await show_scheduled_for_psych(call, uid)
    elif action == "cab_active":
        await show_active_for_psych(call, uid)
    elif action == "cab_completed":
        await show_completed_for_psych(call, uid)

async def show_requests(call: types.CallbackQuery):
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute(
            "SELECT c.id, c.user_id, c.scheduled_time, u.first_name, u.last_name "
            "FROM consultations c LEFT JOIN users u ON u.user_id=c.user_id "
            "WHERE c.status='request' ORDER BY c.scheduled_time"
        )
        rows = await cur.fetchall()

    if not rows:
        await call.message.edit_text("📝 Заявок немає.", reply_markup=cabinet_kb())
        return

    text = "📝 <b>Заявки:</b>\n\n"
    buttons = []
    for cid, uid, tiso, fn, ln in rows:
        kyiv = datetime.fromisoformat(tiso).astimezone(KYIV_TZ).strftime("%d.%m %H:%M")
        name = f"{fn or ''} {ln or ''}".strip() or f"User {uid}"
        text += f"• {kyiv} — {name} (`{uid}`)\n"
        buttons.append([types.InlineKeyboardButton(text=f"Взяти #{cid}", callback_data=f"take_{cid}")])
    buttons.append([types.InlineKeyboardButton(text="↩️ Назад", callback_data="cab_refresh")])
    await call.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))

async def take_request(call: types.CallbackQuery):
    psych_id = call.from_user.id
    cid = int(call.data.replace("take_", ""))

    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT user_id, scheduled_time, status FROM consultations WHERE id=?", (cid,))
        row = await cur.fetchone()
        if not row:
            await call.answer("Заявку не знайдено.", show_alert=True)
            return
        user_id, tiso, status = row
        if status != "request":
            await call.answer("Цю заявку вже взято.", show_alert=True)
            return

        await db.execute(
            "UPDATE consultations SET psychologist_id=?, status='scheduled' WHERE id=?",
            (psych_id, cid)
        )
        await db.commit()

    kyiv_txt = datetime.fromisoformat(tiso).astimezone(KYIV_TZ).strftime("%d.%m.%Y %H:%M")
    await call.answer("Ви взяли консультацію.")
    await call.message.edit_text("✅ Заявку прийнято. Перевірте «Заплановані».", reply_markup=cabinet_kb())

    try:
        await call.bot.send_message(user_id, f"✅ Вашу консультацію на <b>{kyiv_txt}</b> взяв психолог. До зустрічі!")
    except Exception as e:
        logging.error(f"Notify user fail: {e}")
    try:
        await call.bot.send_message(psych_id, f"📅 Консультацію #{cid} призначено на <b>{kyiv_txt}</b>. Клієнт: `{user_id}`")
    except Exception as e:
        logging.error(f"Notify psych fail: {e}")

async def show_scheduled_for_psych(call: types.CallbackQuery, psych_id: int):
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute(
            "SELECT id, user_id, scheduled_time FROM consultations "
            "WHERE status='scheduled' AND psychologist_id=? ORDER BY scheduled_time",
            (psych_id,)
        )
        rows = await cur.fetchall()

    if not rows:
        await call.message.edit_text("📅 Немає запланованих.", reply_markup=cabinet_kb())
        return

    text = "📅 <b>Заплановані:</b>\n\n"
    for cid, uid, tiso in rows:
        kyiv = datetime.fromisoformat(tiso).astimezone(KYIV_TZ).strftime("%d.%m %H:%M")
        text += f"• {kyiv} — user `{uid}` (#{cid})\n"
    await call.message.edit_text(text, reply_markup=cabinet_kb())

async def show_active_for_psych(call: types.CallbackQuery, psych_id: int):
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute(
            "SELECT id, user_id, scheduled_time FROM consultations "
            "WHERE status='active' AND psychologist_id=? ORDER BY scheduled_time DESC",
            (psych_id,)
        )
        rows = await cur.fetchall()

    if not rows:
        await call.message.edit_text("🔴 Немає активних.", reply_markup=cabinet_kb())
        return

    text = "🔴 <b>Активні сесії:</b>\n\n"
    buttons = []
    for cid, uid, tiso in rows:
        kyiv = datetime.fromisoformat(tiso).astimezone(KYIV_TZ).strftime("%H:%M")
        text += f"• user `{uid}` (початок {kyiv})  #{cid}\n"
        buttons.append([types.InlineKeyboardButton(text=f"💬 Приєднатися до #{cid}", callback_data=f"join_{cid}")])
    buttons.append([types.InlineKeyboardButton(text="↩️ Назад", callback_data="cab_refresh")])
    await call.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))

async def join_active(call: types.CallbackQuery):
    psych_id = call.from_user.id
    cid = int(call.data.replace("join_", ""))

    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute(
            "SELECT user_id, psychologist_id, status FROM consultations WHERE id=?",
            (cid,)
        )
        row = await cur.fetchone()
    if not row:
        await call.answer("Не знайдено.", show_alert=True)
        return

    user_id, p_id, status = row
    if status != "active" or p_id != psych_id:
        await call.answer("Сесія не активна або не ваша.", show_alert=True)
        return

    from handlers.consultation import consultation_sessions
    consultation_sessions[user_id] = psych_id
    consultation_sessions[psych_id] = user_id

    await call.answer("Приєднано до чату.")
    await call.message.answer(f"Ви приєдналися до чату з користувачем `{user_id}`.")
    try:
        await call.bot.send_message(user_id, "👨‍⚕️ Психолог приєднався до чату. Можете писати. Для дострокового завершення надішліть /end")
    except Exception as e:
        logging.error(f"Notify client fail: {e}")

async def show_completed_for_psych(call: types.CallbackQuery, psych_id: int):
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute(
            "SELECT id, user_id, scheduled_time FROM consultations "
            "WHERE status='completed' AND psychologist_id=? ORDER BY scheduled_time DESC LIMIT 15",
            (psych_id,)
        )
        rows = await cur.fetchall()

    if not rows:
        await call.message.edit_text("✅ Ще немає завершених.", reply_markup=cabinet_kb())
        return

    text = "✅ <b>Завершені (останні 15):</b>\n\n"
    for cid, uid, tiso in rows:
        kyiv = datetime.fromisoformat(tiso).astimezone(KYIV_TZ).strftime("%d.%m %H:%M")
        text += f"• {kyiv} — user `{uid}` (#{cid})\n"
    await call.message.edit_text(text, reply_markup=cabinet_kb())