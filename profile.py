from html import escape
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database.db import upsert_user, add_name_observation, get_local_user, get_name_history, user_search_count
from keyboards.main import back_menu
from services.funstat import funstat, FunstatUnavailable, unwrap, pick

router = Router()


def profile_keyboard(telegram_id: int, target: str | None = None):
    key = target or str(telegram_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💠 Name History", callback_data=f"fsnames:{key}")],
        [InlineKeyboardButton(text="🔤 Username History", callback_data=f"fsusernames:{key}")],
        [InlineKeyboardButton(text="👥 Groups", callback_data=f"fsgroups:{key}")],
        [InlineKeyboardButton(text="🔎 Search again", callback_data="search")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="menu")],
    ])


def name_of(user):
    return " ".join(x for x in [user.first_name, user.last_name] if x) or "—"


def render_local_profile(row, source="Local index"):
    name = " ".join(x for x in [row["first_name"], row["last_name"]] if x) or "—"
    username = f'@{row["username"]}' if row["username"] else "—"
    return (
        "👤 <b>PROFILE</b>\n\n"
        f"Name: <b>{escape(name)}</b>\n"
        f"Username: {escape(username)}\n"
        f"Telegram ID: <code>{row['telegram_id']}</code>\n"
        f"Type: {'Bot' if row['is_bot'] else 'User'}\n"
        f"Last activity in bot: {row['last_activity']}\n"
        f"Search records: {user_search_count(row['telegram_id'])}\n"
        f"Source: {escape(source)}"
    )


def format_list_result(title: str, result, limit=10):
    data = unwrap(result)
    if isinstance(data, dict):
        data = pick(data, "data", "items", "results", "history", "chats", default=data)
    if isinstance(data, dict):
        data = list(data.values())
    if not isinstance(data, list):
        data = [data]
    lines = [title, ""]
    if not data:
        lines.append("Ma'lumot topilmadi.")
    for i, item in enumerate(data[:limit], 1):
        if isinstance(item, dict):
            name = pick(item, "name", "display_name", "title", "username", "value", default="—")
            username = pick(item, "username", "user_name", default=None)
            date = pick(item, "date", "created_at", "updated_at", "observed_at", default=None)
            line = f"{i}. <b>{escape(str(name))}</b>"
            if username and str(username) != str(name):
                line += f" — @{escape(str(username).lstrip('@'))}"
            if date:
                line += f"\n   <i>{escape(str(date))}</i>"
            lines.append(line)
        else:
            lines.append(f"{i}. <b>{escape(str(item))}</b>")
    return "\n".join(lines)


@router.message(Command("me"))
async def me(message: Message):
    upsert_user(message.from_user)
    u = message.from_user
    display = name_of(u)
    add_name_observation(u.id, display, u.username)
    row = get_local_user(u.id)
    await message.answer(render_local_profile(row, "Bot interaction"), parse_mode="HTML", reply_markup=profile_keyboard(u.id))


@router.message(Command("profile"))
async def profile(message: Message):
    upsert_user(message.from_user)
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2:
        return await message.answer(
            "👤 <b>Profile Search</b>\n\n"
            "<code>/profile @username</code>\n"
            "<code>/profile 123456789</code>\n\n"
            "Public Telegram ma'lumotlari Funstat orqali olinadi.", parse_mode="HTML")

    target = parts[1].strip()
    try:
        result = await funstat.stats(target)
        await message.answer(stats_to_text_safe(result, target), parse_mode="HTML", reply_markup=profile_keyboard(0, target))
        return
    except FunstatUnavailable:
        pass
    except Exception:
        pass

    # Fallback: Telegram Bot API / local index
    if target.isdigit() or (target.startswith("-") and target[1:].isdigit()):
        row = get_local_user(int(target))
        if row:
            return await message.answer(render_local_profile(row), parse_mode="HTML", reply_markup=profile_keyboard(row["telegram_id"]))
    username = target if target.startswith("@") else "@" + target
    try:
        chat = await message.bot.get_chat(username)
        title = chat.title or " ".join(x for x in [chat.first_name, chat.last_name] if x) or "—"
        uname = f"@{chat.username}" if chat.username else "—"
        text = ("👤 <b>PUBLIC TELEGRAM ENTITY</b>\n\n"
                f"Name: <b>{escape(title)}</b>\n"
                f"Username: {escape(uname)}\n"
                f"ID: <code>{chat.id}</code>\n"
                f"Type: {escape(chat.type)}")
        return await message.answer(text, parse_mode="HTML", reply_markup=back_menu())
    except Exception:
        return await message.answer("❌ Profil topilmadi. Username/ID ni tekshiring.", parse_mode="HTML", reply_markup=back_menu())


