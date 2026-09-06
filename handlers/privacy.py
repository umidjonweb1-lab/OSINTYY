from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.main import back_menu

router = Router()

TEXT = (
    "🥷 <b>Privacy / Hide Data</b>\n\n"
    "Bu bot maxfiy ma'lumotlarni olish yoki Telegram privacy cheklovlarini "
    "aylanib o‘tish uchun ishlatilmaydi.\n\n"
    "❌ Parol va login kodi\n❌ Private chatlar\n❌ Yashirin kontaktlar\n"
    "❌ Privacy bypass\n\n"
    "Faqat public/ruxsat etilgan ma'lumotlar bilan ishlanadi."
)

@router.message(Command("hide"))
async def hide(message: Message):
    await message.answer(TEXT, parse_mode="HTML")

@router.callback_query(lambda c: c.data == "privacy")
async def privacy(call: CallbackQuery):
    await call.message.edit_text(TEXT, reply_markup=back_menu(), parse_mode="HTML")
    await call.answer()
