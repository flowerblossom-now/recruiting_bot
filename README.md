# Recruiting Bot — Mindl

> **Prototype / demo project.**

A Telegram bot that takes candidate applications by itself, paired with a web dashboard so HR isn't digging through chat history. The bot runs a guided interview for three roles (DevOps / Frontend / Backend) with role-specific questions, and every application lands straight in a dashboard table — real-time filters, skill search, Excel export. Inviting or rejecting a candidate is one click from the dashboard, no need to switch back to Telegram. Storage is plain SQLite, no external services required, plus a one-click backup for peace of mind.

## Highlights

- Guided Telegram interview per role, no manual data entry
- Live dashboard: filter, search by skill, export to Excel
- Invite / reject candidates straight from the dashboard
- Self-contained SQLite storage with one-click backup

## Run with Docker

```bash
cp .env.example .env      # set BOT_TOKEN and dashboard password
docker compose up -d      # starts the bot and dashboard, auto-restarts on crash
```

The dashboard runs on `http://localhost:5050`. Stop with `docker compose down` (data persists in the volume).

To show the dashboard to a client with sample data already in it:

```bash
python3 seed_demo.py   # adds 8 candidates in various statuses
```

## Run without Docker

You'll need Python 3.9+ and a bot token from [@BotFather](https://t.me/BotFather).

```bash
python3 -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # set BOT_TOKEN and HR_PANEL_PASSWORD
python3 bot.py         # terminal 1
python3 hr_panel.py    # terminal 2 — dashboard on http://localhost:5000, default password: admin
```

## How it plays out

A candidate finds the bot on Telegram, hits `/start`, picks a role, and answers the questions. HR opens the dashboard and sees the new candidate in the table — from there it's filtering, skill search, invites, or rejections, all in one place.

## Bot commands

| Command   | What it does                |
|-----------|------------------------------|
| `/start`  | Start filling out the form   |
| `/cancel` | Cancel the current form      |
| `/help`   | Show help                    |
