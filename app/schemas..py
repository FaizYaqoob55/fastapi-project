from pydantic import BaseModel  , EmailStr



class TeamBase(BaseModel):
    name=str

class CreateTeam(TeamBase):
    pass

class Team(TeamBase):
    id=int
    class Config:
        from_attributes=True



class UserBase(BaseModel):
    name=str
    email=EmailStr

class CreateUser(UserBase):
    team_id=int


class User(UserBase):
    id=int
    class Config():
        from_attributes=True



class ProjectBase(BaseModel):
    name=str

class CreateProject(ProjectBase):
    team_id=str

class Project(BaseModel):
    id=int
    class Config():
        from_attributes=True



