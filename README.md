# Hippity — AI Hypertrophy Training Assistant

Hippity is an AI-powered training assistant that generates personalized hypertrophy (muscle growth) programs and helps track workout progress over time. It combines an LLM (via Groq) with a structured database of programs, sessions, and exercises, delivered through a Telegram bot and a FastAPI backend.

**Status: actively in development.** Multi-user registration is fully working end-to-end — a new user describes themselves in plain language, Hippity extracts a structured profile via the LLM, asks follow-up questions for anything missing, shows the extracted data for review, and saves it to the database on `/yes`. General conversation with per-chat memory also works. Actually generating and saving a user's first training program (`/new_program`) is the next piece being built.

## What it does (or is being built to do)

- Lets a new user describe themselves in a normal sentence — no rigid form — and has an LLM extract a structured training profile (name, age, experience, days/week, session length, equipment, goal) from that free text, asking natural follow-up questions for anything missing, then showing the full extracted profile for the user to confirm (`/yes`) or correct (`/no`) before it's saved
- Generates a personalized training program based on that profile using an LLM (Groq), following real hypertrophy programming principles (volume landmarks, progressive overload, structured warmups) encoded in the system prompt
- Remembers the ongoing conversation per chat, so follow-up questions and coaching advice have context instead of treating every message as a blank slate
- Stores users, programs, sessions, and logged workouts in a SQLite database, with each Telegram account mapped to its own internal user record (built for multiple users from the start, not retrofitted)
- Separately exposes some of that same data over a small FastAPI backend (endpoints to fetch programs, check exercise progress, log sessions)

## Two separate entry points
 
Hippity is really two independent programs sharing one SQLite database — they are **not** connected to each other at runtime, and only one (`hippity.py`) is part of the live user-facing flow right now:
 
**`hippity.py`** — the Telegram bot. This is what a user actually talks to. Run with `python3 hippity.py` from inside `phase1/`. All of its logic — commands, conversation, registration — talks directly to `database.py`.
 
**`main.py`** — a FastAPI backend exposing a few endpoints (`/programs`, `/progress/{exercise_name}`, `/session/log/{program_id}/{user_id}/{day_number}`) over the same database. It was built as a FastAPI learning exercise and demonstrates the same data being served over HTTP, but the bot never calls it — nothing currently connects the two. Run separately with `uvicorn phase1.main:app --reload` from the repo root, if you want to explore it via its interactive docs at `/docs`. (Known issue: `/programs` currently calls `database.get_programs()` without the `user_id` argument the function now requires, so that endpoint will error until fixed.)

## Project structure

```
phase0/   Early standalone scripts — first steps with core training math (1RM, volume, progression logic) and a first LLM API call
phase1/   The actual application
  ├─ database.py           SQLite data layer (users, programs, sessions, exercises) — multi-user aware via telegram_id
  ├─ program_generator.py  Builds prompts and calls the LLM to generate a training program
  ├─ main.py                FastAPI app exposing some backend data as HTTP endpoints (see above — not wired to the bot)
  ├─ hippity.py             The Telegram bot — commands, routing, conversation memory, and the registration flow
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
 
`hippity.py` routes every incoming plain-text message through `router_func`, which checks whether the current chat is mid-registration (a flag stored in `context.chat_data`) and sends it to either the registration handler or general chat accordingly. Slash commands bypass this routing entirely and go straight to their own handlers, so commands like `/cancel` always work regardless of what state a chat is in.
 
**Registration (`/register` → `/yes` or `/no`):** `/register` checks whether the Telegram user already exists in the database (via `telegram_id`) and, if not, starts a natural-language intake, storing progress in `context.chat_data["registration"]`. Each message the user sends afterward is routed to the extraction logic, which sends the LLM both what's already known and the newest reply, gets back structured JSON plus any still-missing fields, merges newly extracted (non-null) values into the stored profile, and either asks a natural follow-up question for what's missing or — once nothing is missing — shows the full profile and asks for confirmation. `/yes` re-checks that nothing is still `None` (guarding against someone confirming too early), then saves the profile to the database via `database.save_user()` and clears the registration state. `/no` prompts the user to describe what's wrong, leaving the partially-collected data in place so only the incorrect parts need re-stating. `/cancel` works at any point mid-registration and clears the state without saving anything.
 
**General chat:** any message outside registration goes to the LLM with the full conversation history for that chat (stored in-memory in `context.chat_data["history"]`, a growing list of `{"role", "content"}` messages) so replies have context. This resets if the bot process restarts — persisting it to the database is a known future improvement, not yet done. *(Known gap: this general chat currently has no system prompt establishing Hippity's identity or capabilities — if a user asks "what can you do?" mid-conversation, the model has no grounding beyond what it infers from the raw exchange. Planned fix: inject a system message describing Hippity's role and command list the first time a chat's history is created.)*

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

- [ ] Build `/new_program`: generate a program from a saved profile via `build_system_prompt()`/`generate_program()` and save it with `database.save_program()`generation + preview of all user programs
- [ ] Add `/changeprofile` — same free-text extraction approach as registration, but seeded with the user's existing profile and requiring a preview/confirm step before overwriting
- [ ] Persist conversation history to the database so it survives a bot restart
- [ ] Wire up `/progress <exercise>`, `/program`, `/my_programs` to their corresponding database functions
- [ ] Use logged session data to give feedback on progression and suggest deloads
- [ ] Add basic tests around database and program generation logic