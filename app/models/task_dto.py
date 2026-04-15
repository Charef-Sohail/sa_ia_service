from pydantic import BaseModel
from typing import List
from datetime import datetime

class TaskDTO(BaseModel):
    id: str
    title: str
    duration_minutes: int
    difficulty: int
    priority: str
    deadline: datetime

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