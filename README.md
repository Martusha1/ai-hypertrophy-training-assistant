# Hippity — AI Hypertrophy Training Assistant

Hippity is an AI-powered training assistant that generates personalized hypertrophy (muscle growth) programs and helps track workout progress over time. It combines an LLM (via Groq) with a structured database of programs, sessions, and exercises, delivered through a Telegram bot and a FastAPI backend.

**Status: actively in development.** The Telegram bot is the main, actively-developed interface. It supports multi-user registration (via natural-language profile extraction, not a rigid form), general conversation with per-chat memory, and is being wired up to actually save profiles and generate programs end-to-end. A separate FastAPI backend also exists but is currently a standalone secondary interface, not something the bot depends on at runtime — see "Two separate entry points" below.

## What it does (or is being built to do)

- Lets a new user describe themselves in a normal sentence — no rigid form — and has an LLM extract a structured training profile (name, age, experience, days/week, session length, equipment, goal) from that free text, asking natural follow-up questions for anything missing
- Generates a personalized training program based on that profile using an LLM (Groq), following real hypertrophy programming principles (volume landmarks, progressive overload, structured warmups) encoded in the system prompt
- Remembers the ongoing conversation per chat, so follow-up questions and coaching advice have context instead of treating every message as a blank slate
- Stores users, programs, sessions, and logged workouts in a SQLite database, with each Telegram account mapped to its own internal user record (built for multiple users from the start, not retrofitted)
- Separately exposes some of that same data over a small FastAPI backend (endpoints to fetch programs, check exercise progress, log sessions)

## Two separate entry points
 
Hippity is really two independent programs sharing one SQLite database — they are **not** connected to each other at runtime, and only one (`hippity.py`) is part of the live user-facing flow right now:
 
**`hippity.py`** — the Telegram bot. This is what a user actually talks to. Run with `python3 hippity.py` from inside `phase1/`. All of its logic — commands, conversation, registration — talks directly to `database.py`.
 
**`main.py`** — a FastAPI backend exposing a few endpoints (`/programs`, `/progress/{exercise_name}`, `/session/log/{program_id}/{user_id}/{day_number}`) over the same database. It was built during Phase 2 as a FastAPI learning exercise and demonstrates the same data being served over HTTP, but the bot never calls it — nothing currently connects the two. Run separately with `uvicorn phase1.main:app --reload` from the repo root, if you want to explore it via its interactive docs at `/docs`. (Known issue: `/programs` currently calls `database.get_programs()` without the `user_id` argument the function now requires, so that endpoint will error until fixed.)

## Project structure

```
phase0/   Early standalone scripts — first steps with core training math (1RM, volume, progression logic) and a first LLM API call
phase1/   The actual application
  ├─ database.py           SQLite data layer (users, programs, sessions, exercises) — multi-user aware via telegram_id
  ├─ program_generator.py  Builds prompts and calls the LLM to generate a training program
  ├─ main.py                FastAPI app exposing some backend data as HTTP endpoints (see above — not wired to the bot)
  ├─ hippity.py             Telegram bot — /start, /help, /info implemented; other commands planned
  └─ session_logger.py      CLI script for logging a workout session
```

## Tech stack

- **Python**
- **SQLite** — data storage
- **Groq API** (currently `openai/gpt-oss-20b`) — LLM integration for both conversation and structured profile/program extraction
- **python-telegram-bot** — Telegram bot interface
- **FastAPI** — a secondary, currently standalone API layer over the same database

## Database schema

- `users` — one row per person, keyed by internal `user_id`; `telegram_id` links each row to a Telegram account (`UNIQUE`, `NOT NULL`) so the bot can support multiple people without mixing up their data
- `program` — one row per generated mesocycle, linked to `users` via `user_id`
- `workout_sessions` — one row per logged training session, linked to both `program` and `users`
- `logged_sets` — one row per logged set within a session, linked to `workout_sessions`

# How the Telegram bot works
 
`hippity.py` routes every incoming plain-text message through `router_func`, which checks whether the current chat is mid-registration (a flag stored in `context.chat_data`) and sends it to either the registration handler or general chat accordingly.
 
**Registration (`/register`):** checks whether this Telegram user already exists in the database; if not, starts a natural-language intake — the user describes themselves in one or more messages, and each reply is sent to the LLM along with what's already been extracted so far, asking it to return updated structured JSON plus a list of any still-missing fields and a natural follow-up question. This loops until the profile is complete. *(Currently: extraction and the missing-field follow-up loop work; saving the completed profile to the database and generating the first program is the piece actively being finished.)*
 
**General chat:** any message outside registration goes to the LLM with the full conversation history for that chat (stored in-memory in `context.chat_data["history"]`, a growing list of `{"role", "content"}` messages) so replies have context. This resets if the bot process restarts — persisting it to the database is a known future improvement, not yet done.

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
4. Run the Telegram bot (the main interface):
   ```
   cd phase1
   python3 hippity.py
   ```
5. (Optional) Run the standalone FastAPI backend:
   ```
   uvicorn phase1.main:app --reload
   ```

## Roadmap

- [ ] Finish the registration flow: merge extracted fields across turns, and on completion save the user + generate/save their first program
- [ ] Add `/changeprofile` — same free-text extraction approach as registration, but seeded with the user's existing profile and requiring a preview/confirm step before overwriting
- [ ] Persist conversation history to the database so it survives a bot restart
- [ ] Wire up `/progress <exercise>`, `/program`, `/my_programs` to their corresponding database functions
- [ ] Fix the `/programs` FastAPI endpoint (missing `user_id` argument)
- [ ] Use logged session data to give feedback on progression and suggest deloads
- [ ] Add basic tests around database and program generation logic