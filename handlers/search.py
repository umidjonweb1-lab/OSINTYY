from html import escape
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import upsert_user, add_search, add_tracking, search_local_users, get_local_user
from keyboards.main import back_menu
from services.funstat import funstat, FunstatUnavailable, unwrap, pick

router = Router()

def arg(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else ""

def result_keyboard(target):
    safe = str(target)[:100]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Profile", callback_data=f"fsprofile:{safe}")],
        [InlineKeyboardButton(text="💠 Names", callback_data=f"fsnames:{safe}")],
        [InlineKeyboardButton(text="👥 Groups", callback_data=f"fsgroups:{safe}")],
        [InlineKeyboardButton(text="🔎 New search", callback_data="search")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="menu")],
    ])

def format_search_result(result, q):
    data = unwrap(result)
    data = pick(data, "data", "results", "items", default=data)
    if isinstance(data, dict):
        items = list(data.values())
    elif isinstance(data, list):
        items = data
    else:
        items = [data]
    lines = [f"🔎 <b>SEARCH RESULT</b>", "", f"Query: <code>{escape(q)}</code>", ""]
    if not items:
        lines.append("Natija topilmadi.")
    for i, item in enumerate(items[:10], 1):
        if isinstance(item, dict):
            name = pick(item, "name", "display_name", "title", "username", default="—")
            username = pick(item, "username", "user_name", default=None)
            uid = pick(item, "id", "telegram_id", "user_id", default=None)
            line = f"<b>{i}.</b> {escape(str(name))}"
            if username and str(username) != str(name):
                line += f" — @{escape(str(username).lstrip('@'))}"
            if uid:
                line += f"\n   🆔 <code>{escape(str(uid))}</code>"
            lines.append(line)
        else:
            lines.append(f"<b>{i}.</b> {escape(str(item))}")
    return "\n".join(lines)

async def run_user_search(message: Message, q: str):
    if len(q) > 128:
        return await message.answer("❌ Qidiruv so‘rovi 128 belgidan oshmasin.")
    add_search(message.from_user.id, q, "user")

    # Primary source: Funstat public-data API.
    try:
        result = await funstat.resolve(q) if not q.isdigit() else await funstat.stats(q)
        return await message.answer(format_search_result(result, q), parse_mode="HTML", reply_markup=result_keyboard(q))
    except FunstatUnavailable:
        pass
    except Exception:
        pass

    # Fallback to Telegram Bot API for public usernames.
    if q.startswith("@") or (q and q.replace("_", "").isalnum() and not q.isdigit() and " " not in q):
        username = q if q.startswith("@") else "@" + q
        try:
            chat = await message.bot.get_chat(username)
            name = chat.title or " ".join(x for x in [chat.first_name, chat.last_name] if x) or "—"
            uname = f"@{chat.username}" if chat.username else "—"
            text = ("🔎 <b>SEARCH RESULT</b>\n\n"
                    f"👤 Name: <b>{escape(name)}</b>\n"
                    f"🔗 Username: <b>{escape(uname)}</b>\n"
                    f"🆔 ID: <code>{chat.id}</code>\n"
                    f"📌 Type: <b>{escape(chat.type)}</b>")
            return await message.answer(text, parse_mode="HTML", reply_markup=result_keyboard(chat.id))
        except Exception:
            pass

    rows = search_local_users(q, 10)
    if not rows and q.isdigit():
        row = get_local_user(int(q))
        if row:
            rows = [row]
    if not rows:
        return await message.answer("🔎 <b>Natija topilmadi</b>\n\nBoshqa username, ID yoki ism bilan urinib ko‘ring.", parse_mode="HTML", reply_markup=back_menu())
    text = [f"🔎 <b>SEARCH: {escape(q)}</b>", "", f"Topildi: <b>{len(rows)}</b>", ""]
    for i, row in enumerate(rows, 1):
        name = " ".join(x for x in [row["first_name"], row["last_name"]] if x) or "—"
        username = f'@{row["username"]}' if row["username"] else "—"
        text.append(f"<b>{i}.</b> 👤 <b>{escape(name)}</b> — {escape(username)}\n<code>{row['telegram_id']}</code>")
    await message.answer("\n".join(text), parse_mode="HTML", reply_markup=back_menu())

