import os, json
from dotenv import load_dotenv

load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

from telegram import ForceReply, Update, User, Message
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
from groq import Groq
import program_generator, database

# update is an object that holds all data coming from Telegram
# context is an object that holds data about the status of the library
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # possible first message for when user opens bot for the first time
    await update.message.reply_text("""Hello there, friend! How can I help with your training? \
    Please refer to /help if you want a brief outlook on what I can do.""")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""Here are all commands you can use in Hippity:
    /start : activates Hippity
    /help : lists all possible commands in Hippity
    /register: introduce yourself to Hippity (only for new users)
    /info : describes Hippity's purpose
    /log : allows you to log your workout data
    /progress <exercise> : checks for progression in an exercise of your choice
    /program : show the current program you follow
    /my_programs: lists all your programs
    /new_program : Hippity generates a new program based on your needs""")

# summarizes the bot's purpose in short
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""Hi! My name is Hippity and I am your personal \
    AI-powered hypertrophy assistant! I can hold records of your workout data and \
    analyze trends within your performance to help you overcome your current challenges \
    in the gym strictly based on current scientific evidence. Feel free to ask about \
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

    user = update.effective_user # will pass the the user that sent any update
    user_id = user.id # extract id from user object

    chat_history = context.chat_data

    if isinstance(database.get_user_by_telegram_id(user_id),int):
        await update.message.reply_text("""You're already registered!
        Use /changeprofile to update your info, or /program to see the current program you follow.""")
    else:
        chat_history["registration"] = {} # for signalling that chat is mid-registration
        await update.message.reply_text("""I am Hippity and I will gladly help in \
                achieving all of your fitness goals. Since you're new here, let's start by generating \
                your first training programs based on your profile. Please answer the following questions:
                What's your name?
                How old are you?
                What is your training experience?
                How many days would you like to train per week?
                How long would you like your workouts to be?
                What equipment do you have available?
                What is your goal?""")

    
async def fill_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    message: Message = update.effective_message

    # dict for keeping track of already registered/ missing data
    registrated_user_data = context.chat_data["registration"]

    # user message now contains user's newest reply + profile info he may have already given in a previous reply that still needs correction
    user_message_text = {"role": "user", "content": f"Known so far: {registrated_user_data}. Newest reply: {message.text}"}
    
    llm_response_behaviour = """Act as the user's personal coach in his/hers fitness-journey that \
    specializes in hypertrophy training. You will create a training program according to the user's needs, \
    characteristics and goals by first and foremost extracting his profile information from his message. \
    Your answer should produce a JSON string that follows the following structure:
    {
        "name": name of the user in string,
        "age": age of the user in string,
        "training experience": you decide whether Beginner/Intermediate/Advanced based on user's message,  
        "training days per week": 1 to 7,
        "session length": in minutes,
        "available equipment": gym/dumbbells only/ bodyweight only etc.,
        "goal": maximum hypertrophy/ fitness (if user says strength, then please inform that strength advice is not supported),
        "missing_fields": keep a list of all keys here that you believe the user hasn't given a clear answer to
        "follow_up_message": Your follow up message in case some input is missing
    }
    All fields that you believe can't be filled based on the user's input, should have their value set to None. \
    Return only the JSON. Ensure the JSON is valid and complete. Double-check all brackets and braces are closed. \
    No explanation, no commentary before or after."""

    llm_context = {"role": "system", "content": llm_response_behaviour}

    messages = [llm_context, user_message_text]

    raw_json_profile = program_generator.handle_register_message(messages)

    try:
        formatted_profile = json.loads(raw_json_profile)
    except ValueError:
        print("JSON is probably faulty.")
        return None

    # update registered user data
    for key, value in formatted_profile.items():
        if key in ["missing_fields", "follow_up_message"]:
            continue
        if value != None:
            registrated_user_data[f"{key}"] = value

    if formatted_profile["missing_fields"]:
        await update.message.reply_text(f"{formatted_profile["follow_up_message"]}")
    else:
        await update.message.reply_text("""Profile info extraction done. Please review \
        your data and use /yes if you approve it and /no if something is wrong.""")


async def router_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "registration" in context.chat_data: # user can fill his profile data only if /register was used in prior
        await fill_user_profile(update, context)
    else:
        await talk_to_llm(update, context)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE): # if the user wants to stop registrating
    if "registration" in context.chat_data:
        del context.chat_data["registration"]
        await update.message.reply_text("Registration canceled!")
    else:
        await update.message.reply_text("You haven't begun registrating, therefore nothing to cancel, my dear friend!")

async def yes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def no_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass



def main():
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register", register_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("yes", yes_command))
    application.add_handler(CommandHandler("no", no_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router_func))


    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()