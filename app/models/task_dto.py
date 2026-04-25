from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TaskDTO(BaseModel):
    id: str
    title: str
    duration_minutes: int
    difficulty: int
    priority: str
    deadline: datetime
    # --- NOUVEAUX CHAMPS POUR LES COURS FIXES ---
    # alias="isFixed" permet à Python de lire le JSON de Java correctement
    is_fixed: bool = Field(default=False, alias="isFixed") 
    start_time: Optional[str] = Field(default=None, alias="startTime")

class StudentProfileDTO(BaseModel):
    student_id: str
    wake_up_time: str
    sleep_time: str
    peak_productivity: str
    energy_score: int

class OptimizationRequest(BaseModel):
    student: StudentProfileDTO
    tasks: List[TaskDTO]
    start_date: datetime