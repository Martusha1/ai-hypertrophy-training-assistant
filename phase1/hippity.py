import os
from dotenv import load_dotenv

load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

from telegram import ForceReply, Update, User, Message
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
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
    
    user_message_text = {"role": "user", "content": message.text} # underline which messages are from the user by following LLM call shape
    
    chat_history = context.chat_data
    if bool(chat_history) == True:
        pass
    else: # if no chat history yet, then create a key that will store all messages as a list
        chat_history["history"] = [] # preparing the history to be a list of dicts
    chat_history["history"].append(user_message_text)
    
    llm_response = program_generator.telegram_message_to_llm(chat_history["history"])
    llm_message_text = {"role": "assistant", "content": llm_response} # underline which messages are from the LLM

    chat_history["history"].append(llm_message_text)

    await update.message.reply_text(llm_response)

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass



def main():
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, talk_to_llm))


    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()