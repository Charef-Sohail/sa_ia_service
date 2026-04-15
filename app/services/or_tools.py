from ortools.sat.python import cp_model
from datetime import timedelta

def generate_schedule(request):
    model = cp_model.CpModel()
    HORIZON = 336 # 7 jours * 48 blocs de 30 min
    
    # 1. Extraction du sommeil
    wake_hour, wake_min = map(int, request.student.wake_up_time.split(':'))
    sleep_hour, sleep_min = map(int, request.student.sleep_time.split(':'))
    wake_bloc = (wake_hour * 2) + (1 if wake_min >= 30 else 0)
    sleep_bloc = (sleep_hour * 2) + (1 if sleep_min >= 30 else 0)

    task_starts = {}
    task_ends = {}
    task_intervals = {}

    # 2. Création des variables
    for task in request.tasks:
        duration_blocs = max(1, task.duration_minutes // 30) 
        start_var = model.NewIntVar(0, HORIZON, f'start_{task.id}')
        end_var = model.NewIntVar(0, HORIZON, f'end_{task.id}')
        interval_var = model.NewIntervalVar(start_var, duration_blocs, end_var, f'interval_{task.id}')
        
        task_starts[task.id] = start_var
        task_ends[task.id] = end_var
        task_intervals[task.id] = interval_var

    # 3. Contraintes
    model.AddNoOverlap(task_intervals.values())
    for task_id, end_var in task_ends.items():
        model.Add(end_var <= sleep_bloc)
        model.Add(task_starts[task_id] >= wake_bloc)

    # 4. Optimisation selon l'énergie
    if request.student.energy_score <= 2:
        model.Maximize(sum(task_starts.values())) # Étale le travail
    else:
        model.Minimize(sum(task_ends.values()))   # Tasse le travail

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # 5. Formatage du résultat
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        planned_tasks = []
        for task in request.tasks:
            start_bloc = solver.Value(task_starts[task.id])
            actual_start_time = request.start_date + timedelta(minutes=start_bloc * 30)
            actual_end_time = actual_start_time + timedelta(minutes=task.duration_minutes)
            
            planned_tasks.append({
                "task_id": task.id,
                "start_time": actual_start_time.isoformat(),
                "end_time": actual_end_time.isoformat()
            })
        return {"status": "SUCCESS", "schedule": planned_tasks}
    else:
        return {"status": "FAILED", "message": "Impossible de trouver un planning avec ces contraintes."}