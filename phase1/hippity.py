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

    chat_history = context.chat_data

    init_chat_history(chat_history)

    await update.message.reply_text("Hello there, friend! How can I help with your training? \
Please refer to /help if you want a brief outlook on what I can do.")

def init_chat_history(chat_history): # makes the frequent check if "history" exists, more convenient

    llm_behaviour = program_generator.define_llm()
    
    if "history" in chat_history:
        return
    else:
        chat_history["history"] = []
        chat_history["history"].append(llm_behaviour)

def init_program_history(program_history):
    program_history["programs"] = [] # ensures list is emptied before used
    return

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""Here are all commands you can use in Hippity:
/help : lists all possible commands in Hippity
/info : describes Hippity's purpose
/register: start registration process (only for new users)
/fill_user_profile: tell Hippity more about yourself (use after /register)
/yes: approves profile extraction results or a new program
/no: denies extracted profile details or a new program and asks for correction
/program : shows the current program you follow
/my_programs: lists all your programs
/new_program : Hippity generates a new program based on your needs
/log : allows you to log your workout session details (sets, reps, RIR)
/progress <exercise> : checks if progressive overload is achieved in an exercise of your choice
""")

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE): # summarizes the bot's purpose in short
    await update.message.reply_text("""Hi! My name is Hippity and I am your personal \
AI-powered hypertrophy assistant! I can hold records of your workout data and \
analyze trends within your performance to help you overcome your current challenges \
in the gym strictly based on current scientific evidence. Feel free to ask about \
anything that's on your mind about muscle building and I will do my best to inform you.""")

async def talk_to_llm(update: Update, context: ContextTypes.DEFAULT_TYPE): # processes free text messages from the user

    message: Message = update.effective_message
    
    user_message_text = {"role": "user", "content": message.text} # underline which messages are from the user by following LLM call shape
    
    chat_history = context.chat_data
    init_chat_history(chat_history)
    chat_history["history"].append(user_message_text)

    llm_response = program_generator.telegram_message_to_llm(chat_history["history"])
    llm_message_text = {"role": "assistant", "content": llm_response} # underline which messages are from the LLM

    chat_history["history"].append(llm_message_text)

    await update.message.reply_text(llm_response)

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE): # initializes register process

    user = update.effective_user # will pass the the user that sent any update
    telegram_id = user.id # extract id from user object

    chat_history = context.chat_data

    if isinstance(database.get_user_by_telegram_id(telegram_id),int):
        await update.message.reply_text("""You're already registered! \
Use /changeprofile to update your info, or /program to see the current program you follow.""")
    else:
        chat_history["registration"] = {} # for signalling that chat is mid-registration
        await update.message.reply_text("""I am Hippity and I will gladly help in\
    achieving all of your fitness goals. Since you're new here, let's start by generating \
    your first training programs based on your profile. Please answer the following questions:
    What's your name?
    How old are you?
    What is your training experience?
    How many days would you like to train per week?
    How long would you like your workouts to be?
    What equipment do you have available?
    What is your goal?""")
    
async def fill_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE): # extracts user profile data
    
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
        "training experience": you decide whether Beginner/Intermediate/Advanced based on user's message \
        (consistent lifting for < 1 year is Beginner, 1-2 years is Intermediate, > 3 years is Advanced),  
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
        for key, value in formatted_profile.items():
            if key in ["missing_fields", "follow_up_message"]:
                continue
            await update.message.reply_text(f"{key}: {value}")

async def router_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "registration" in context.chat_data: # user can fill his profile data only if /register was used in prior
        await fill_user_profile(update, context)
    elif "programs" in context.chat_data:
        await revise_program(update, context, context.chat_data["programs"])
    else:
        await talk_to_llm(update, context)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE): # stops the registration process
    if "registration" in context.chat_data:
        del context.chat_data["registration"]
        await update.message.reply_text("Registration cancelled!")
    elif "programs" in context.chat_data:
        del context.chat_data["programs"]
        await update.message.reply_text("New program discussion cancelled!")
    else:
        await update.message.reply_text("""You haven't done anything that utilizes this command. \
You can use it to stop registration and new program generation processes.""")

async def yes_command(update: Update, context: ContextTypes.DEFAULT_TYPE): # approves saving user profile data or new programs

    if "programs" in context.chat_data:
        telegram_id = update.effective_user.id
        user_id = database.get_user_by_telegram_id(telegram_id)
        formatted_p = json.loads(context.chat_data["programs"][0])
        database.save_program(user_id, formatted_p)
        await update.message.reply_text("""Your new program has been saved. Use '/program' \
to preview your current program.""")
        del context.chat_data["programs"]
        return

    if "registration" in context.chat_data: # mid-registration check
        registrated_data = context.chat_data["registration"]
        for key, value in registrated_data.items(): # check if user entered /yes before profile is complete
            if key in ["missing_fields", "follow_up_message"]:
                continue
            if value is None:
                await update.message.reply_text("""Please use this command to approve your registrated data \
only after it's all been fully recorded.""")
                return

        user = update.effective_user
        telegram_id = user.id
        database.save_user(context.chat_data["registration"], telegram_id)
        del context.chat_data["registration"]
        await update.message.reply_text("""Your data has been successfuly saved! If you want me to draft a \
        personal training program according to your current profile, please write /new_program.""")
    else:
        await update.message.reply_text("""This command is only intended for approval of a \
        newly generated program or update in user profile data.""")

