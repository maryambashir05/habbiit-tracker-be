from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date, time
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class User(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class HabitCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    color: str
    reminder_time: Optional[time] = None

class Habit(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    color: str
    reminder_time: Optional[time] = None
    is_archived: bool
    streak_count: int
    longest_streak: int
    created_at: datetime
    updated_at: datetime

class HabitEntryCreate(BaseModel):
    date: date
    notes: Optional[str] = None

class HabitEntry(BaseModel):
    id: UUID
    habit_id: UUID
    user_id: UUID
    date: date
    notes: Optional[str] = None
    completed_at: datetime
    created_at: datetime

class AnalyticsSummary(BaseModel):
    current_streak: int
    longest_streak: int
    completion_rate: float
    total_completions: int

class HabitAnalytics(BaseModel):
    streak_data: AnalyticsSummary
    completion_history: List[date] 