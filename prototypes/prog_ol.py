def did_progress(s1, s2):
    avg1 = sum(s1) / len(s1) # sum of s1 is 215 divided by
    # the length of s1 which is 3
    avg2 = sum(s2) / len(s2)
    
    return avg2 > avg1

session1 = [70,65,80]
session2 = [85,70,65]

print(did_progress(session1, session2))