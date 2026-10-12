def plan_mesocycle(starting_sets, weeks):
    weekly_sets=[]
    planned_sets=starting_sets
    for curr_week in range(weeks):
        weekly_sets.append(planned_sets)
        planned_sets+=1

    return weekly_sets


weekly_sets=plan_mesocycle(3,4)

for curr_week, set_count in enumerate(weekly_sets):
    print(f"Week {curr_week+1}: {set_count} sets")

        