@router.message(Command("search"))
async def search(message: Message):
    upsert_user(message.from_user)
    q = arg(message)
    if not q:
        return await message.answer("🔎 <b>Advanced Search</b>\n\n<code>/search @username</code>\n<code>/search 123456789</code>\n<code>/search Ali Valiyev</code>", parse_mode="HTML")
    await run_user_search(message, q)

@router.message(Command("human"))
async def human(message: Message):
    upsert_user(message.from_user)
    q = arg(message)
    if not q:
        return await message.answer("👨 Misol: <code>/human Ali Valiyev</code>", parse_mode="HTML")
    await run_user_search(message, q)

@router.message(Command("text"))
async def text_search(message: Message):
    upsert_user(message.from_user)
    q = arg(message)
    if not q:
        return await message.answer("📝 Misol: <code>/text football</code>", parse_mode="HTML")
    add_search(message.from_user.id, q, "text")
    try:
        result = await funstat.search_text(q)
        return await message.answer(format_search_result(result, q), parse_mode="HTML", reply_markup=back_menu())
    except FunstatUnavailable:
        return await message.answer("❌ FUNSTAT_TOKEN sozlanmagan.", parse_mode="HTML", reply_markup=back_menu())
    except Exception:
        return await message.answer("❌ Public text search uchun API natija qaytarmadi.", parse_mode="HTML", reply_markup=back_menu())

@router.message(Command("track"))
async def track(message: Message):
    upsert_user(message.from_user)
    q = arg(message)
    if not q:
        return await message.answer("🔔 Misol: <code>/track @username</code>", parse_mode="HTML")
    if len(q) > 128:
        return await message.answer("❌ Target juda uzun.")
    add_tracking(message.from_user.id, q)
    await message.answer(f"🔔 <b>Tracking added</b>\n\nTarget: <code>{escape(q)}</code>", parse_mode="HTML")

@router.callback_query(F.data == "search")
async def search_button(call: CallbackQuery):
    await call.message.edit_text("🔎 <b>Advanced Search</b>\n\n<code>/search @username</code> — public profil/chat\n<code>/search 123456789</code> — public data\n<code>/search Ali Valiyev</code> — name search", parse_mode="HTML", reply_markup=back_menu())
    await call.answer()

@router.callback_query(F.data.startswith("fsprofile:"))
async def fs_profile(call: CallbackQuery):
    from handlers.profile import stats_to_text_safe
    target = call.data.split(":", 1)[1]
    try:
        result = await funstat.stats(target)
        await call.message.edit_text(stats_to_text_safe(result, target), parse_mode="HTML", reply_markup=result_keyboard(target))
        await call.answer()
    except Exception:
        await call.answer("Profil ma'lumotini olishda xatolik.", show_alert=True)

@router.callback_query(F.data.startswith("quickprofile:"))
async def quick_profile(call: CallbackQuery):
    target = call.data.split(":", 1)[1]
    from handlers.profile import stats_to_text_safe
    try:
        result = await funstat.stats(target)
        await call.message.edit_text(stats_to_text_safe(result, target), parse_mode="HTML", reply_markup=result_keyboard(target))
        return await call.answer()
    except Exception:
        pass
    row = get_local_user(int(target)) if target.isdigit() else None
    if not row:
        return await call.answer("Profil topilmadi", show_alert=True)
    from handlers.profile import render_local_profile
    await call.message.edit_text(render_local_profile(row), parse_mode="HTML", reply_markup=back_menu())
    await call.answer()

@router.callback_query(F.data == "topchat")
async def topchat(call: CallbackQuery):
    await call.message.edit_text("🏆 <b>Top Public Chats</b>\n\nPublic chat ma'lumotlari API orqali olinadi.", parse_mode="HTML", reply_markup=back_menu())
    await call.answer()
