from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Profile Search", callback_data="profile"),
         InlineKeyboardButton(text="🔎 Search", callback_data="search")],
        [InlineKeyboardButton(text="👨 Human Search", callback_data="human"),
         InlineKeyboardButton(text="📝 Text Search", callback_data="text")],
        [InlineKeyboardButton(text="📊 Statistics", callback_data="stats"),
         InlineKeyboardButton(text="🔔 Track", callback_data="track")],
        [InlineKeyboardButton(text="💠 Name History", callback_data="names"),
         InlineKeyboardButton(text="👥 Groups", callback_data="groups")],
        [InlineKeyboardButton(text="📣 Channels", callback_data="channels"),
         InlineKeyboardButton(text="💬 Messages", callback_data="messages")],
        [InlineKeyboardButton(text="🔍 Analysis", callback_data="analysis"),
         InlineKeyboardButton(text="👍 Reputation", callback_data="reputation")],
        [InlineKeyboardButton(text="🤝 Public Connections", callback_data="connections"),
         InlineKeyboardButton(text="🎁 Gifts", callback_data="gifts")],
        [InlineKeyboardButton(text="🏆 Top Chats", callback_data="topchat")],
        [InlineKeyboardButton(text="🥷 Privacy", callback_data="privacy"),
         InlineKeyboardButton(text="ℹ️ Help", callback_data="help")],
    ])

def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="menu")]
    ])
