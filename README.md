# HoodShop

Telegram clothing store starter project.

## Stack
- Python
- aiogram 3
- FastAPI
- SQLite (starter database)
- Telegram Web App

## 1. Create environment

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Configure Telegram token

Copy `.env.example` to `.env` and put your BotFather token into `BOT_TOKEN`.

For the first local test, `WEBAPP_URL` can stay unchanged. The `/start` command will still work; the Web App button becomes usable after we publish the web folder over HTTPS.

## 3. Start the web app

```bash
uvicorn web.app:app --reload --port 8000
```

Open http://127.0.0.1:8000

## 4. Start the Telegram bot

In another Terminal tab:

```bash
source .venv/bin/activate
python -m bot.main
```

Then open your bot in Telegram and send `/start`.

## Project structure

```text
HoodShop/
├── bot/
│   ├── __init__.py
│   └── main.py
├── web/
│   ├── __init__.py
│   ├── app.py
│   └── static/
│       └── index.html
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
