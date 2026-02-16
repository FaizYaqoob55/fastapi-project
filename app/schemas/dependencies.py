from pydantic import BaseModel  , EmailStr





class Usercreate(BaseModel):
    name:str
    password:str
    email:EmailStr

class UserResponse(BaseModel):
    id:int
    name:str
    email:EmailStr

    class Config():
        for_attributes=True

class LoginRequest(BaseModel):
    email:EmailStr
    password:str