def stats_to_text_safe(result, target):
    data = unwrap(result)
    data = pick(data, "data", default=data)
    name = pick(data, "name", "display_name", "full_name", default="—")
    username = pick(data, "username", "user_name", default="—")
    uid = pick(data, "id", "telegram_id", "user_id", default="—")
    total = pick(data, "total_msg_count", "messages_count", "message_count", default="—")
    groups = pick(data, "groups_count", "group_count", "chats_count", default="—")
    uname = str(username)
    if uname != "—" and not uname.startswith("@"):
        uname = "@" + uname
    return ("👤 <b>PROFILE</b>\n\n"
            f"Name: <b>{escape(str(name))}</b>\n"
            f"Username: <b>{escape(uname)}</b>\n"
            f"Telegram ID: <code>{escape(str(uid))}</code>\n"
            f"💬 Public messages: <b>{escape(str(total))}</b>\n"
            f"👥 Public groups/chats: <b>{escape(str(groups))}</b>\n"
            f"🔎 Query: <code>{escape(target)}</code>\n\n"
            "Source: Funstat public-data API")


async def _history(call: CallbackQuery, method: str, target: str, title: str):
    try:
        result = await getattr(funstat, method)(target)
        text = format_list_result(title, result)
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=profile_keyboard(0, target))
    except FunstatUnavailable:
        await call.answer("FUNSTAT_TOKEN Render Variables'da sozlanmagan.", show_alert=True)
        return
    except Exception:
        await call.answer("Ma'lumotni olishda xatolik. API token/balance ni tekshiring.", show_alert=True)
        return
    await call.answer()


@router.callback_query(F.data.startswith("fsnames:"))
async def names_fs(call: CallbackQuery):
    target = call.data.split(":", 1)[1]
    await _history(call, "names", target, "💠 <b>NAME HISTORY</b>")


@router.callback_query(F.data.startswith("fsusernames:"))
async def usernames_fs(call: CallbackQuery):
    target = call.data.split(":", 1)[1]
    await _history(call, "usernames", target, "🔤 <b>USERNAME HISTORY</b>")


@router.callback_query(F.data.startswith("fsgroups:"))
async def groups_fs(call: CallbackQuery):
    target = call.data.split(":", 1)[1]
    await _history(call, "chats", target, "👥 <b>PUBLIC GROUPS / CHATS</b>",)


@router.callback_query(F.data.startswith("names:"))
async def old_names(call: CallbackQuery):
    try:
        telegram_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        return await call.answer("ID xato", show_alert=True)
    rows = get_name_history(telegram_id, 10)
    if not rows:
        text = "💠 <b>Name History</b>\n\nTarix hali yig‘ilmagan."
    else:
        lines = ["💠 <b>Name History</b>", ""]
        for i, row in enumerate(rows, 1):
            uname = f" — @{row['username']}" if row['username'] else ""
            lines.append(f"{i}. {escape(row['display_name'])}{escape(uname)}\n   <i>{row['observed_at']}</i>")
        text = "\n".join(lines)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=profile_keyboard(telegram_id))
    await call.answer()


@router.callback_query(F.data == "profile")
async def profile_button(call: CallbackQuery):
    await call.message.edit_text(
        "👤 <b>Profile Search</b>\n\n"
        "<code>/profile @username</code>\n"
        "<code>/profile 123456789</code>\n\n"
        "Public profil statistikasi Funstat API orqali olinadi.",
        reply_markup=back_menu(), parse_mode="HTML")
    await call.answer()
