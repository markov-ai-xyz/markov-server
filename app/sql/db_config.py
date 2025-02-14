import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

COCKROACH_DB_URL = os.getenv("COCKROACH_DB_URL")
db_uri = COCKROACH_DB_URL.replace("postgresql://", "cockroachdb://")

engine = create_engine(db_uri)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def create_tables():
    Base.metadata.create_all(engine)
