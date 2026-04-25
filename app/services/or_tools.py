from ortools.sat.python import cp_model
from datetime import timedelta, datetime

def generate_schedule(request):
    model = cp_model.CpModel()
    HORIZON_MINUTES = 7 * 24 * 60 # 7 jours en minutes
    
    task_starts = {}
    task_ends = {}
    task_intervals = {}

    if isinstance(request.start_date, str):
        global_start_dt = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
    else:
        global_start_dt = request.start_date

    global_start_dt = global_start_dt.replace(tzinfo=None)

    for task in request.tasks:
        duration = task.duration_minutes

        if task.is_fixed and task.start_time:
            # COURS FIXE
            if isinstance(task.start_time, str):
                task_start_dt = datetime.fromisoformat(task.start_time.replace('Z', '+00:00'))
            else:
                task_start_dt = task.start_time
                
            task_start_dt = task_start_dt.replace(tzinfo=None)
            
            start_minute = int((task_start_dt - global_start_dt).total_seconds() / 60)
            end_minute = start_minute + duration
            
            start_var = model.NewIntVar(start_minute, start_minute, f'start_{task.id}')
            end_var = model.NewIntVar(end_minute, end_minute, f'end_{task.id}')
            interval_var = model.NewIntervalVar(start_var, duration, end_var, f'interval_{task.id}')
            
        else:
            # TÂCHE FLEXIBLE
            if isinstance(task.deadline, str):
                task_deadline_dt = datetime.fromisoformat(task.deadline.replace('Z', '+00:00'))
            else:
                task_deadline_dt = task.deadline
                
            task_deadline_dt = task_deadline_dt.replace(tzinfo=None)
            
            max_minute = int((task_deadline_dt - global_start_dt).total_seconds() / 60)
            
            # Sécurité pour éviter les deadlines dans le passé
            if max_minute < duration:
                max_minute = duration

            start_var = model.NewIntVar(0, max_minute - duration, f'start_{task.id}')
            end_var = model.NewIntVar(duration, max_minute, f'end_{task.id}')
            interval_var = model.NewIntervalVar(start_var, duration, end_var, f'interval_{task.id}')

        task_starts[task.id] = start_var
        task_ends[task.id] = end_var
        task_intervals[task.id] = interval_var

    # 3. Contraintes : Pas de chevauchement !
    model.AddNoOverlap(task_intervals.values())
    
    # Note : Les contraintes de sommeil ont été retirées temporairement car elles 
    # nécessitent de calculer les nuits exactes sur l'horizon des 7 jours en minutes.

    # 4. Optimisation
    if request.student.energy_score <= 2:
        model.Maximize(sum(task_starts.values()))
    else:
        model.Minimize(sum(task_ends.values()))

    solver = cp_model.CpSolver()
    # --- LA LIGNE MAGIQUE À AJOUTER ---
    # On donne 10 secondes maximum à l'IA pour trouver le planning
    solver.parameters.max_time_in_seconds = 10.0 
    
    status = solver.Solve(model)

    # 5. Formatage du résultat
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        planned_tasks = []
        for task in request.tasks:
            # On récupère la vraie valeur en minutes calculée par l'IA
            start_minute_val = solver.Value(task_starts[task.id])
            
            # On ajoute ces minutes à la date de départ globale
            actual_start_time = global_start_dt + timedelta(minutes=start_minute_val)
            actual_end_time = actual_start_time + timedelta(minutes=task.duration_minutes)
            
            planned_tasks.append({
                "task_id": task.id,
                "start_time": actual_start_time.isoformat() + "Z",
                "end_time": actual_end_time.isoformat() + "Z"
            })
        return {"status": "SUCCESS", "schedule": planned_tasks}
    else:
        return {"status": "FAILED", "message": "Impossible de trouver un planning avec ces contraintes."}