from fastapi import FastAPI, HTTPException
from app.models.task_dto import OptimizationRequest
from app.services.or_tools import generate_schedule

app = FastAPI(title="Smart Calendar - IA Planner")

@app.post("/api/planner/optimize")
def optimize_student_schedule(request: OptimizationRequest):
    if not request.tasks:
        raise HTTPException(status_code=400, detail="Aucune tâche fournie.")
        
    result = generate_schedule(request)
    
    if result["status"] == "FAILED":
        raise HTTPException(status_code=422, detail=result["message"])
        
    return result