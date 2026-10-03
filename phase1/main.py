from fastapi import FastAPI
from phase1 import database

app = FastAPI()

@app.get("/") # in case of no specific request
def default():
    return {"message": "Hypertrophy API running"}

@app.get("/progress/{exercise_name}") # in case of progression request
def get_progress(exercise_name: str):
    result = database.check_progress(exercise_name)
    return {"Result": result}

@app.get("/programs") # request to list all programs
def http_get_programs():
    programs = database.get_programs()
    return {"Programs": programs}

@app.post("/session/log/{program_id}/{user_id}/{day_number}") # request to update stored data
def http_log_session(program_id: int, user_id: int, day_number: int):
    workout_id = database.log_session(program_id, user_id, day_number)
    return {"Workout logged": workout_id}

