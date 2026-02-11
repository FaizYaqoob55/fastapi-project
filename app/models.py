from sqlalchemy import Column,Integer,String,ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship

class Team(Base):
    __tablename__='team'

    id=(Column(Integer,primary_key=True,index=True))
    name=(Column(String(100),nullable=False))

    users=relationship('users',back_populates='Team')
    project=relationship('project',back_populates='Team')


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




