# Hippity — AI Hypertrophy Training Assistant

Hippity is an AI-powered training assistant that generates personalized hypertrophy (muscle growth) programs and helps track workout progress over time. It combines an LLM (via Groq) with a structured database of programs, sessions, and exercises, delivered through a Telegram bot and a FastAPI backend.

**Status: actively in development.** Multi-user registration is fully working end-to-end — a new user describes themselves in plain language, Hippity extracts a structured profile via the LLM, asks follow-up questions for anything missing, shows the extracted data for review, and saves it to the database on `/yes`. General conversation has per-chat memory and is grounded by a system prompt describing Hippity's identity and commands, so it can accurately describe itself instead of guessing. `/new_program` generates a full training program from a saved profile, shows it to the user, and lets them either approve it (`/yes`) or just describe what they didn't like in plain text — an LLM call classifies whether that reply is an actual correction request, an implicit approval, or unrelated chatter, and responds accordingly. `/my_programs` lists a user's saved programs by id, and `/show_program <id>` pulls one back up on demand — both check that the requested program actually belongs to the requesting user before showing anything. `/log` walks a user through logging a completed workout session (program, day, then weight/reps/RIR per set) as a guided, strictly-parsed step-by-step flow rather than free-text LLM extraction, and resumes correctly if the conversation is interrupted mid-log. `/progress <exercise>` and `/changeprofile` are still open.

## What it does (or is being built to do)

- Lets a new user describe themselves in a normal sentence — no rigid form — and has an LLM extract a structured training profile (name, age, experience, days/week, session length, equipment, goal) from that free text, asking natural follow-up questions for anything missing, then showing the full extracted profile for the user to confirm (`/yes`) or correct (`/no`) before it's saved
- Generates a personalized training program based on that profile using an LLM (Groq), following real hypertrophy programming principles (volume landmarks, progressive overload, structured warmups) encoded in the system prompt, and lets the user iterate on it conversationally until they approve it
- Grounds every LLM conversation (general chat and program generation) in one shared system prompt describing Hippity's identity, tone, and available commands, so the model doesn't improvise an identity or claim capabilities it doesn't have
- Remembers the ongoing conversation per chat, so follow-up questions and coaching advice have context instead of treating every message as a blank slate
- Lets a user list all their saved programs (`/my_programs`) and pull any one of them back up by id (`/show_program <id>`) — useful if they forgot to write a program down, with an ownership check so one user can never view another's saved program
- Walks a user through logging a finished workout (`/log`) one question at a time — which program, which day, then weight, reps, and RIR for every set of every exercise in that day — with no LLM involved in this flow at all, since each step only ever expects one well-defined value
- Stores users, programs, sessions, and logged workouts in a SQLite database, with each Telegram account mapped to its own internal user record (built for multiple users from the start, not retrofitted)
- Includes a rules-based progressive-overload check (`database.check_progress`) that compares a session's logged sets against the previous one using rep, weight, and RIR thresholds — not yet wired to a command
- Separately exposes some of that same data over a small FastAPI backend (endpoints to fetch programs, check exercise progress, log sessions)

## Two separate entry points

Hippity is really two independent programs sharing one SQLite database — they are **not** connected to each other at runtime, and only one (`hippity.py`) is part of the live user-facing flow right now:

**`hippity.py`** — the Telegram bot. This is what a user actually talks to. Run with `python3 hippity.py` from inside `phase1/`. All of its logic — commands, conversation, registration, program generation, workout logging — talks directly to `database.py` and `program_generator.py`.

**`main.py`** — a FastAPI backend exposing a few endpoints (`/programs`, `/progress/{exercise_name}`, `/session/log/{program_id}/{user_id}/{day_number}`) over the same database. It was built as a FastAPI learning exercise and demonstrates the same data being served over HTTP, but the bot never calls it — nothing currently connects the two. Run separately with `uvicorn phase1.main:app --reload` from the repo root, if you want to explore it via its interactive docs at `/docs`. (Known issue: `/programs` currently calls `database.get_all_programs_by_user()` without the `user_id` argument the function now requires, so that endpoint will error until fixed.)

## Project structure

```
phase0/   Early standalone scripts — first steps with core training math (1RM, volume, progression logic) and a first LLM API call
phase1/   The actual application
  ├─ database.py           SQLite data layer (users, programs, sessions, exercises) — multi-user aware via telegram_id
  ├─ program_generator.py  Hippity's identity/system prompt (`define_llm`), program-prompt building (`build_system_prompt`), and the single consolidated Groq call (`call_llm`) used by every LLM-driven feature — general chat, registration extraction, program generation, correction, and the correction-intent classifier
  ├─ main.py                FastAPI app exposing some backend data as HTTP endpoints (see above — not wired to the bot)
  ├─ hippity.py             The Telegram bot — commands, routing, conversation memory, registration, program generation/correction, program lookup, and workout logging
  └─ session_logger.py      CLI script for logging a workout session
```

## Tech stack

- **Python**
- **SQLite** — data storage
- **Groq API** (currently `openai/gpt-oss-20b`) — LLM integration for conversation, structured profile/program extraction, program generation and correction, and correction-intent classification
- **python-telegram-bot** — Telegram bot interface
- **FastAPI** — a secondary, currently standalone API layer over the same database

## Database schema

- `users` — one row per person, keyed by internal `user_id`; `telegram_id` links each row to a Telegram account (`UNIQUE`, `NOT NULL`) so the bot can support multiple people without mixing up their data
- `program` — one row per generated mesocycle, linked to `users` via `user_id`
- `workout_sessions` — one row per logged training session, linked to both `program` and `users` via `program_id`/`user_id`, storing which `day_number` of the program was followed
- `logged_sets` — one row per logged set within a session, linked to `workout_sessions` via `workout_id`, storing exercise name, set number, reps done, weight (kg and lbs), and RIR

