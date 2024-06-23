from datetime import datetime
from typing import Annotated, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from .auth_routes import get_current_user
from models import Jobs
from passlib.context import CryptContext
from database import SessionLocal, engine
from enum import Enum

job_router = APIRouter(prefix="/job", tags=["job"])

session = SessionLocal(bind=engine)

class StatusChoice(str,Enum):
    PENDING = 'pending'
    INTERVIEW = 'interview'
    DECLINE = 'decline'

class ModeChoice(str,Enum):
    FULLTIME = 'fulltime'
    PARTTIME = 'parttime'
    INTERNSHIP = 'decline'

class JobRequest(BaseModel):
    job_position: str = Field(min_length=3,max_length=100)
    job_company: str = Field(min_length=3, max_length=100)
    job_location: str = Field(min_length=3, max_length=150)
    job_status: StatusChoice = Field(default=StatusChoice.PENDING)
    job_mode: ModeChoice = Field(default=ModeChoice.FULLTIME)

    class Config:
        json_schema_extra = {
            'example':{
                'job_position':'Software Developer',
                'job_company':'Google',
                'job_location':"Banglore",
                'job_status':"pending",
                'job_mode':"fulltime"
            }
        }



# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@job_router.get('/get_all_jobs', status_code=status.HTTP_200_OK)
async def get_all_jobs(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return db.query(Jobs).filter(Jobs.owner_id==user.get('user_id')).all()


@job_router.post('/create_job',status_code=status.HTTP_201_CREATED)
async def create_job(user:user_dependency,db:db_dependency,job_request:JobRequest):
    if user is None:
        raise HTTPException(status_code=401,detail='Authentication Failed')
    job_id = str(uuid4())
    current_time = datetime.utcnow()
    create_job_model = Jobs(
        job_id = job_id,
        job_position =  job_request.job_position,
        job_company = job_request.job_company,
        job_location = job_request.job_location,
        job_created_at = current_time,
        job_status = job_request.job_status.value.upper(),
        job_mode = job_request.job_mode.value.upper(),
        owner_id = user.get('user_id'),
    )
    db.add(create_job_model)
    db.commit()

@job_router.get('/get_job/{job_id}',status_code=status.HTTP_200_OK)
async def get_job(user:user_dependency,db:db_dependency,job_id:str):
    if user is None:
        raise HTTPException(status_code=401,detail='Authentication Failed')
    job_model = db.query(Jobs).filter(Jobs.job_id==job_id).first()
    if job_model is not None:
        return job_model
    raise HTTPException(status_code=404,detail='Job not found')

@job_router.put('/update_job/{job_id}',status_code=status.HTTP_204_NO_CONTENT)
async def update_job(user:user_dependency,db:db_dependency,job:JobRequest,job_id:str):
    if user is None:
            raise HTTPException(status_code=401,detail='Authentication Failed')
    job_model = db.query(Jobs).filter(Jobs.job_id == job_id).filter(Jobs.owner_id==user.get('user_id')).first()
    if job_model is None:
        raise HTTPException(status_code=404,detail="Job not found")
    job_model.job_company = job.job_company
    job_model.job_position = job.job_position
    job_model.job_location = job.job_location
    job_model.job_status = job.job_status.value.upper()
    job_model.job_mode = job.job_mode.value.upper()

    db.add(job_model)
    db.commit()

@job_router.delete('/delete_job/{job_id}',status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(user:user_dependency,db:db_dependency,job_id:str):
    if user is None:
        raise HTTPException(status_code=401,detail='Authentication Failed')
    job_model = db.query(Jobs).filter(Jobs.job_id == job_id).filter(Jobs.owner_id==user.get('user_id')).first()
    if job_model is None:
        raise HTTPException(status_code=404,detail='Job not found')
    db.delete(job_model)
    db.commit()