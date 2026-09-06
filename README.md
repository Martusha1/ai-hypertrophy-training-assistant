# Hippity — AI Hypertrophy Training Assistant

Hippity is an AI-powered training assistant that generates personalized hypertrophy (muscle growth) programs and helps track workout progress over time. It combines an LLM (via Groq) with a structured database of programs, sessions, and exercises, delivered through a Telegram bot and a FastAPI backend.

**Status: actively in development.** The FastAPI backend, database layer, and LLM-based program generation are functional. The Telegram bot is currently a basic scaffold (echo/command handling) and is being wired up to the program generator next.

## What it does (or is being built to do)

- Generates a personalized training program based on the user's experience level, goals, and circumstances, using an LLM (Groq / Llama 3.3)
- Stores programs, sessions, and logged workouts in a SQLite database
- Exposes a FastAPI backend with endpoints to fetch programs, check exercise progress, and log sessions
- Aims to analyze logged workout data to give feedback on progression, deloads, and technique via a Telegram chat interface

## Project structure

```
phase0/   Early standalone scripts — first steps with core training math (1RM, volume, progression logic) and a first LLM API call
phase1/   The actual application
  ├─ database.py           SQLite data layer (users, programs, sessions, exercises)
  ├─ program_generator.py  Builds prompts and calls the LLM to generate a training program
  ├─ main.py                FastAPI app exposing the backend as an API
  ├─ hippity.py             Telegram bot entry point (basic scaffold, not yet connected to program_generator)
  └─ session_logger.py      CLI script for logging a workout session
```

## Tech stack

- **Python**
- **FastAPI** — backend/API layer
- **SQLite** — data storage
- **Groq API (Llama 3.3)** — LLM integration for program generation
- **python-telegram-bot** — Telegram bot interface

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
3. Run the API:
   ```
   uvicorn phase1.main:app --reload
   ```
4. Run the Telegram bot:
   ```
   python phase1/hippity.py
   ```

## Roadmap

- [ ] Connect the Telegram bot to `program_generator.py` so users can generate and receive programs directly in chat
- [ ] Let users log sessions through the bot instead of the CLI
- [ ] Use logged session data to give feedback on progression and suggest deloads
- [ ] Add basic tests around database and program generation logic
