from sqlalchemy import Column,Integer,String,ForeignKey,Enum
from app.database import Base
from app.model.role import UserRole
from sqlalchemy.orm import relationship



class User(Base):
    __tablename__='userr'

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(100),nullable=False)
    email=Column(String(100),unique=True,index=True,nullable=False)
    password=Column(String(100),nullable=False)
    role=Column(Enum(UserRole),default=UserRole.viewer,nullable=False)







class Team(Base):
    __tablename__='team'

    id=(Column(Integer,primary_key=True,index=True))
    name=(Column(String(100),nullable=False))

    users=relationship('Users',back_populates='team')
    project=relationship('Project',back_populates='team')


class Users(Base):
    __tablename__='users'

    id=(Column(Integer,primary_key=True,index=True))
    name=(Column(String(100),nullable=False))
    email=(Column(String(100),unique=True,index=True,nullable=True))

    team_id=Column(Integer,ForeignKey('team.id'))

    team=relationship('Team',back_populates='users')

class Project(Base):
    __tablename__='project'

    id=(Column(Integer,primary_key=True,index=True))
    name=(Column(String(100),nullable=False))
    team_id=Column(Integer,ForeignKey('team.id'))

    team=relationship('Team',back_populates='project')




