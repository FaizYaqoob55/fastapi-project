from sqlalchemy import Column, Integer, String, ForeignKey, Enum,Date,Boolean
from app.database import Base
from app.model.role import UserRole
from sqlalchemy.orm import relationship
from app.model.role import SessionStatus,Action_Status


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
    
    


class GrothSession(Base):
    __tablename__ = 'groth_session'

    id = Column(Integer,primary_key=True,index=True)
    title= Column(String,nullable=False)
    date=Column(Date,nullable=False)
    status=Column(Enum(SessionStatus),default=SessionStatus.PLANNED)
    team_id=Column(Integer,ForeignKey('team.id'))
    notes=relationship('SessionNote',back_populates='session',cascade='all,delete')
    action_items=relationship('ActionItem',back_populates='session',cascade='all,delete')


class SessionNote(Base):
    __tablename__='session_note'
    id=Column(Integer,primary_key=True,index=True)
    content=Column(String,nullable=False)
    session_id=Column(Integer,ForeignKey('groth_session.id'))
    session=relationship('GrothSession',back_populates='notes')


class ActionItem(Base):
    __tablename__='action_items'
    id=Column(Integer,primary_key=True,index=True)
    titlr=Column(String,nullable=False)
    completed=Column(Boolean,default=False)
    status=Column(Enum(Action_Status),default=Action_Status.PENDING)
    session_id=Column(Integer,ForeignKey('groth_session.id'))
    session=relationship('GrothSession',back_populates='action_items')



