import sqlite3, json
import os
DB_PATH = os.path.join(os.path.dirname(__file__), "hypertrophy.db")

def get_user_id(program_id): # so i can pass user_id in log_session func
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT user_id FROM program
    WHERE program_id = ?
""", (program_id,))
    
    user_id = cursor.fetchone()[0]
    
    conn.close()

    return user_id

def get_user_by_telegram_id(telegram_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT user_id from users
    WHERE telegram_id = ?
""", (telegram_id,))

    try:
        user_id = cursor.fetchone()[0] # fetchone() could return (None,) if there user not yet registered
        conn.close()
        return user_id
    except TypeError: # because None[0] can't run
        print("This user is not yet registered in the database.")
        conn.close()


def save_user(user, telegram_id):
    conn = sqlite3.connect(DB_PATH)
    # opens a connection to the database; if it doesn't exist,
    # SQLite creates it
    cursor = conn.cursor()
    # runs SQL statements through the connection

    cursor.execute("""
        INSERT INTO users (telegram_id, name, age, training_experience,
        training_days_per_week, session_length,
        available_equipment, goal) VALUES (?,?,?,?,?,?,?,?)
    """, (telegram_id, user["name"], user["age"], user["training experience"], user["training days per week"],
    user["session length"],user["available equipment"], user["goal"]))

    # sends SQL statements to DB through the cursor
    # but doesn't save anything, it just queues them up

    conn.commit()
    # saves everything you've inserted/updated/deleted until now
    conn.close()
    # closes the connection

    return cursor.lastrowid # gives back the ID that SQLite auto-generated after an INSERT

def save_program(user_id, formatted_program):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    raw_json = json.dumps(formatted_program)
    
    cursor.execute("""
        INSERT INTO program (user_id, program_name,
        weeks, raw_json) VALUES (?,?,?,?)
    """, (user_id, formatted_program["program_name"], formatted_program["weeks"], raw_json))

    conn.commit()
    conn.close()

    return cursor.lastrowid # returns program_id

def get_programs(user_id): 
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT program_id, program_name FROM program
        WHERE user_id = ?
""", (user_id,))
    
    all_programs = cursor.fetchall() # fetches multiple things
    conn.close()

    return all_programs # returns a list of all programs
    
def get_program_day(program_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT raw_json from program
    WHERE program_id = ?
    """, (program_id,)) # , is needed because
    # execute expects 2nd arg to be a tuple or list
    
    rj = cursor.fetchone()[0] # because the result need to be
    # a tuple or list, we can also address which part of it we want
    conn.close()

    return json.loads(rj) # return raw json of program details for certain day

