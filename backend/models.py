from sqlalchemy import Column, Integer, String, Date, TIMESTAMP,ForeignKey
from sqlalchemy_utils import UUIDType, ChoiceType
from database import Base
from uuid import uuid4


Status = (
    ('PENDING', 'pending'),
    ('INTERVIEW', 'interview'),
    ('DECLINE', 'decline'),
)
Mode = (
    ('FULLTIME', 'fulltime'),
    ('PARTTIME', 'parttime'),
    ('INTERNSHIP', 'internship'),
)

Role = (
    ('ADMIN','admin'),
    ('USER','user')
)

class Users(Base):
    __tablename__ = 'users'

    user_id = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    user_name = Column(String)
    user_email = Column(String, unique=True)
    user_password = Column(String)
    user_created_at = Column(TIMESTAMP)
    role = Column(ChoiceType(Role),default="USER")
    # user_phone_number = Column(String, unique=True)
    
class Jobs(Base):
    __tablename__ = 'jobs'

    job_id = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    job_position = Column(String)
    job_company = Column(String)
    job_location = Column(String)
    job_created_at = Column(TIMESTAMP)
    job_status = Column(ChoiceType(Status),default="PENDING")
    job_mode = Column(ChoiceType(Mode),default="FULLTIME")
    owner_id = Column(UUIDType(binary=False),ForeignKey("users.user_id"))