async def no_command(update: Update, context: ContextTypes.DEFAULT_TYPE): # denies saving user profile data or new programs

    if "programs" in context.chat_data:
        await update.message.reply_text("""Please tell me exactly what you didn't like in the last \
program so I can propose something more suitable for your needs.""")
        return

    if "registration" in context.chat_data:
        await update.message.reply_text("Please point out what exactly needs to be added or corrected to your data. \
        You can also use /cancel to terminate the entire registration process.")
    else:
        await update.message.reply_text("""This command is only intended for denial of a \
        newly generated program or update in user profile data.""")

async def new_program_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    telegram_id = update.effective_user.id
    user_id = database.get_user_by_telegram_id(telegram_id)

    if user_id is None:
        await update.message.reply_text("""You haven't registered yet. Please use /register to start \
the registration process and tell Hippity more about yourself.""")
    else:
        user_profile = database.get_user_profile(user_id)

        messages_to_llm = []
        llm_program_generation_instruction = {"role": "system", "content": program_generator.build_system_prompt(user_profile)}
        user_message = {"role": "user", "content": "Please generate my program now."}
        messages_to_llm.extend([llm_program_generation_instruction, user_message])

        program_history = context.chat_data
        init_program_history(program_history)

        program = program_generator.generate_program(messages_to_llm)
        program_history["programs"].append(program)

        display_ready_program = await parse_and_display_program(update, context, program)
        if display_ready_program is None:
            return
        await update.message.reply_text("""Your new program is done. Please review it \
and let me know if I should save it by writing '/yes' or '/no' if you would like a new one.""")
        
        await update.message.reply_text(display_ready_program)

async def parse_and_display_program(update: Update, context: ContextTypes.DEFAULT_TYPE, program):
    try:
        formatted_p = json.loads(program)
    except ValueError: # LLM sometimes fails to deliver raw JSON
        await update.message.reply_text("""There was an error generating your program. \
Please try again by using '/new_program' again.""")
        formatted_p = None
        return formatted_p

    program_message = formatted_p["program_name"]
    program_message += f"\nWeeks: {formatted_p["weeks"]}\n"

    for day in formatted_p["days"]: # loops only needed for lists
        
        program_message += f"Day: {day["day"]}\n"
        
        for muscle in day["muscles_targeted"]:
            program_message += f"{muscle} " # prevents newline when several muscles get printed
        
        program_message += "\nWarmup:"
        for drill in day["warmup"]:
            program_message += f"- {drill}\n"
        
        program_message += "Exercises:\n"
        for exercise in day["exercises"]:
            program_message += f"{exercise["name"]}: "
            program_message += f"{exercise["sets"]} sets X {exercise["reps"]} reps\n"

        program_message += "Cooldown:\n"
        for info in day["cooldown"]:
            program_message += f"- {info}\n"
        
        program_message += "Technique notes:\n"
        for ex_name, cue  in day["technique_notes"].items():
            program_message += f"- {ex_name}: {cue}\n"

    return program_message

async def revise_program(update: Update, context: ContextTypes.DEFAULT_TYPE, program_history):

    telegram_id = update.effective_user.id
    user_id = database.get_user_by_telegram_id(telegram_id)
    user_dict = database.get_user_profile(user_id)

    message: Message = update.effective_message
        
    user_message = {"role": "user", "content": "Please generate the corrected program now."}
    program_correction_context = {"role": "system", "content": f"""You already generated the following program \
for the user: {program_history[0]}. The user either didn't explicitly approve it via '/yes' as instructed and just wrote something \
in free text or he didn't like and requested correction via '/no'. He said: {message.text}. \
If he wants a correction of the program, then please take these into account. If not and he is just writing about something
irrelevant to his new program, please tell him that he is mid-new-program-generation and needs to review his new program
by either approving it via '/yes' or request correction via '/no'."""}
    program_generation_instruction = {"role": "system", "content": program_generator.build_system_prompt(user_dict)}
    messages = [program_generation_instruction, program_correction_context, user_message]

    corrected_program = program_generator.generate_program(messages)
    
    display_ready_program = await parse_and_display_program(update, context, corrected_program)
    if display_ready_program is None:
        return
    program_history[0] = corrected_program
    await update.message.reply_text("""Your new program is done. Please review it \
and let me know if I should save it by writing '/yes' or '/no' if you would like a new one.""")
    
    await update.message.reply_text(display_ready_program)
    
    

async def my_programs(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    application.add_handler(CommandHandler("new_program", new_program_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router_func))


    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()