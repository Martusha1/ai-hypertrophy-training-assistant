def weekly_volume_by_mg(s):
    result={}
    for item in s:
        m=item["muscle"]
        if m not in result: # check if specific muscle not yet in result dict
            result[m]=item.get("sets")*item.get("reps")*item.get("weight")
        else: # check if specific muscle already in result dict, in order to only add to existing value
            result[m]+=item.get("sets")*item.get("reps")*item.get("weight")
    return result

def simpler_ver(s):
    result={}
    for item in s:
        m=item["muscle"]
        result[m] = result.get(m, 0) + item["sets"] * item["reps"] * item["weight"]
        # because result.get reads the value of m and return 0 if it doesnt exist
        # so it works when creating new keys and adding onto the values of existing ones
    return result



sessions = [
    {"exercise": "Squat", "muscle": "quads", "sets": 4, "reps": 8, "weight": 100},
    {"exercise": "RDL", "muscle": "hamstrings", "sets": 3, "reps": 10, "weight": 80},
    {"exercise": "Leg Press", "muscle": "quads", "sets": 3, "reps": 12, "weight": 150},
]



print(weekly_volume_by_mg(sessions))
print(simpler_ver(sessions))