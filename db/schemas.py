from pydantic import BaseModel, EmailStr
from typing import Optional, Set
from datetime import datetime
from fastapi_users import schemas
import uuid
from dependencies.helper import SkillName



class UserRead(schemas.BaseUser[uuid.UUID]):
    role: str
    name: Optional[str]
    phone: Optional[str]
    # email: Optional[str]
    canceled_count : Optional[int]
    car_type: Optional[str]
    car_model: Optional[str]
    user_lat: Optional[float]
    user_lng: Optional[float]



class MechanicRead(schemas.BaseUser[uuid.UUID]):
    role: str
    name: Optional[str]
    phone: Optional[str]
    # email: Optional[str]
    workshop_name: Optional[str]
    workshop_lat: Optional[float]
    workshop_lng: Optional[float]
    experience_years: Optional[int]
    is_available: Optional[bool]
    avg_rating: Optional[float] 
    total_jobs: Optional[int]
    review_count: Optional[int]
    canceled_count : Optional[int]


class UserUpdate(BaseModel):
    name: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[EmailStr] = ""
    car_type: Optional[str] = ""
    car_model: Optional[str] = ""

class MechanicUpdate(BaseModel):

    name: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[EmailStr] = ""
    workshop_name: Optional[str] = ""
    experience_years: Optional[int] = -1

class MechanicAdminUpdate(BaseModel):

    name: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[EmailStr] = ""
    workshop_name: Optional[str] = ""
    experience_years: Optional[int] = -1
    avg_rating: Optional[float] = -1
    total_jobs: Optional[int] = -1
    review_count: Optional[int] = -1
    canceled_count : Optional[int] = -1
    
    
class UserCreate(schemas.BaseUserCreate):
    role: str = "user"  
    password : Optional[str] = ""
    name: Optional[str] = ""
    phone: Optional[str] = ""
    # email: Optional[str] = ""
    car_type: Optional[str] = ""
    car_model: Optional[str] = ""


class MechanicCreate(schemas.BaseUserCreate):
    role: str = "mechanic"  
    password : Optional[str] = ""
    name: Optional[str] = ""
    phone: Optional[str] = ""
    # email: Optional[str] = ""
    workshop_name: Optional[str] = ""
    experience_years: Optional[int] = 0
    is_available: Optional[bool] = False
    avg_rating: Optional[float]  = 0.0
    total_jobs: Optional[int] = 0
    review_count: Optional[int] = 0


class AdminRead(schemas.BaseUser[uuid.UUID]):
    role : str
    email: Optional[str]
class AdminCreate(schemas.BaseUserCreate):
    role: str = "admin"
    email: Optional[str] = ""

class ServiceRequestCreate(BaseModel):
    user_id: int
    mechanic_id: Optional[int] = None
    request_type: str
    status: Optional[str] = "pending"
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None

class ServiceRequestBase(BaseModel):
    request_type: str

class ServiceRequestCreate(ServiceRequestBase):
    pass

class ServiceRequestRead(BaseModel):
    request_id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    user_id: uuid.UUID
    mechanic_id: Optional[uuid.UUID]

    class Config:
        from_attributes = True




class LocationTrackingRead(BaseModel):
    request_id: int
    mechanic_lat: float
    mechanic_lng: float
    timestamp: Optional[datetime] = None



class RatingCreate(BaseModel):
    rating: int
    feedback_text: Optional[str] = None

class RatingRead(RatingCreate):
    rating_id: int
    created_at: datetime

    user_id: uuid.UUID
    mechanic_id: uuid.UUID
    request_id: int

    class Config:
        from_attributes = True



class SkillRead(BaseModel):
    skill_id: int
    skill_name: str

    class Config:
        from_attributes = True

class SkillCreate(BaseModel):
    skill_name: str



class MechanicSkillRead(BaseModel):
    skill: SkillRead

    class Config:
        from_attributes = True

class MechanicSkillCreate(BaseModel):
    skills: Set[SkillName]

