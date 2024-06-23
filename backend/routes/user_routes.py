from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from models import Users
from .auth_routes import get_current_user
from passlib.context import CryptContext
from database import SessionLocal, engine

user_router = APIRouter(prefix="/user", tags=["User"])

session = SessionLocal(bind=engine)

#User Verification Model
class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)

#Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@user_router.get("/get_user", status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return db.query(Users).filter(Users.user_id == user.get('user_id')).first()


@user_router.put("/change_password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency, user_verification: UserVerification):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    user_model = db.query(Users).filter(
        Users.user_id == user.get('user_id')).first()

    if not bcrypt_context.verify(user_verification.password, user_model.user_password):
        raise HTTPException(status_code=401, detail='Error on password change')
    user_model.user_password = bcrypt_context.hash(
        user_verification.new_password)
    db.add(user_model)
    db.commit()