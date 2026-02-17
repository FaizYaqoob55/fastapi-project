from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from app.database import Base
from app.model.role import UserRole
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'userr'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.viewer, nullable=False)
    team = relationship('Team', secondary='team_member', back_populates='members')


class Team(Base):
    __tablename__ = 'team'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    lead_id = Column(Integer, ForeignKey('userr.id'), nullable=False)
    lead = relationship('User', foreign_keys=[lead_id])

    members = relationship('User', secondary='team_member', back_populates='team')


class TeamMemberUpdate:
    user_id: int


class TeamMember(Base):
    __tablename__ = 'team_member'

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey('team.id'))
    user_id = Column(Integer, ForeignKey('userr.id', ondelete='CASCADE'))


class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, index=True)
    name=Column(String,unique=True,index=True)
    description=Column(String)
    status=Column(Enum('active','inactive','completed',name='project_status'),default='active')
    team_id=Column(Integer,ForeignKey('team.id'))
    team=relationship('Team',backref='projects')
    
    