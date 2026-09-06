# Hippity — AI Hypertrophy Training Assistant

Hippity is an AI-powered training assistant that generates personalized hypertrophy (muscle growth) programs and helps track workout progress over time. It combines an LLM (via Groq) with a structured database of programs, sessions, and exercises, delivered through a Telegram bot and a FastAPI backend.

**Status: actively in development.** The FastAPI backend, database layer, and LLM-based program generation are functional. The database now supports multiple users (each Telegram account maps to its own `user_id`). The Telegram bot responds to `/start`, `/help`, and `/info`; the remaining commands listed in `/help` (`/log`, `/progress`, `/program`, `/all_programs`, `/new_program`) are planned but not yet wired to the program generator or database.

## What it does (or is being built to do)

- Generates a personalized training program based on the user's experience level, goals, and circumstances, using an LLM (Groq / Llama 3.3)
- Stores users, programs, sessions, and logged workouts in a SQLite database, with each user identified by their Telegram ID
- Exposes a FastAPI backend with endpoints to fetch programs, check exercise progress, and log sessions
- Aims to analyze logged workout data to give feedback on progression, deloads, and technique via a Telegram chat interface

## Project structure

```
phase0/   Early standalone scripts — first steps with core training math (1RM, volume, progression logic) and a first LLM API call
phase1/   The actual application
  ├─ database.py           SQLite data layer (users, programs, sessions, exercises) — multi-user aware via telegram_id
  ├─ program_generator.py  Builds prompts and calls the LLM to generate a training program
  ├─ main.py                FastAPI app exposing the backend as an API
  ├─ hippity.py             Telegram bot — /start, /help, /info implemented; other commands planned
  └─ session_logger.py      CLI script for logging a workout session
```

## Tech stack

- **Python**
- **FastAPI** — backend/API layer
- **SQLite** — data storage
- **Groq API (Llama 3.3)** — LLM integration for program generation
- **python-telegram-bot** — Telegram bot interface

## Database schema

- `users` — one row per person, keyed by internal `user_id`; `telegram_id` links each row to a Telegram account (`UNIQUE`, `NOT NULL`) so the bot can support multiple people without mixing up their data
- `program` — one row per generated mesocycle, linked to `users` via `user_id`
- `workout_sessions` — one row per logged training session, linked to both `program` and `users`
- `logged_sets` — one row per logged set within a session, linked to `workout_sessions`

## Running it locally

1. Clone the repo and install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the project root with:
   ```
   GROQ_API_KEY=your_groq_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ```
3. Initialize the database (creates `hypertrophy.db` with all tables):
   ```
   python -m phase1.database
   ```
4. Run the API:
   ```
   uvicorn phase1.main:app --reload
   ```
5. Run the Telegram bot:
   ```
   python phase1/hippity.py
   ```

## Roadmap

- [ ] Add a lookup step (Telegram ID → internal `user_id`) so the bot can identify returning users and create new ones on first contact
- [ ] Connect the Telegram bot to `program_generator.py` so users can generate and receive programs directly in chat (`/new_program`)
- [ ] Wire up `/all_programs` and `/program` to the database's per-user program queries
- [ ] Wire up `/progress <exercise>` to `check_progress()`
- [ ] Let users log sessions through the bot instead of the CLI (`/log`)
- [ ] Use logged session data to give feedback on progression and suggest deloads
- [ ] Add basic tests around database and program generation logic