from sqlalchemy import Column, Integer, String, DateTime
from aihub.core.database import Base
from datetime import datetime

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    okta_id = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String) 
    access_date = Column(DateTime, default=datetime.utcnow)
    access_token = Column(String)
    refresh_token = Column(String) 