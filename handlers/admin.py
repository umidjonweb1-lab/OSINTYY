from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config import settings
from database.db import stats, all_user_ids

router = Router()

def is_admin(message: Message):
    return message.from_user.id in settings.admin_ids

@router.message(Command("admin"))
async def admin(message: Message):
    if not is_admin(message):
        return await message.answer("⛔ Ruxsat yo‘q.")
    s = stats()
    await message.answer(
        f"👑 <b>ADMIN PANEL</b>\n\n"
        f"👤 Users: {s['users']}\n"
        f"🔎 Searches: {s['searches']}\n"
        f"🔔 Tracking: {s['tracking']}\n\n"
        "Broadcast: <code>/broadcast matn</code>",
        parse_mode="HTML")

@router.message(Command("broadcast"))
async def broadcast(message: Message, bot):
    if not is_admin(message):
        return await message.answer("⛔ Ruxsat yo‘q.")
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2:
        return await message.answer("Misol: /broadcast Salom")
    sent = 0
    for uid in all_user_ids():
        try:
            await bot.send_message(uid, parts[1])
            sent += 1
        except Exception:
            pass
    await message.answer(f"📢 Yuborildi: {sent}")
