import bcrypt

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
