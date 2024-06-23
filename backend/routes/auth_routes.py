from enum import Enum
from uuid import uuid4
from jose import jwt,JWTError
from fastapi import Form
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from passlib.context import CryptContext
from models import Users
from database import SessionLocal
from starlette import status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Optional
from datetime import timedelta, datetime,date



#Custom Request Form in Authentication
class OAuth2EmailRequestForm:
    def __init__(self,email:str=Form(...),password:str=Form(...)):
        self.email=email
        self.password=password

# API Router
auth_router = APIRouter(prefix="/auth", tags=['Authentication'])

# Secret key and algo used for jwt authentication
SECRET_KEY = '197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3'
ALGORITHM = 'HS256'


bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/login')

class RoleChoice(str,Enum):
    ADMIN = 'admin'
    USER = 'user'

# Models for validation
class CreateUserRequest(BaseModel):
    user_name:str = Field(min_length=3,max_length=100)
    user_email: str = Field(min_length=3,max_length=100)
    user_password: str = Field(min_length=3,max_length=100)
    role:Optional[str] = Field(default=RoleChoice.USER)
    # user_phone_number:str


class Token(BaseModel):
    access_token: str
    token_type: str


# Db dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


# Function for authenticating user
def authenticate_user(email: str, password: str, db):
    user = db.query(Users).filter(Users.user_email == email).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.user_password):
        return False
    return user


# Function to create access_token
def create_access_token(email: str, id: str, role:str,expires_delta: timedelta,):
    encode = {'sub': email, 'id': id,'role':str(role)}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


# Authenticating the patinet
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        id: str = payload.get('id')
        role:str=payload.get('role')
        if email is None or id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate user.')
        return {'user_email': email, 'user_id': id,'role':role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')
    

# Route to create a user
@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,
                      create_user_request: CreateUserRequest):
    user_id = str(uuid4())
    current_time = datetime.utcnow()
    if db.query(Users).filter(Users.user_email == create_user_request.user_email).first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='User already Exists')
    create_user_model = Users(
        user_name = create_user_request.user_name,
        user_email=create_user_request.user_email,
        user_password=bcrypt_context.hash(
            create_user_request.user_password),
        user_id=user_id,
        user_created_at=current_time,
        role = create_user_request.role.upper()
        # user_phone_number = create_user_request.user_phone_number,
    )

    db.add(create_user_model)
    db.commit()


# Route to create access token for a user
@auth_router.post("/login", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')
    token = create_access_token(
        user.user_email, str(user.user_id),user.role, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}
