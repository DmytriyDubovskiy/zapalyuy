from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from config import KYIV_TZ, WORKING_DAYS, START_HOUR, END_HOUR

def generate_slots(next_days: int = 14, max_buttons: int = 40) -> list[datetime]:
    """Генерує доступні слоти (початок сесії) у Київському часі, повертає в UTC."""
    now_kyiv = datetime.now(KYIV_TZ)
    slots_utc: list[datetime] = []
    for d in range(next_days + 1):
        day = (now_kyiv + timedelta(days=d)).date()
        weekday = (now_kyiv + timedelta(days=d)).weekday()
        if weekday not in WORKING_DAYS:
            continue
        for hour in range(START_HOUR, END_HOUR + 1):
            local_dt = datetime(day.year, day.month, day.day, hour, 0, tzinfo=KYIV_TZ)
            if local_dt <= now_kyiv:
                continue
            slots_utc.append(local_dt.astimezone(timezone.utc))
            if len(slots_utc) >= max_buttons:
                return slots_utc
    return slots_utc

async def is_psychologist(user_id: int, db) -> bool:
    cur = await db.execute("SELECT 1 FROM psychologists WHERE user_id=?", (user_id,))
    return (await cur.fetchone()) is not None