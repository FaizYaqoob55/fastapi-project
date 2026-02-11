from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_CONNECTION="postgresql://postgres:faiz@localhost:5432/fastapi_db"

engine=create_engine(DB_CONNECTION,echo=True)

Sessionlocal=sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine

)

Base=declarative_base()