def log_session(program_id, user_id, day_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO workout_sessions(program_id, user_id, day_number)
    VALUES (?,?,?)
""", (program_id, user_id, day_number))
    
    conn.commit()
    conn.close()

    return cursor.lastrowid # return workout_id

def save_set(workout_id, exercise_name, set_number, reps_done, weight_kg, rir):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    weight_lbs = weight_kg * 2.20462

    cursor.execute("""
    INSERT INTO logged_sets (workout_id, exercise_name,
    set_number, reps_done, weight_kg, weight_lbs, rir)
    VALUES (?,?,?,?,?,?,?)
""",(workout_id, exercise_name, set_number, reps_done, weight_kg, weight_lbs, rir))
    
    conn.commit()
    conn.close()

    return cursor.lastrowid # return new set id

def check_progress(exercise_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT workout_sessions.workout_id, logged_sets.exercise_name, logged_sets.set_number, logged_sets.reps_done, logged_sets.weight_kg, logged_sets.rir
    FROM logged_sets
    JOIN workout_sessions ON logged_sets.workout_id = workout_sessions.workout_id
    WHERE logged_sets.exercise_name = ?
    ORDER BY workout_sessions.session_date ASC
""", (exercise_name, ))
    
    sessions = cursor.fetchall() # returns a tuple of tuples
    
    ex_history = {}
    for w in sessions:
        if w[0] not in ex_history:
            ex_history[w[0]] = []
        ex_history[w[0]].append(w[2:6])

    # ex_history dict approx. looks like this
    # {5: [(1, 5, 100, 1), (2, 4, 100, 1)],
    # 6: [(1, 7, 100, 1), (2, 6, 100, 1)] }

    ex_history_list = list(ex_history.values())

    if len(ex_history_list) < 2:
        return "Not enough sessions to determine if progress is achieved. Please have at least 2 logged sessions."

    # conditions for trueness of progressive overload:
    # top set must improve, maintain or have more rir
    # no set can drop by more than 3 reps compared to the same set last session
    # big weight drops (over 20%) need low rir to count, otherwise it's junk volume

    current_session = ex_history_list[-1]
    previous_session = ex_history_list[-2]

    curr_top_set_reps = current_session[0][1]
    curr_top_set_weight = current_session[0][2]
    curr_top_set_rir = current_session[0][3]

    prev_top_set_reps = previous_session[0][1]
    prev_top_set_weight = previous_session[0][2]
    prev_top_set_rir = previous_session[0][3]

    if curr_top_set_weight >= prev_top_set_weight: # checking valid top set conditions
        if curr_top_set_reps >= 4:
            if curr_top_set_rir <= 2:
                if curr_top_set_rir >= prev_top_set_rir:
                    if curr_top_set_weight > prev_top_set_weight: # checking if top set
                        if curr_top_set_reps >= 4:
                                progress = True
                        else:
                            progress = False
                    elif curr_top_set_weight == prev_top_set_weight:
                        if curr_top_set_reps > prev_top_set_reps:
                            progress = True
                        elif curr_top_set_reps == prev_top_set_reps:
                            progress = False
                        else:
                            progress = False
                    else:
                        progress = False
                    for curr_output, prev_output in zip(current_session[1:], previous_session[1:]): # referring to all sets after 1st set by pairing them to check remaining conditions
                        # pairs look approx. like this:
                        # curr_output = (2, 7, 100.0, 1)
                        # prev_output = (2, 5, 100.0, 1)

                        curr_set_number = curr_output[0]
                        curr_reps = curr_output[1]
                        curr_weight = curr_output[2]
                        curr_rir = curr_output[3]

                        prev_reps = prev_output[1]
                        prev_weight = prev_output[2]

                        # Branching out different weight and reps scenarios
                        if curr_weight > prev_weight: # more weight than last time means only rep count must be valid
                            if curr_reps >= 4: # minimum rep count check
                                    if 0 <= curr_rir <= 2: # effort check
                                        progress = True
                                        continue
                                    else:
                                        conn.close()
                                        return f"Too little effort on set {curr_set_number} - aim for RIR of 0-2 reps in order to achieve enough mechanical tension."
                            else:
                                conn.close()
                                return f"Reps too low on set {curr_set_number} - possible acute fatigue."
                        elif curr_weight == prev_weight: # same weight as last time
                            if curr_top_set_reps > prev_top_set_reps: # rep count must be valid relative to last time, thus in the worst case not drop too much
                                if curr_reps >= prev_reps - 3: # valid rep difference check
                                    if curr_reps <= curr_top_set_reps: # reps must naturally decline if top set was truly at high intensity
                                        if 0 <= curr_rir <= 2:
                                            progress = True
                                            continue
                                        else:
                                            conn.close()
                                            return f"Too little effort on set {curr_set_number} - aim for RIR of 0-2 reps in order to achieve enough mechanical tension."                                    
                                    else: # top set was underperformed and a later set came up better
                                        if 0 <= curr_rir <= 2:
                                            progress = True
                                            print(f"Beware that set {curr_set_number} was better than your top set. Please warm up efficiently before your top set to avoid injury.")
                                            continue
                                        else:
                                            conn.close()
                                            return f"Too little effort on set {curr_set_number} - aim for RIR of 0-2 reps in order to achieve enough mechanical tension."
                                else:
                                    conn.close()
                                    return f"Reps too low on set {curr_set_number} - possible acute fatigue."
                            elif curr_top_set_reps == prev_top_set_reps:
                                if curr_reps > prev_reps:
                                    if 0 <= curr_rir <= 2:
                                        progress = True
                                        print(f"Beware that set {curr_set_number} was better than your top set. Please warm up efficiently before your top set to avoid injury.")
                                        continue
                                    else:
                                        conn.close()
                                        return f"Too little effort on set {curr_set_number} - aim for RIR of 0-2 reps in order to achieve enough mechanical tension."
                                elif curr_reps >= prev_reps - 3:
                                    if 0 <= curr_rir <= 2:                                        
                                        continue # no progress yet but rest of sets must be checked for progress
                                    else:
                                        conn.close()
                                        return f"Too little effort on set {curr_set_number} - aim for RIR of 0-2 reps in order to achieve enough mechanical tension."
                                else:
                                    conn.close()
                                    return f"Reps too low on set {curr_set_number} - possible acute fatigue."
                            else:
                                conn.close()
                                return "Top set reps didn't improve. Go for a lighter weight."
                        elif curr_weight >= prev_weight - (1/5) * prev_weight and curr_weight <= (99/100) * prev_weight: # less weight than last time
                            if curr_reps >= 4:
                                if 0 <= curr_rir <= 2:
                                    curr_one_rep_max = curr_weight * (1+curr_reps/30)
                                    prev_one_rep_max = prev_weight * (1+prev_reps/30)
                                    if curr_one_rep_max > prev_one_rep_max:
                                        progress = True
                                        continue
                                    else:
                                        conn.close()
                                        return f"Based on e1RM, your performance decreased on set {curr_set_number}."
                                else:
                                    conn.close()
                                    return f"Too little effort on set {curr_set_number}."
                            else:
                                conn.close()
                                return f"Reps too low on set {curr_set_number} - possible acute fatigue."
                        else:
                            conn.close()
                            return f"Weight dropped too much. Drop no more than 20% of your usual working set load if possible."
                    if progress:
                        conn.close()
                        return "Progressive overload achieved!"
                    else:
                        conn.close()
                        return "Performance maintained - you achieved the same number of reps and effort as last time."
                else:
                    conn.close()
                    return "Top set didn't improve. Your RIR got worse - it took more effort to lift the same volume you lifted last time."
            else:
                conn.close()
                return "Top set didn't improve. Your RIR is over 2 - you left too much in the tank. Go for 0 to 2 reps close to failure."
        else:
            conn.close()
            return "Rep count too low. You possibly picked a weight too heavy for you."
    else:
        conn.close()
        return "Top set didn't improve. You lifted less weight than last time. Go lighter."


def init_db():
    conn = sqlite3.connect("hypertrophy.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL UNIQUE,
        name TEXT,
        age INTEGER NOT NULL,
        training_experience TEXT,
        training_days_per_week INTEGER NOT NULL,
        session_length INTEGER NOT NULL,
        available_equipment TEXT,
        goal TEXT,
        created_at DATE          
        );
""")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS program (
        program_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        program_name TEXT,
        weeks INTEGER NOT NULL,
        raw_json TEXT,
        created_at DATE,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
""")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_sessions (
        workout_id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        session_date DATE,
        day_number INTEGER NOT NULL,
        notes TEXT,
        FOREIGN KEY (program_id) REFERENCES program(program_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
""")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logged_sets (
        sets_id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_id INTEGER NOT NULL,
        exercise_name TEXT,
        set_number INTEGER,
        reps_done INTEGER,
        weight_kg REAL,
        weight_lbs REAL,
        rir INTEGER,
        FOREIGN KEY (workout_id) REFERENCES workout_sessions(workout_id)
        );
""")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()