from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from database.db import upsert_user
from keyboards.main import main_menu

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    upsert_user(message.from_user)
    text = (
        "👋 <b>OSINT Telegram Bot</b>\n\n"
        "Ochiq va qonuniy ma'lumotlar bilan ishlash uchun bot.\n\n"
        "Ma'lumot izlash uchun menyudan kerakli bo‘limni tanlang.\n\n"
        "⚠️ Private chatlar, parollar, login kodlari va yashirin ma'lumotlar olinmaydi."
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")
