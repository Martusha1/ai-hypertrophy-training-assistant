import os, json, database
from groq import Groq

from dotenv import load_dotenv

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")

def get_name():
    while True:
        name = input("Please enter your name: ")
        if name.isdigit():
            print("Please use only letters. ")
        else: break
    return name

def get_age():
    while True:
        age = input("Please enter your age: ")
        if age.isdigit():
            age = int(age)
            if age > 0 and age <= 122:
                break
            else:
                print("Please enter a valid age. ")
        else:
            print("Please use only numbers. ")
    return age

def get_training_exp():
    while True:
        training_exp = input("Please select the number corresponding to your training experience: 1. Beginner, 2. Intermediate, 3. Advanced. ")
        if training_exp.isdigit():
            training_exp=int(training_exp)
            if training_exp in [1,2,3]:
                if training_exp == 1:
                    training_exp = "Beginner"
                elif training_exp == 2:
                    training_exp = "Intermediate"
                else:
                    training_exp = "Advanced"
                break
            else:
                print("Please select a number from 1 to 3 depending on your training experience. ")
        else:
            print("Please enter the number standing to your individual training experience. ")
    return training_exp

def get_training_days_per_week():
    while True:
        days = input("Please enter how many days per week you would like to train: ")
        if days.isdigit():
            days=int(days)
            if days >= 1 and days <= 7:
                break
            else:
                print("Please enter a valid number of days within a week. ")
        else:
            print("Please enter a valid number. ")
    return days
    
def get_session_length():
    while True:
        length = input("Please enter how many minutes per session you would like to train: ")
        if length.isdigit():
            length=int(length)
            if length >= 15 and length <= 360:
                break
            else:
                print("Please enter a valid session length. ")
        else:
            print("Please enter a number representing the amount of time you would like to train per session in minutes. ")
    return length

def get_available_equipment():
    while True:
        equipment=input("Please select what equipment you have available by choosing its corresponding number: 1. Full gym, 2. Dumbbells, 3. Barbell, 4. Bench, 5. Rack, 6. Resistance bands, 7. Nothing. ")
        if equipment.isdigit():
            equipment=int(equipment)
            if equipment in [1,2,3,4,5,6,7]:
                match equipment:
                    case 1:
                        equipment = "Full gym"
                        break
                    case 2:
                        equipment = "Dumbbells"
                        break
                    case 3:
                        equipment = "Barbell"
                        break
                    case 4:
                        equipment = "Bench"
                        break
                    case 5:
                        equipment = "Rack"
                        break
                    case 6:
                        equipment = "Resistance bands"
                        break
                    case 7:
                        equipment = "Nothing"
                        break
                    case _:
                        print("Error. Please try again. ")
            else:
                print("Please select a number from 1 to 7. ")
        else:
            print("Please select a number that correlates to your equipment. ")
    return equipment

def get_goal():
    while True:
        goal = input("Please select the number corresponding to your goal: 1. Maximum hypertrophy, 2. General fitness (based on muscle building). ")
        if goal.isdigit():
            goal=int(goal)
            if goal in [1,2]:
                if goal == 1:
                    goal = "Maximum hypertrophy"
                    break
                else:
                    goal = "General fitness (based on muscle building)"
                    break
            else:
                print("Please enter either 1 or 2 depending on your goal. ")
        else:
            print("Please use only a number. ")
    return goal

def get_user_profile():

    user = {"name": None, "age": None, "training experience": None,
            "training days per week": None, "session length": None,
            "available equipment": None, "goal": None}
    
    user["name"]=get_name()
    user["age"]=get_age()
    user["training experience"]=get_training_exp()
    user["training days per week"]=get_training_days_per_week()
    user["session length"]=get_session_length()
    user["available equipment"]=get_available_equipment()
    user["goal"]=get_goal()
    
    return user

