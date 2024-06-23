from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, date

class UsersBase(BaseModel):
    user_id: Optional[UUID]
    user_name: str = Field(min_length=3)
    user_email: str
    user_created_at: Optional[datetime]
    user_phone_number: str
    role: str

class JobsBase(BaseModel):
    job_id: Optional[UUID]
    job_position: str = Field(min_length=3)
    job_location: str = Field(min_length=3)
    job_company:str = Field(min_length=3)
    job_status:str
    job_mode:str
    job_created_at: Optional[datetime]