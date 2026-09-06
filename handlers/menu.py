from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.main import main_menu, back_menu
from database.db import stats

router = Router()

HELP = (
    "ℹ️ <b>Yordam</b>\n\n"
    "• /search so‘z — public manbalardagi qidiruv uchun\n"
    "• /human Ism Familiya — public ma'lumotlar bo‘yicha qidiruv\n"
    "• /text matn — public indeksdagi matn qidiruvi\n"
    "• /topchat — public chatlar reytingi\n"
    "• /hide — maxfiylik bo‘limi\n\n"
    "Global Telegram bazasiga avtomatik kirish oddiy Bot API imkoniyati emas."
)

@router.callback_query(F.data == "menu")
async def menu(call: CallbackQuery):
    await call.message.edit_text("💠 <b>Menu</b>", reply_markup=main_menu(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "help")
async def help_cb(call: CallbackQuery):
    await call.message.edit_text(HELP, reply_markup=back_menu(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "stats")
async def stats_cb(call: CallbackQuery):
    s = stats()
    await call.message.edit_text(
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👤 Users: {s['users']}\n"
        f"🔎 Searches: {s['searches']}\n"
        f"🔔 Active tracking: {s['tracking']}",
        reply_markup=back_menu(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "track")
async def track_cb(call: CallbackQuery):
    await call.message.edit_text(
        "🔔 <b>Track</b>\n\n"
        "Kuzatish uchun /track @username formatidan foydalaning.\n"
        "Kuzatuv faqat public/ruxsat etilgan ma'lumot manbasi bilan ishlaydi.",
        reply_markup=back_menu(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.in_({
    "profile","search","human","text","names","groups","channels",
    "messages","analysis","reputation","connections","gifts","topchat"
}))
async def placeholder(call: CallbackQuery):
    names = {
        "profile":"👤 Profile Search", "search":"🔎 Search",
        "human":"👨 Human Search", "text":"📝 Text Search",
        "names":"💠 Name History", "groups":"👥 Groups",
        "channels":"📣 Channels", "messages":"💬 Messages",
        "analysis":"🔍 Analysis", "reputation":"👍 Reputation",
        "connections":"🤝 Public Connections", "gifts":"🎁 Gifts",
        "topchat":"🏆 Top Chats",
    }
    await call.message.edit_text(
        f"{names[call.data]}\n\n"
        "Bu modul arxitekturaga ulangan. Real natijalar faqat "
        "qonuniy/public data source ulangandan keyin ko‘rsatiladi.",
        reply_markup=back_menu())
    await call.answer()