## How the Telegram bot works

`hippity.py` routes every incoming plain-text message through `router_func`, which checks whether the current chat is mid-registration, has a program awaiting review, or is mid-log (flags stored in `context.chat_data`) and sends it to the matching handler, falling back to general chat otherwise. Slash commands bypass this routing entirely and go straight to their own handlers, so commands like `/cancel` always work regardless of what state a chat is in.

**Registration (`/register` → `/yes` or `/no`):** `/register` checks whether the Telegram user already exists in the database (via `telegram_id`) and, if not, starts a natural-language intake, storing progress in `context.chat_data["registration"]`. Each message the user sends afterward is routed to the extraction logic, which sends the LLM both what's already known and the newest reply, gets back structured JSON plus any still-missing fields, merges newly extracted (non-null) values into the stored profile, and either asks a natural follow-up question for what's missing or — once nothing is missing — shows the full profile and asks for confirmation. `/yes` re-checks that nothing is still `None` (guarding against someone confirming too early), then saves the profile to the database via `database.save_user()` and clears the registration state. `/no` prompts the user to describe what's wrong, leaving the partially-collected data in place so only the incorrect parts need re-stating. `/cancel` works at any point mid-registration and clears the state without saving anything.

**Program generation (`/new_program` → review → `/yes`/`/no` or free-text correction):** `/new_program` checks the user is registered, pulls their saved profile from the database, and sends it to the LLM alongside the program-generation system prompt to produce a full JSON training program, which gets parsed and shown back to the user for review. If generation fails (for example, the response gets cut off by the token limit and doesn't parse as valid JSON), the pending program state is cleared immediately rather than left sitting around — so a stray follow-up message after a failed attempt falls through to ordinary chat instead of crashing. Once a program is successfully shown, the user can approve it with `/yes` (saved via `database.save_program()`) or respond in plain text. Any free text sent while a program is pending gets routed to a correction flow: a first, lightweight LLM call classifies whether the message is a correction request, an implicit "it's fine, save it" (handled the same as typing `/yes`), or unrelated chatter (in which case the bot just reminds the user to use `/yes`/`/no` and the pending program is left untouched). Only on an actual correction request does Hippity make a second LLM call — with the previous program and the user's specific feedback — to produce a revised version, which goes through the same review loop again.

**Looking up saved programs (`/my_programs`, `/show_program <id>`):** `/my_programs` lists every program a user has saved, formatted as `Program <id>: <name>` per line. `/show_program <id>` takes that id as a command argument, checks it against the requesting user's own list of saved program ids (`database.get_program_ids_by_user`) before doing anything else, and only then fetches and displays the full program — so a user can never view another user's saved program by guessing or incrementing ids. Invalid, missing, or non-numeric ids each get a specific, distinct reply rather than a crash.

**Logging a workout (`/log`):** `/log` starts a guided, strictly-structured flow — deliberately not an LLM-extraction flow like registration, since every question in it has exactly one expected kind of answer (an id, a day number, a weight, a rep count, an RIR value), so there's no real ambiguity to resolve. It stores progress in `context.chat_data["log"]`, shows the user's saved programs and asks them to pick one by id, pulls that program back up and asks which day they followed, then creates a `workout_sessions` row via `database.log_session()` and walks through every exercise and every set of that day one at a time — asking for weight, then reps, then RIR for each set in turn, saving each completed set to `logged_sets` via `database.save_set()` as soon as all three values for it are in. Rather than tracking an explicit "current step" pointer, each incoming message re-walks the exercise/set structure and skips anything already marked done in `context.chat_data["log"]`, so the flow resumes correctly if the conversation is interrupted partway through — a deliberately low-tech but working approach to picking up where it left off. The in-progress weight/reps/RIR values live in `context.chat_data["log"]` alongside everything else (an earlier version held them in plain Python globals, which leaked state across every chat the bot was handling — fixed). The numeric parsing helpers (`check_for_int_in_user_message`, `check_for_float_in_user_message`) split each reply into tokens and try to parse each one as a number, returning a single value only when exactly one clean number is found, and a list otherwise (zero numbers found, or more than one) — the caller treats any list as "ask again." Two small known rough edges: a list return doesn't distinguish "you typed nothing numeric" from "you typed more than one number," so the reprompt wording is a little generic either way, and a decimal typed with a comma instead of a dot (e.g. `70,5`) currently fails to parse and triggers the same generic reprompt rather than a message that points at the format specifically.

**General chat:** any message outside registration, program review, and logging goes to the LLM with the full conversation history for that chat (stored in-memory in `context.chat_data["history"]`, a growing list of `{"role", "content"}` messages), seeded the first time it's created with a system message (`program_generator.define_llm()`) describing Hippity's identity, tone, and command list — the same identity text is reused as the base of the program-generation system prompt, so both features share one source of truth for who Hippity is. Conversation history resets if the bot process restarts — persisting it to the database is a known future improvement, not yet done.

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

- [ ] Wire up `/progress <exercise>` to `database.check_progress()`, which already implements the rep/weight/RIR progressive-overload logic
- [ ] Add `/changeprofile` — same free-text extraction approach as registration, but seeded with the user's existing profile and requiring a preview/confirm step before overwriting
- [ ] Persist conversation history to the database so it survives a bot restart
- [ ] Decide whether the free-text "it's fine, save it" shortcut during program review should stay a quiet convenience or become a documented, intentional part of the command flow
- [ ] Add a defensive `try`/`except` around the JSON parsing in `/yes`'s program-save path, as a second line of defense beyond the upstream state-clearing fix
- [ ] Consider sending an approved program as a PDF, for a more durable copy than plain chat text
- [ ] Add basic tests around database and program generation logic