def build_system_prompt(user):
    instruction = f"""Act as my personal coach in my fitness-journey that specializes in hypertrophy training \
for both complete beginners and also advanced. You will create a training program according to my needs, \
characteristics and goals. Be direct, evidence-based, no fluff, no hype, but also not condescending, and \
comfortable saying 'the research isn't clear on this' rather than faking certainty. Skip motivational filler \
unless the user expresses discouragement. You don't have to act numb to show seriousness, so show kindness and \
empathy when needed. Cite relevant research or established scientific consensus where applicable. \
If evidence is limited or conflicting, say so. Don't validate bad practices to be polite. \
Here is some information about me. My name is {user["name"]} and I am {user["age"]} years old. \
My training experience is at a {user["training experience"]} level. I would like to train {user["training days per week"]} days per week \
with each session preferably being around {user["session length"]} minutes long. Equipment-wise I have {user["available equipment"]} at my disposal. \
My goal is {user["goal"]}. Remember the following gradual warmup: 'Warm-up for compound movements: empty bar X 10 reps -> \
50% of W (Working weight) X 5 reps -> 70% of W X 3 reps -> 90% of W X 1 rep -> 2 min rest. Warm-up for isolated movements: \
50% of W X 8 reps -> 80% of W X 4 reps -> 1 min rest.' Your answers should produce a JSON that follows the following structure: \
{{
  "program_name": "",
  "weeks": 4,
  "days": [
    {{
      "day": integer from 1 to 7,
      "muscles_targeted": [],
      "warmup": [i.e. list of plain strings],
      "exercises": [
        {{
          "name": "",
          "sets": 0,
          "reps": ""
        }}
      ],
      "cooldown": [i.e. list of plain strings],
      "technique_notes": {{
        "exercise_name": "cue or common error to avoid"
      }}
    }}
  ]
}} Return only the JSON. Ensure the JSON is valid and complete. Double-check all brackets and braces are closed." No explanation, no commentary before or after. """

    return instruction

def generate_program(user_profile_message):
    client = Groq(api_key=groq_key)

    response = client.chat.completions.create(model="openai/gpt-oss-20b",
    messages=[{"role": "user", "content": user_profile_message}])
    
    return response.choices[0].message.content

def parse_and_display_program(p):
    try:
        formatted_p = json.loads(p)
    except ValueError: # LLM sometimes fails to deliver raw JSON
        print("JSON is probably faulty.")
        return None
    
    print(formatted_p["program_name"])
    print(f"Weeks: {formatted_p["weeks"]}")

    for day in formatted_p["days"]: # loops only needed for lists
        
        print(f"Day: {day["day"]}")
        
        for muscle in day["muscles_targeted"]:
            print(f"{muscle} ", end="") # prevents newline when several muscles get printed
        
        print("\nWarmup:")
        for drill in day["warmup"]:
            print(f"- {drill}")
        
        print("Exercises:")
        for exercise in day["exercises"]:
            print(f"{exercise["name"]}:")
            print(f"{exercise["sets"]} sets X {exercise["reps"]} reps")

        print("Cooldown:")
        for info in day["cooldown"]:
            print(f"- {info}")
        
        print("Technique notes:")
        for ex_name, cue  in day["technique_notes"].items():
            print(f"- {ex_name}: {cue}")

    return formatted_p

def telegram_message_to_llm(chat_history):
    client = Groq(api_key=groq_key)

    response = client.chat.completions.create(model="openai/gpt-oss-20b", messages=chat_history)

    return response.choices[0].message.content

def handle_register_message(register_message):
    client = Groq(api_key=groq_key)
    
    response = client.chat.completions.create(model="openai/gpt-oss-20b",
    messages=register_message)
        
    return response.choices[0].message.content


def main():
    user = get_user_profile()
    prompt = build_system_prompt(user)
    program = generate_program(prompt)
    formatted_program = parse_and_display_program(program)
    user_id = database.save_user(user)
    program_id = database.save_program(user_id, formatted_program)

if __name__ == "__main__":
        main()

    

    
    

    


