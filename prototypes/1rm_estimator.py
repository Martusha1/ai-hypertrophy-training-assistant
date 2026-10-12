import math

def onerep_max(weight, reps):
    result = weight*(1+reps/30)
    return round(result,1)

print (onerep_max(70,8))