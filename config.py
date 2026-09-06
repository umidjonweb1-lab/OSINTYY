import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: tuple[int, ...]
    db_path: str
    funstat_token: str

def parse_admins(value: str) -> tuple[int, ...]:
    result = []
    for item in value.split(","):
        item = item.strip()
        if item.isdigit():
            result.append(int(item))
    return tuple(result)

token = os.getenv("BOT_TOKEN", "").strip()
if not token:
    raise RuntimeError("BOT_TOKEN is missing. Put it in .env")

settings = Settings(
    bot_token=token,
    admin_ids=parse_admins(os.getenv("ADMIN_IDS", "")),
    db_path=os.getenv("DB_PATH", "data/bot.db"),
    funstat_token=os.getenv("FUNSTAT_TOKEN", "").strip(),
)
