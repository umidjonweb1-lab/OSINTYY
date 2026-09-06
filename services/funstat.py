from __future__ import annotations

import asyncio
import os
from typing import Any

try:
    from funstat_api import AsyncFunstatClient
except Exception:  # package is optional until installed
    AsyncFunstatClient = None


class FunstatUnavailable(Exception):
    pass


class FunstatService:
    """Small async adapter around the public-data Funstat/Telelog API."""

    def __init__(self) -> None:
        self.token = os.getenv("FUNSTAT_TOKEN", "").strip()
        self.base_url = os.getenv("FUNSTAT_BASE_URL", "").strip()

    @property
    def enabled(self) -> bool:
        return bool(self.token and AsyncFunstatClient)

    def _client(self):
        if not self.enabled:
            raise FunstatUnavailable("FUNSTAT_TOKEN is not configured")
        kwargs = {}
        if self.base_url:
            # The client exposes a config object in current releases; keep the
            # default API endpoint unless a custom endpoint is explicitly set.
            try:
                from funstat_api import FunstatConfig
                kwargs["config"] = FunstatConfig(base_url=self.base_url)
            except Exception:
                pass
        return AsyncFunstatClient(self.token, **kwargs)

    async def _call(self, method: str, target: str, *args, **kwargs):
        async with self._client() as fs:
            fn = getattr(fs, method)
            return await fn(target, *args, **kwargs)

    async def stats(self, target: str):
        return await self._call("stats", target)

    async def resolve(self, target: str):
        return await self._call("resolve_username", target)

    async def names(self, target: str):
        return await self._call("get_names", target)

    async def usernames(self, target: str):
        return await self._call("get_usernames", target)

    async def chats(self, target: str):
        return await self._call("get_chats", target)

    async def messages(self, target: str, **kwargs):
        return await self._call("get_messages", target, **kwargs)

    async def reputation(self, target: str):
        return await self._call("rep", target)

    async def search_text(self, query: str):
        if not self.enabled:
            raise FunstatUnavailable("FUNSTAT_TOKEN is not configured")
        async with self._client() as fs:
            return await fs.search_text(query)

    async def balance(self):
        if not self.enabled:
            raise FunstatUnavailable("FUNSTAT_TOKEN is not configured")
        async with self._client() as fs:
            return await fs.get_balance()


funstat = FunstatService()


def unwrap(value: Any) -> Any:
    """Convert pydantic models / nested objects into plain Python data."""
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            pass
    if hasattr(value, "dict"):
        try:
            return value.dict()
        except Exception:
            pass
    if isinstance(value, dict):
        return {k: unwrap(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [unwrap(v) for v in value]
    if hasattr(value, "__dict__"):
        return {k: unwrap(v) for k, v in vars(value).items() if not k.startswith("_")}
    return value


def pick(data: Any, *names: str, default=None):
    data = unwrap(data)
    if isinstance(data, dict):
        for name in names:
            if name in data and data[name] is not None:
                return data[name]
        # case-insensitive fallback
        lower = {str(k).lower(): v for k, v in data.items()}
        for name in names:
            if name.lower() in lower and lower[name.lower()] is not None:
                return lower[name.lower()]
    return default


def stats_to_text(result: Any, target: str) -> str:
    data = pick(result, "data", default=result)
    name = pick(data, "name", "display_name", "full_name", default="—")
    username = pick(data, "username", "user_name", default="—")
    uid = pick(data, "id", "telegram_id", "user_id", default="—")
    total = pick(data, "total_msg_count", "messages_count", "message_count", default="—")
    groups = pick(data, "groups_count", "group_count", "chats_count", default="—")
    return (
        "👤 <b>PROFILE</b>\n\n"
        f"Name: <b>{name}</b>\n"
        f"Username: <b>{username if str(username).startswith('@') or username == '—' else '@'+str(username)}</b>\n"
        f"Telegram ID: <code>{uid}</code>\n"
        f"💬 Public messages: <b>{total}</b>\n"
        f"👥 Public groups/chats: <b>{groups}</b>\n"
        f"🔎 Query: <code>{target}</code>\n\n"
        "Source: Funstat public-data API"
    )
