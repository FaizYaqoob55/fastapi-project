import os
import bcrypt
from datetime import datetime, timedelta
import jwt
# from .env import SECRET_KEY as SeCRET_KEY
from dotenv import load_dotenv


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


def hash_password(password:str):
    pwd_bytes=password.encode('utf-8')
    salt=bcrypt.gensalt()
    hash_password=bcrypt.hashpw(pwd_bytes,salt)
    return hash_password.decode('utf_8')

def verify_password(plain_password:str , hashed_password:str):
    return bcrypt.checkpw(
        plain_password.encode('utf_8'),
        hashed_password.encode('utf_8')
    )


def create_access_token(data:dict,expires_delta:timedelta |None=None):
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.utcnow()+expires_delta
    else:
        expire=datetime.utcnow()+timedelta(minutes=15)
    to_encode.update({'exp':expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

def refresh_access_token(data:dict,expires_delta:timedelta |None=None):
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.utcnow()+expires_delta
    else:
        expire=datetime.utcnow()+timedelta(days=7)
    to_encode.update({'exp':expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt
