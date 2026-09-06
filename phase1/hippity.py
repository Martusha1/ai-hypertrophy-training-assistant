import os
from dotenv import load_dotenv

load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

from telegram import ForceReply, Update, User, Message
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from groq import Groq
import program_generator

# update is an object that holds all data coming from Telegram
# context is an object that holds data about the status of the library
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # possible first message for when user opens bot for the first time
    await update.message.reply_text("""Hello there, friend! How can I help with your training?
    Please refer to /help if you want a brief outlook on what I can do.""")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""Here are all commands you can use in Hippity:
    /start : activates Hippity
    /help : lists all possible commands in Hippity
    /info : describes Hippity's purpose
    /log : allows you to log your workout data
    /progress <exercise> : checks for progression in an exercise of your choice
    /program : show the current program you follow
    /all_programs: lists all your programs
    /new_program : Hippity generates a new program based on your needs""")

# summarizes the bot's purpose in short
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""Hi! My name is Hippity and I am your personal
    AI-powered hypertrophy assistant! I can hold records of your workout data and
    analyze trends within your performance to help you overcome your current challenges
    in the gym strictly based on current scientific evidence. Feel free to ask about
    anything that's on your mind about muscle building and I will do my best to inform you.""")

async def talk_to_llm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message: Message = update.effective_message

    message_text = message.text

    llm_response = program_generator.telegram_message_to_llm(message_text)

    await update.message.reply_text(llm_response)



def main():
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, talk_to_llm))


    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()