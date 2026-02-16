import os 
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


load_dotenv()

SQLALCHEMY_DATABASE_URL=os.getenv('DB_CONNECTION')

engine=create_engine(SQLALCHEMY_DATABASE_URL,echo=True)

Sessionlocal=sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine 

)

Base=declarative_base()


def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()



