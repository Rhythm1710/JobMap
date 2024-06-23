from typing import Annotated, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from models import Users,Jobs
from database import SessionLocal
from starlette import status
from .auth_routes import get_current_user


admin_router = APIRouter(
    prefix="/admin",
    tags=['admin']
)


def get_db():
    db = SessionLocal()
    try:
        yield db  
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]



@admin_router.get("/get_all_users",status_code=status.HTTP_200_OK)
async def read_all(user:user_dependency,db:db_dependency):
    if user is None or user.get('role')!='admin':
        raise HTTPException(status_code=401,detail="Authentication Failed")
    return db.query(Users).all()

@admin_router.delete('/todo/{todo_id}',status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user:user_dependency,db:db_dependency,user_id:int):
    if user is None or user.get('role')!='admin':
        raise HTTPException(status_code=401,detail='Authentication Failed')
    job_model = db.query(Jobs).filter(Jobs.id==user_id).first()
    if job_model is None:
        raise HTTPException(status_code=404,detail='Todo not found')
    db.delete(job_model)
    db.commit()