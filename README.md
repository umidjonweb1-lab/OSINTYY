# Telegram Public Analytics Bot — V4

This version connects Profile/Search to the Funstat/Telelog public-data API.

## Render Variables

- `BOT_TOKEN` — Telegram BotFather token
- `ADMIN_IDS` — comma-separated Telegram IDs
- `DB_PATH` — optional, defaults to `data/bot.db`
- `FUNSTAT_TOKEN` — your Funstat API token
- `FUNSTAT_BASE_URL` — optional custom API base URL; normally leave empty

## Main commands

- `/search @username` — public search
- `/search 123456789` — public ID lookup when supported by the API
- `/profile @username` — public profile statistics
- `/profile 123456789` — public profile statistics
- `/text query` — public message-text search when enabled by the API
- `/me` — local bot profile

The integration is limited to public/lawfully accessible data. It does not collect passwords, login codes, private chat contents, hidden contacts, or bypass Telegram privacy settings.
