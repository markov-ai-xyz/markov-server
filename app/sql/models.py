from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ARRAY
from app.sql.db_config import Base


class User(Base):
    __tablename__ = "users"

    phone = Column(String, primary_key=True)
    name = Column(String)
    location = Column(String)
    email = Column(String)
    skills = Column(ARRAY(String), default=[])
    tenure = Column(String, default=None)


class Authentication(Base):
    __tablename__ = "auth"

    username = Column(String, primary_key=True)
    password = Column(String)


class APIKey(Base):
    __tablename__ = "api_keys"

    user_id = Column(String, primary_key=True)
    hashed_key = Column(String)
