from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# موديل المستخدم الأساسي (مشترك بين الدكتور والمريض)
class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: str = Field(..., description="patient or doctor")
    phone: Optional[str] = None

# موديل التسجيل (Signup)
class UserCreate(UserBase):
    password: str
    doctor_id: Optional[str] = None # للمريض فقط وقت التسجيل

# موديل الـ Exercise (قائمة التمارين)
class Exercise(BaseModel):
    title: str
    category: str # Stretch or Strength
    description: str
    reps_sets: str # e.g., "3 sets, 10 reps"
    image_url: str

# موديل الـ Daily Log (اللي المريض بيملاه كل يوم)
class DailyLog(BaseModel):
    patient_id: str
    exercise_id: str
    completed: bool = True
    pain_level: int = Field(..., ge=0, le=10) # من 0 لـ 10 (VAS)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# موديل الـ NDI Assessment (جزء الـ Onboarding والمتابعة)
class NDIAssessment(BaseModel):
    patient_id: str
    scores: List[int]
    total_score: int
    severity: Optional[str] = None 
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Message(BaseModel):
    sender_email: EmailStr
    receiver_email: EmailStr
    content: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)